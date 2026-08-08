"""Gate application - turn analyzer outputs into a survivor list per use case.

Spec Sec 5: "A provider that fails a gate is out of that use case regardless
of how good it is elsewhere; domination on the Pareto frontier is a claim
about survivors only."

Gates come from gates.yaml (locked in prereg-v1). Metric values come from
`analysis/<run_id>/*.json`. This module maps each gate's `metric` field to
the right analyzer output and applies the op/threshold rule.

na_policy (defect 3.22):
    - "fail": missing measurement counts as gate failure (default was to
      just skip, which quietly excluded structurally-unmeasurable providers)
    - "exempt-and-annotate": provider keeps its seat in the use case with a
      "not assessed - reason" status; the frontier chart annotates it
    - "exclude-from-use-case": drop the provider outright (rarely used)

robustness_points is honored by robustness.py; this module only applies the
canonical threshold.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from veval.config import Gate, GatesFile, NaPolicy, UseCase


# Map gate.metric -> (analyzer_filename, callable extracting the value
# per provider from that analyzer's JSON). Keeps the dispatch table in
# one place so a metric rename lands in exactly one spot.
def _get_ttfa_p90(payload: dict, provider: str, use_case: str) -> float | None:
    for row in payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            return row.get("ttfa_p90_ms")
    return None


def _get_failure_incidence_pct(payload: dict, provider: str, use_case: str) -> float | None:
    for row in payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            return row.get("failure_incidence_pct")
    return None


def _get_clipped_samples(payload: dict, provider: str, use_case: str) -> float | None:
    for row in payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            return float(row.get("total_clipped_samples", 0))
    return None


def _get_long_stratum_clipped(payload: dict, provider: str, use_case: str) -> float | None:
    """Narration `long_stratum_clipped_samples` — reads from hygiene."""
    for row in payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            ls = row.get("long_stratum", {})
            n = ls.get("n", 0)
            if n == 0:
                return None
            return 0.0 if ls.get("gate_long_stratum_clipped_pass") else 1.0
    return None


def _get_long_stratum_noise_floor(payload: dict, provider: str, use_case: str) -> float | None:
    for row in payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            ls = row.get("long_stratum", {})
            return ls.get("worst_noise_floor_dbfs")
    return None


def _get_rtf(payload: dict, provider: str, use_case: str) -> float | None:
    for row in payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            # Use the P10 (worst 10%) of long-stratum RTF - conservative
            return row.get("long_stratum_rtf_p10") or row.get("long_stratum_rtf_p50")
    return None


def _get_monotonic_drift(payload: dict, provider: str, use_case: str) -> float | None:
    """From drift.json - 0.0 = pass, 1.0 = at least one item flagged."""
    if use_case != "narration":
        return 0.0  # gate is narration-only per gates.yaml
    for row in payload.get("by_provider", []):
        if row["provider"] == provider:
            return 0.0 if row.get("gate_pass") else 1.0
    return None


def _get_commercial_use_permitted(_payload: dict, provider: str, _use_case: str) -> float | None:
    """From the D8 capability matrix. Not populated by any analyzer yet -
    load from a separate `capability_matrix.json` if present, else default
    True for providers on paid tiers and unknown for free-only providers.
    """
    # Portfolio-edition default: everyone we're paying is commercial-ok.
    # Real deployment would load capability_matrix.json from configs/.
    return 1.0


# One entry per gate metric that ships in the pre-registered gates.yaml.
# Adding a new gate metric requires a new dispatch row + a new extractor
# above; fails loud in `_extract_value` if the metric isn't recognised.
_METRIC_DISPATCH: dict[str, tuple[str, Any]] = {
    "ttfa_p90_ms": ("latency.json", _get_ttfa_p90),
    "failure_incidence_pct": ("wer.json", _get_failure_incidence_pct),
    "clipped_samples": ("hygiene.json", _get_clipped_samples),
    "long_stratum_clipped_samples": ("hygiene.json", _get_long_stratum_clipped),
    "long_stratum_acoustic_noise_floor_dbfs": ("hygiene.json", _get_long_stratum_noise_floor),
    "rtf": ("latency.json", _get_rtf),
    "monotonic_quality_drift_flag": ("drift.json", _get_monotonic_drift),
    "commercial_use_permitted": (None, _get_commercial_use_permitted),  # type: ignore[dict-item]
}


@dataclass
class GateOutcome:
    provider: str
    use_case: UseCase
    gate_metric: str
    op: str
    threshold: float
    measured: float | None
    passed: bool | None  # None = na_policy-driven exemption
    na_policy: NaPolicy
    reason: str  # short human-readable outcome


@dataclass
class ProviderSurvival:
    provider: str
    use_case: UseCase
    survives: bool
    gate_outcomes: list[GateOutcome] = field(default_factory=list)
    exempt_gates: list[str] = field(default_factory=list)


def _apply_op(measured: float, op: str, threshold: float) -> bool:
    if op == "lt":
        return measured < threshold
    if op == "lte":
        return measured <= threshold
    if op == "gt":
        return measured > threshold
    if op == "gte":
        return measured >= threshold
    if op == "eq":
        return measured == threshold
    raise ValueError(f"Unknown gate op: {op!r}")


def _extract_value(
    gate: Gate,
    provider: str,
    use_case: UseCase,
    analyses: dict[str, dict],
) -> float | None:
    if gate.metric not in _METRIC_DISPATCH:
        raise KeyError(
            f"Gate metric {gate.metric!r} has no dispatch entry. "
            f"Known: {sorted(_METRIC_DISPATCH)}"
        )
    filename, extractor = _METRIC_DISPATCH[gate.metric]
    if filename is None:
        # Capability-matrix metrics: no analyzer payload
        return extractor({}, provider, use_case)
    payload = analyses.get(filename)
    if payload is None:
        return None
    return extractor(payload, provider, use_case)


def apply_gate(
    gate: Gate,
    provider: str,
    use_case: UseCase,
    analyses: dict[str, dict],
) -> GateOutcome:
    measured = _extract_value(gate, provider, use_case, analyses)

    if measured is None:
        # NA - policy decides
        if gate.na_policy == "exempt-and-annotate":
            passed = None
            reason = f"NA (exempt-and-annotate): no measurement for {gate.metric}"
        elif gate.na_policy == "fail":
            passed = False
            reason = f"NA (na_policy=fail): missing {gate.metric}"
        else:  # exclude-from-use-case
            passed = False
            reason = f"NA (na_policy=exclude): missing {gate.metric}"
        return GateOutcome(
            provider=provider, use_case=use_case,
            gate_metric=gate.metric, op=gate.op, threshold=gate.threshold,
            measured=None, passed=passed, na_policy=gate.na_policy, reason=reason,
        )

    ok = _apply_op(measured, gate.op, gate.threshold)
    reason = f"{measured:.3g} {gate.op} {gate.threshold:.3g} -> {'pass' if ok else 'fail'}"
    return GateOutcome(
        provider=provider, use_case=use_case,
        gate_metric=gate.metric, op=gate.op, threshold=gate.threshold,
        measured=measured, passed=ok, na_policy=gate.na_policy, reason=reason,
    )


def apply_gates(
    providers: list[str],
    gates_file: GatesFile,
    analyses: dict[str, dict],
) -> list[ProviderSurvival]:
    """Apply every gate for every (provider, use_case). A provider
    survives a use case iff EVERY gate either passes or is exempt.

    `analyses` is keyed by analyzer JSON filename (e.g. `hygiene.json`).
    """
    survivals: list[ProviderSurvival] = []
    for uc_block in gates_file.use_cases:
        use_case = uc_block.use_case
        for provider in providers:
            outcomes = [apply_gate(g, provider, use_case, analyses) for g in uc_block.gates]
            hard_fails = [o for o in outcomes if o.passed is False]
            exempts = [o for o in outcomes if o.passed is None]
            survives = len(hard_fails) == 0
            survivals.append(ProviderSurvival(
                provider=provider, use_case=use_case,
                survives=survives, gate_outcomes=outcomes,
                exempt_gates=[e.gate_metric for e in exempts],
            ))
    return survivals


def load_analyses(analysis_dir: Path) -> dict[str, dict]:
    """Load every analyzer JSON under `analysis_dir` into a dict keyed by
    filename. Missing files silently skipped - the gate application
    treats missing measurements per each gate's na_policy.
    """
    out: dict[str, dict] = {}
    for path in analysis_dir.glob("*.json"):
        try:
            out[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
    return out


def as_dicts(survivals: list[ProviderSurvival]) -> list[dict]:
    """JSON-safe dump helper for veval score output."""
    return [
        {
            **{k: v for k, v in asdict(s).items() if k != "gate_outcomes"},
            "gate_outcomes": [asdict(o) for o in s.gate_outcomes],
        }
        for s in survivals
    ]
