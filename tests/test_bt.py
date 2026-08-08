"""Regression tests for human/bt.py.

Two load-bearing behaviors:
    1. Recover a known ranking on synthetic data (BT + bootstrap CIs
       cover the true strengths).
    2. Domination test on the pairwise-DIFFERENCE CI (spec §5 line
       532): when two strengths are indistinguishable, `dominates`
       must be "none"; when the true gap is huge, it must name the
       correct winner.
"""

from __future__ import annotations

import math
import random

import pytest

from veval.human.bt import (
    CI_LEVEL,
    DEFAULT_ALPHA,
    DEFAULT_RESAMPLES,
    RawJudgment,
    consistency_rate,
    fit_bt,
    fit_bt_with_bootstrap,
    fit_per_use_case,
)


def _synth_judgments(
    strengths: dict[str, float],
    n_items: int = 20,
    reps: int = 3,
    seed: int = 0,
    use_case: str = "conversational",
) -> list[RawJudgment]:
    """Simulate BT-generated judgments with given true strengths."""
    rng = random.Random(seed)
    systems = list(strengths)
    js: list[RawJudgment] = []
    for i in range(n_items):
        item_id = f"S{i:02d}"
        for a in systems:
            for b in systems:
                if a >= b:
                    continue
                for _ in range(reps):
                    ea = math.exp(strengths[a])
                    eb = math.exp(strengths[b])
                    p_left_wins = ea / (ea + eb)
                    winner = "left" if rng.random() < p_left_wins else "right"
                    js.append(RawJudgment(
                        use_case=use_case, item_id=item_id,
                        system_left=a, system_right=b, winner=winner,
                    ))
    return js


# --- fit_bt (point estimate) --------------------------------------------


def test_fit_bt_recovers_ordering() -> None:
    js = _synth_judgments({"a": 2.0, "b": 0.5, "c": -1.0, "d": -1.5})
    systems, strengths = fit_bt(js)
    order = [s for _, s in sorted(zip(strengths, systems), reverse=True)]
    assert order == ["a", "b", "c", "d"]


def test_fit_bt_strengths_centered_at_zero() -> None:
    js = _synth_judgments({"a": 2.0, "b": 0.0, "c": -2.0})
    _, strengths = fit_bt(js)
    assert abs(float(sum(strengths))) < 1e-6


def test_fit_bt_rejects_empty_judgments() -> None:
    with pytest.raises(ValueError, match="zero judgments"):
        fit_bt([])


# --- fit_bt_with_bootstrap ---------------------------------------------


def test_bootstrap_ci_covers_true_strengths_on_easy_case() -> None:
    """Wide gaps + plenty of data → CIs are tight and include the truth."""
    truth = {"a": 2.0, "b": 0.5, "c": -1.0, "d": -1.5}
    js = _synth_judgments(truth, n_items=20, reps=3)
    fit = fit_bt_with_bootstrap(js, n_resamples=500, seed=0)
    truth_centered = {k: v - sum(truth.values()) / len(truth) for k, v in truth.items()}
    for sys_name, true_val in truth_centered.items():
        lo = fit.strength_ci_lower[sys_name]
        hi = fit.strength_ci_upper[sys_name]
        assert lo <= true_val <= hi, (
            f"{sys_name}: true {true_val:.2f} outside [{lo:.2f}, {hi:.2f}]"
        )


def test_bootstrap_flags_domination_when_gap_is_wide() -> None:
    """Big true gap → pairwise-difference CI excludes zero → `dominates`
    names the winner."""
    js = _synth_judgments({"a": 2.0, "b": -2.0}, n_items=20, reps=3)
    fit = fit_bt_with_bootstrap(js, n_resamples=500, seed=0)
    diff = fit.pairwise_diff[("a", "b")]
    assert diff["dominates"] == "a"
    assert diff["ci_lower"] > 0


def test_bootstrap_flags_no_domination_when_systems_equal() -> None:
    """Equal true strengths → pairwise CI includes zero → `dominates`
    must be 'none' (spec 'no difference detected at this n')."""
    js = _synth_judgments({"a": 0.0, "b": 0.0}, n_items=20, reps=3, seed=42)
    fit = fit_bt_with_bootstrap(js, n_resamples=500, seed=0)
    diff = fit.pairwise_diff[("a", "b")]
    assert diff["dominates"] == "none"
    assert diff["ci_lower"] <= 0 <= diff["ci_upper"]


def test_bootstrap_defaults_match_analyzers_yaml() -> None:
    """These are the load-bearing constants from analyzers.yaml
    `bootstrap:` — changing silently would produce results with a
    different CI construction than the pre-registered one."""
    assert DEFAULT_RESAMPLES == 2000
    assert DEFAULT_ALPHA == 0.5
    assert CI_LEVEL == 0.95


def test_fit_rejects_multi_use_case_input() -> None:
    """Fits are per use case; pooling would blur two questions."""
    js = _synth_judgments({"a": 1.0, "b": -1.0}, use_case="conversational") + \
         _synth_judgments({"a": 1.0, "b": -1.0}, use_case="narration")
    with pytest.raises(ValueError, match="one use case"):
        fit_bt_with_bootstrap(js, n_resamples=100)


def test_fit_per_use_case_splits_and_fits_independently() -> None:
    js = _synth_judgments({"a": 2.0, "b": -2.0}, use_case="conversational") + \
         _synth_judgments({"a": -2.0, "b": 2.0}, use_case="narration")
    fits = fit_per_use_case(js, n_resamples=200)
    assert set(fits.keys()) == {"conversational", "narration"}
    # In conversational, a wins; in narration, b wins
    assert fits["conversational"].pairwise_diff[("a", "b")]["dominates"] == "a"
    assert fits["narration"].pairwise_diff[("a", "b")]["dominates"] == "b"


# --- consistency_rate ---------------------------------------------------


def test_consistency_rate_100_pct_when_repeats_agree() -> None:
    orig = RawJudgment("conv", "S01", "a", "b", "left")
    repeat = RawJudgment("conv", "S01", "a", "b", "left", is_consistency_repeat=True)
    frac, n = consistency_rate([orig, repeat])
    assert frac == 1.0
    assert n == 1


def test_consistency_rate_handles_flipped_left_right() -> None:
    """Consistency should be about which SYSTEM won, not which SIDE."""
    orig = RawJudgment("conv", "S01", "a", "b", "left")     # a wins
    # Repeat with sides swapped, still picking a → consistent
    repeat = RawJudgment("conv", "S01", "b", "a", "right", is_consistency_repeat=True)
    frac, n = consistency_rate([orig, repeat])
    assert frac == 1.0
    assert n == 1


def test_consistency_rate_50_pct_on_split() -> None:
    js = [
        RawJudgment("conv", "S01", "a", "b", "left"),
        RawJudgment("conv", "S01", "a", "b", "right", is_consistency_repeat=True),
        RawJudgment("conv", "S02", "a", "b", "left"),
        RawJudgment("conv", "S02", "a", "b", "left", is_consistency_repeat=True),
    ]
    frac, n = consistency_rate(js)
    assert n == 2
    assert frac == 0.5


def test_consistency_rate_zero_when_no_repeats() -> None:
    frac, n = consistency_rate([RawJudgment("conv", "S01", "a", "b", "left")])
    assert n == 0
    assert frac == 0.0
