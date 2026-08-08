"""Bradley-Terry fit + clustered bootstrap CIs.

Spec §4.3 (D4): "Bradley-Terry over the judgments; bootstrap 2,000
resamples over the judgment set clustered BY ITEM (not by judgment) —
judgments on the same item are not independent."

Spec §5 (line 532): "Domination is asserted only when the bootstrap
95% CI on the *difference* between two Bradley-Terry scores excludes
zero. Where it includes zero, the pair is reported as 'no difference
detected at this n' — a first-class result category, not a failure."

Penalty term (analyzers.yaml `bootstrap.penalty_term: 0.5`): keeps
all-win/all-loss resamples finite. `choix.ilsr_pairwise` takes this
as its `alpha` parameter.

Fits are done per (use_case), NOT pooled across use cases — the
comparison "which system wins conversational" is separate from
"which system wins narration", and pooling would blur two different
questions.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

import choix
import numpy as np

# Analyzers.yaml `bootstrap`:
DEFAULT_RESAMPLES = 2000
DEFAULT_ALPHA = 0.5
CI_LEVEL = 0.95


@dataclass(frozen=True)
class RawJudgment:
    """One completed judgment from the rating CSV."""

    use_case: str
    item_id: str
    system_left: str
    system_right: str
    winner: Literal["left", "right"]
    is_consistency_repeat: bool = False


@dataclass
class BTFit:
    use_case: str
    systems: list[str]                    # ordered — index = BT param index
    strengths: list[float]                # log-strength per system (spec: "score")
    strength_ci_lower: dict[str, float] = field(default_factory=dict)
    strength_ci_upper: dict[str, float] = field(default_factory=dict)
    # Pairwise-difference intervals: {(a, b): (lower, upper, dominates)}
    pairwise_diff: dict[tuple[str, str], dict[str, float | bool]] = field(default_factory=dict)
    n_judgments: int = 0
    n_items: int = 0
    n_bootstrap: int = 0
    alpha: float = DEFAULT_ALPHA


def _index_systems(judgments: Iterable[RawJudgment]) -> list[str]:
    return sorted({s for j in judgments for s in (j.system_left, j.system_right)})


def _to_pairwise_wins(
    judgments: Iterable[RawJudgment], systems: list[str]
) -> list[tuple[int, int]]:
    """Convert judgments to choix's (winner_idx, loser_idx) format."""
    idx = {s: i for i, s in enumerate(systems)}
    out: list[tuple[int, int]] = []
    for j in judgments:
        winner_system = j.system_left if j.winner == "left" else j.system_right
        loser_system = j.system_right if j.winner == "left" else j.system_left
        out.append((idx[winner_system], idx[loser_system]))
    return out


def fit_bt(
    judgments: list[RawJudgment],
    systems: list[str] | None = None,
    alpha: float = DEFAULT_ALPHA,
) -> tuple[list[str], np.ndarray]:
    """Single Bradley-Terry fit. Returns (systems, log-strengths).

    Log-strengths are identified only up to a global constant (BT is
    scale-invariant); we center them at mean=0 so cross-use-case
    comparisons are legible.
    """
    if not judgments:
        raise ValueError("Cannot fit BT with zero judgments")
    if systems is None:
        systems = _index_systems(judgments)
    data = _to_pairwise_wins(judgments, systems)
    params = choix.ilsr_pairwise(
        n_items=len(systems), data=data, alpha=alpha, max_iter=500, tol=1e-6
    )
    # Center at mean=0
    return systems, params - np.mean(params)


def _bootstrap_iter(
    judgments: list[RawJudgment],
    systems: list[str],
    n_resamples: int,
    alpha: float,
    seed: int,
) -> np.ndarray:
    """Return an (n_resamples, n_systems) array of fitted strengths.

    Clustered by item: each resample samples ITEMS with replacement,
    then takes ALL judgments for those items. Preserves within-item
    correlation the spec calls out.
    """
    # Group judgments by item
    by_item: dict[str, list[RawJudgment]] = defaultdict(list)
    for j in judgments:
        by_item[j.item_id].append(j)
    items = list(by_item.keys())
    rng = random.Random(seed)
    n_sys = len(systems)

    out = np.full((n_resamples, n_sys), np.nan)
    for b in range(n_resamples):
        picked_items = [rng.choice(items) for _ in range(len(items))]
        resample: list[RawJudgment] = []
        for iid in picked_items:
            resample.extend(by_item[iid])
        if not resample:
            continue
        data = _to_pairwise_wins(resample, systems)
        try:
            params = choix.ilsr_pairwise(
                n_items=n_sys, data=data, alpha=alpha, max_iter=200, tol=1e-5
            )
            out[b] = params - np.mean(params)
        except Exception:  # noqa: BLE001 — degenerate resample = drop
            continue
    return out


