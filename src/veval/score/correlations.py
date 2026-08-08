"""Spearman rho correlations across D3 (TTSDS2/Audiobox), D4 (BT), HI.

Spec Sec 4.3 / Sec 5: "Spearman rho published for D3 <-> D4, D3 <-> HI,
D4 <-> HI, each with n and an exact interpretation."

Spearman is rank-order agreement - the right measure here because:
    - D3 (distributional score) is on an unbounded scale.
    - D4 (BT strength) is log-odds centered at 0.
    - HI is a 0-100 index.
Neither Pearson r nor magnitude comparison makes sense across these
scales. Rank agreement does.

Interpretation guide (spec convention):
    |rho| >= 0.9: strong agreement
    0.7 <= |rho| < 0.9: substantial
    0.5 <= |rho| < 0.7: moderate
    0.3 <= |rho| < 0.5: weak
    |rho| < 0.3: essentially uncorrelated
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats


@dataclass
class SpearmanResult:
    left_axis: str
    right_axis: str
    rho: float | None
    p_value: float | None
    n_shared: int
    left_values: dict[str, float]
    right_values: dict[str, float]
    shared_providers: list[str]
    interpretation: str


def _interpret(rho: float) -> str:
    ar = abs(rho)
    if ar >= 0.9:
        return "strong"
    if ar >= 0.7:
        return "substantial"
    if ar >= 0.5:
        return "moderate"
    if ar >= 0.3:
        return "weak"
    return "essentially uncorrelated"


def spearman(
    left: dict[str, float],
    right: dict[str, float],
    *,
    left_axis: str,
    right_axis: str,
    exclude: Iterable[str] = ("anchor",),
) -> SpearmanResult:
    """Rank correlation over providers present in BOTH dicts.

    Anchor is excluded by default: it's a REFERENCE, not a system under
    test, and its rank against providers isn't the correlation of
    interest.

    Returns rho=None when n_shared < 3 (Spearman needs at least 3 pairs
    for a meaningful test).
    """
    exclude_set = set(exclude)
    shared = sorted(set(left) & set(right) - exclude_set)
    if len(shared) < 3:
        return SpearmanResult(
            left_axis=left_axis, right_axis=right_axis,
            rho=None, p_value=None,
            n_shared=len(shared),
            left_values={p: left[p] for p in shared},
            right_values={p: right[p] for p in shared},
            shared_providers=shared,
            interpretation="too few shared providers",
        )
    left_arr = np.array([left[p] for p in shared], dtype=float)
    right_arr = np.array([right[p] for p in shared], dtype=float)
    result = stats.spearmanr(left_arr, right_arr)
    rho = float(result.statistic)
    p = float(result.pvalue)
    return SpearmanResult(
        left_axis=left_axis, right_axis=right_axis,
        rho=rho, p_value=p,
        n_shared=len(shared),
        left_values={p: float(left[p]) for p in shared},
        right_values={p: float(right[p]) for p in shared},
        shared_providers=shared,
        interpretation=_interpret(rho),
    )


def as_dict(r: SpearmanResult) -> dict:
    return asdict(r)
