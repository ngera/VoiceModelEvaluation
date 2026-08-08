"""Pareto frontier + CI-domination rule.

Spec Sec 5 (line 532): "Domination is asserted only when the bootstrap
95% CI on the *difference* between two Bradley-Terry scores excludes
zero. Where it includes zero, the pair is reported as 'no difference
detected at this n' - a first-class result category, not a failure."

Two frontier axes per use case:
    - quality x cost: y = BT strength, x = $/1K words at 100K-wpm
    - quality x latency: y = BT strength, x = TTFA p90 (or total_ms
      for buffered providers, annotated as such)

Pareto membership rules:
    - Higher y is better (BT strength is the quality signal).
    - Lower x is better (both cost and latency).
    - A point is on the frontier iff no other survivor STRICTLY
      DOMINATES it, where "strictly dominates" uses the CI test:
      dominator has a lower x AND a BT-difference CI excluding zero
      (positive difference in dominator's favor). Overlapping CIs
      -> no domination claim -> both stay on the frontier.

Non-survivors (gate failures) never appear on the frontier - by
design of the gate/frontier separation. Exempt-and-annotate providers
DO appear, with the na-annotation attached.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from veval.human.bt import BTFit

Axis = Literal["cost", "latency"]


@dataclass
class FrontierPoint:
    provider: str
    y_strength: float
    y_ci_lower: float
    y_ci_upper: float
    x_value: float | None
    x_source: str  # e.g. "100K_words_per_month" or "ttfa_p90_ms"
    on_frontier: bool
    dominated_by: list[str] = field(default_factory=list)
    annotations: list[str] = field(default_factory=list)


@dataclass
class UseCaseFrontier:
    use_case: str
    axis: Axis
    x_source: str
    y_source: str
    points: list[FrontierPoint] = field(default_factory=list)
    # Pairwise domination table (only when the difference CI excludes zero).
    # `dominates`: system that strictly beats; `beaten`: system beaten.
    dominations: list[dict[str, Any]] = field(default_factory=list)


def _pairwise_diff_dominance(bt_fit: BTFit, a: str, b: str) -> str:
    """Look up (a, b) or (b, a) in the fit's pairwise_diff table and
    return the dominator's name, or 'none'.
    """
    for (x, y), d in bt_fit.pairwise_diff.items():
        if {x, y} == {a, b}:
            return str(d.get("dominates", "none"))
    return "none"


def _cost_x_value(cost_payload: dict, provider: str, projection: str) -> float | None:
    for pc in cost_payload.get("providers", []):
        if pc["provider"] == provider:
            return pc.get("dollars_per_1k_words_at", {}).get(projection)
    return None


def _latency_x_value(
    latency_payload: dict, provider: str, use_case: str,
) -> tuple[float | None, str]:
    """Return (x, source_label). Prefers ttfa_p90; falls back to
    total_p90 for buffered providers (Speechify per D-008). The label
    tells the chart to annotate accordingly.
    """
    for row in latency_payload.get("by_provider", []):
        if row["provider"] == provider and row["use_case"] == use_case:
            if row.get("ttfa_p90_ms") is not None:
                return row["ttfa_p90_ms"], "ttfa_p90_ms"
            if row.get("total_p90_ms") is not None:
                return row["total_p90_ms"], "total_p90_ms (buffered, D-008)"
    return None, "unavailable"


def build_frontier(
    bt_fit: BTFit,
    survivors: list[str],
    axis: Axis,
    *,
    cost_payload: dict | None = None,
    latency_payload: dict | None = None,
    cost_projection: str = "100K_words_per_month",
    exempt_providers: dict[str, list[str]] | None = None,
) -> UseCaseFrontier:
    """Compute the Pareto frontier for one use case on one axis.

    `bt_fit` is a per-use-case fit from human/bt.py. `survivors` is the
    provider list from gates.py. `exempt_providers` maps
    provider -> list of exempt gate metrics (for annotations).

    The BT fit may contain the anchor system; the anchor is always
    included in the frontier because it's the reference the study is
    designed to measure ("does the best TTS reach the human anchor?").
    """
    exempt_providers = exempt_providers or {}
    included = set(survivors) | {"anchor"}
    x_source_label = ""

    points: list[FrontierPoint] = []
    for i, system in enumerate(bt_fit.systems):
        if system not in included:
            continue
        y = bt_fit.strengths[i]
        y_lo = bt_fit.strength_ci_lower.get(system, y)
        y_hi = bt_fit.strength_ci_upper.get(system, y)

        if axis == "cost":
            x_source_label = cost_projection
            x = (
                _cost_x_value(cost_payload, system, cost_projection)
                if cost_payload else None
            )
        else:  # latency
            x, x_source_label = (
                _latency_x_value(latency_payload, system, bt_fit.use_case)
                if latency_payload else (None, "unavailable")
            )

        annotations: list[str] = []
        if system == "anchor":
            annotations.append("human anchor (reference)")
        for gate_metric in exempt_providers.get(system, []):
            annotations.append(f"NA: {gate_metric}")
        if axis == "latency" and x_source_label.startswith("total_p90"):
            annotations.append("buffered response (TTFA NA)")

        points.append(FrontierPoint(
            provider=system,
            y_strength=y,
            y_ci_lower=y_lo,
            y_ci_upper=y_hi,
            x_value=x,
            x_source=x_source_label,
            on_frontier=True,  # tentative; refined below
            annotations=annotations,
        ))

    # Domination pass. Point A dominates point B iff:
    #   1. A.x < B.x (strictly better on cost/latency)  AND
    #   2. BT pairwise-difference CI for (A, B) picks A as the winner
    dominations: list[dict[str, Any]] = []
    for a in points:
        for b in points:
            if a is b:
                continue
            if a.x_value is None or b.x_value is None:
                continue
            if a.x_value >= b.x_value:
                continue
            dominator = _pairwise_diff_dominance(bt_fit, a.provider, b.provider)
            if dominator == a.provider:
                b.on_frontier = False
                b.dominated_by.append(a.provider)
                dominations.append({
                    "dominator": a.provider,
                    "beaten": b.provider,
                    "delta_y": a.y_strength - b.y_strength,
                    "delta_x": b.x_value - a.x_value,
                })
    # Points with missing x are shown separately - not on the frontier
    for p in points:
        if p.x_value is None:
            p.on_frontier = False
            p.annotations.append(f"x axis {x_source_label!r} unavailable")

    return UseCaseFrontier(
        use_case=bt_fit.use_case,
        axis=axis,
        x_source=x_source_label,
        y_source="bt_strength",
        points=points,
        dominations=dominations,
    )


def as_dict(frontier: UseCaseFrontier) -> dict[str, Any]:
    return {
        **{k: v for k, v in asdict(frontier).items() if k != "points"},
        "points": [asdict(p) for p in frontier.points],
    }