def _percentile_ci(values: np.ndarray, ci_level: float = CI_LEVEL) -> tuple[float, float]:
    alpha = (1.0 - ci_level) / 2.0
    return (
        float(np.nanpercentile(values, 100.0 * alpha)),
        float(np.nanpercentile(values, 100.0 * (1.0 - alpha))),
    )


def fit_bt_with_bootstrap(
    judgments: list[RawJudgment],
    n_resamples: int = DEFAULT_RESAMPLES,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
    ci_level: float = CI_LEVEL,
) -> BTFit:
    """Point estimate + clustered-bootstrap CIs for a single use case.

    Callers should partition judgments by use_case BEFORE calling this
    — the returned fit's `use_case` label is inferred from the first
    judgment (spec: one fit per use case, not pooled).
    """
    if not judgments:
        raise ValueError("Cannot fit BT with zero judgments")
    use_cases = {j.use_case for j in judgments}
    if len(use_cases) > 1:
        raise ValueError(
            f"fit_bt_with_bootstrap expects one use case; got {use_cases}. "
            "Split the judgment set by use_case first."
        )
    use_case = next(iter(use_cases))

    systems, point_strengths = fit_bt(judgments, alpha=alpha)
    n_items = len({j.item_id for j in judgments})

    fit = BTFit(
        use_case=use_case,
        systems=list(systems),
        strengths=[float(x) for x in point_strengths],
        n_judgments=len(judgments),
        n_items=n_items,
        n_bootstrap=n_resamples,
        alpha=alpha,
    )

    if n_resamples <= 0:
        return fit

    resamples = _bootstrap_iter(judgments, systems, n_resamples, alpha, seed)

    # Per-system CI (marginal — for the table, not for domination)
    for i, sys_name in enumerate(systems):
        lo, hi = _percentile_ci(resamples[:, i], ci_level)
        fit.strength_ci_lower[sys_name] = lo
        fit.strength_ci_upper[sys_name] = hi

    # Pairwise-difference CI (the load-bearing domination test)
    for i, a in enumerate(systems):
        for j, b in enumerate(systems):
            if i >= j:
                continue
            diffs = resamples[:, i] - resamples[:, j]
            lo, hi = _percentile_ci(diffs, ci_level)
            point_diff = float(point_strengths[i] - point_strengths[j])
            # Domination: CI on the difference excludes zero
            dominates = "none"
            if lo > 0:
                dominates = a  # a strictly greater than b
            elif hi < 0:
                dominates = b  # b strictly greater than a
            fit.pairwise_diff[(a, b)] = {
                "point_diff": point_diff,
                "ci_lower": lo,
                "ci_upper": hi,
                "dominates": dominates,
            }

    return fit


def fit_per_use_case(
    judgments: list[RawJudgment],
    n_resamples: int = DEFAULT_RESAMPLES,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> dict[str, BTFit]:
    """Convenience: split judgments by use case, fit each independently."""
    by_uc: dict[str, list[RawJudgment]] = defaultdict(list)
    for j in judgments:
        by_uc[j.use_case].append(j)
    return {
        uc: fit_bt_with_bootstrap(js, n_resamples=n_resamples, alpha=alpha, seed=seed)
        for uc, js in by_uc.items()
    }


def consistency_rate(
    judgments: list[RawJudgment],
) -> tuple[float, int]:
    """Fraction of consistency-repeat judgments that agree with the
    original ruling on the same (item, system_a, system_b).

    Returns (fraction, n_repeats_checked). Missing pair (repeat without
    a corresponding original) is not counted.
    """
    firsts: dict[tuple[str, str, str, str], str] = {}
    for j in judgments:
        if j.is_consistency_repeat:
            continue
        a, b = sorted([j.system_left, j.system_right])
        key = (j.use_case, j.item_id, a, b)
        winner = j.system_left if j.winner == "left" else j.system_right
        firsts[key] = winner

    agree = 0
    total = 0
    for j in judgments:
        if not j.is_consistency_repeat:
            continue
        a, b = sorted([j.system_left, j.system_right])
        key = (j.use_case, j.item_id, a, b)
        if key not in firsts:
            continue
        winner = j.system_left if j.winner == "left" else j.system_right
        total += 1
        if winner == firsts[key]:
            agree += 1
    if total == 0:
        return 0.0, 0
    return agree / total, total
