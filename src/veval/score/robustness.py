"""Robustness sweep - re-apply gates at each threshold in `robustness_points`.

Spec Sec 5 + defect 3.40: the naive "+/- 20% sweep" broke for the 400 ms
conversational latency gate (a +/-20% envelope of 400 ms tops at 480 ms
and never reaches the 500-600 ms perception threshold the rationale
cites). Fix: gates.yaml carries an EXPLICIT `robustness_points` list per
gate.

Output: for each (use_case, robustness_point) tuple, the survivor set
that would result. Downstream: if the frontier composition changes at
adjacent robustness points, the rank is threshold-sensitive and the
report annotates. If the frontier is stable across the sweep, the
finding is robust (spec §5 "gate-robustness sweep").
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from veval.config import Gate, GatesFile
from veval.score.gates import apply_gates


@dataclass
class RobustnessResult:
    use_case: str
    gate_metric: str
    robustness_points: list[float]
    survivors_per_point: dict[str, list[str]] = field(default_factory=dict)
    is_stable: bool = True  # False if survivor set differs across points


def _clone_gates_with_swap(
    original: GatesFile, use_case: str, metric: str, new_threshold: float
) -> GatesFile:
    """Return a new GatesFile with a single (use_case, metric) threshold
    overridden. Everything else identical - immutable sweep."""
    # Pydantic v2 doesn't offer a native deep-copy-with-overrides, so
    # we round-trip through model_dump / model_validate.
    data = original.model_dump()
    for uc in data["use_cases"]:
        if uc["use_case"] != use_case:
            continue
        for g in uc["gates"]:
            if g["metric"] == metric:
                g["threshold"] = new_threshold
    return original.__class__.model_validate(data)


def sweep_gate(
    gate: Gate,
    use_case: str,
    providers: list[str],
    gates_file: GatesFile,
    analyses: dict[str, dict],
) -> RobustnessResult:
    """Re-apply the FULL gate suite at each robustness_point for one gate."""
    result = RobustnessResult(
        use_case=use_case,
        gate_metric=gate.metric,
        robustness_points=list(gate.robustness_points),
    )
    baseline: list[str] | None = None
    for point in gate.robustness_points:
        swapped = _clone_gates_with_swap(gates_file, use_case, gate.metric, point)
        survivals = apply_gates(providers, swapped, analyses)
        survivors = sorted(
            s.provider for s in survivals
            if s.use_case == use_case and s.survives
        )
        result.survivors_per_point[str(point)] = survivors
        if baseline is None:
            baseline = survivors
        elif survivors != baseline:
            result.is_stable = False
    return result


def sweep_all(
    providers: list[str],
    gates_file: GatesFile,
    analyses: dict[str, dict],
) -> list[RobustnessResult]:
    """Sweep every gate that has robustness_points defined."""
    out: list[RobustnessResult] = []
    for uc_block in gates_file.use_cases:
        for gate in uc_block.gates:
            if not gate.robustness_points:
                continue
            out.append(sweep_gate(
                gate, uc_block.use_case, providers, gates_file, analyses,
            ))
    return out


def as_dicts(results: list[RobustnessResult]) -> list[dict[str, Any]]:
    return [asdict(r) for r in results]
