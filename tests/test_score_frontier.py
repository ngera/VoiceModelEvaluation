"""Regression tests for score/frontier.py.

Load-bearing behaviour:
    - Domination requires BOTH lower x AND a CI-excluding-zero win.
    - Overlapping CIs -> NO domination -> both stay on the frontier
      (spec Sec 5 "no difference detected at this n" as a first-class
      result, not a failure).
    - Missing x values keep the provider visible but off the frontier.
    - The anchor is always included even if not a survivor.
"""

from __future__ import annotations

import pytest

from veval.human.bt import BTFit
from veval.score.frontier import as_dict, build_frontier


def _bt_fit(strengths: dict[str, float], pairwise: dict[tuple[str, str], str]) -> BTFit:
    """Small helper: build a BTFit with hand-set strengths + pairwise
    domination lookup. `pairwise` maps (a, b) -> dominator (a, b, or 'none')."""
    systems = list(strengths)
    pd = {}
    for (a, b), dom in pairwise.items():
        # Store both orderings to match how BT emits them internally
        pd[(a, b)] = {"dominates": dom, "point_diff": strengths[a] - strengths[b],
                      "ci_lower": -0.1, "ci_upper": 0.1}
    fit = BTFit(
        use_case="conversational",
        systems=systems,
        strengths=[strengths[s] for s in systems],
        strength_ci_lower={s: strengths[s] - 0.05 for s in systems},
        strength_ci_upper={s: strengths[s] + 0.05 for s in systems},
        pairwise_diff=pd,
        n_judgments=100, n_items=10, n_bootstrap=200,
    )
    return fit


def test_cheaper_and_stronger_dominates_others() -> None:
    fit = _bt_fit(
        {"a": 1.0, "b": 0.5, "c": 0.0},
        {("a", "b"): "a", ("a", "c"): "a", ("b", "c"): "b"},
    )
    cost = {"providers": [
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
        {"provider": "b", "dollars_per_1k_words_at": {"100K_words_per_month": 0.10}},
        {"provider": "c", "dollars_per_1k_words_at": {"100K_words_per_month": 0.20}},
    ]}
    f = build_frontier(fit, survivors=["a", "b", "c"], axis="cost", cost_payload=cost)
    by_prov = {p.provider: p for p in f.points}
    # A is cheapest AND wins on quality -> both b and c dominated
    assert by_prov["a"].on_frontier is True
    assert by_prov["b"].on_frontier is False
    assert by_prov["c"].on_frontier is False
    assert "a" in by_prov["b"].dominated_by
    assert "a" in by_prov["c"].dominated_by


def test_no_domination_when_ci_includes_zero() -> None:
    """Even if cost is lower, `dominates=='none'` on the BT diff means
    the quality claim isn't there -> both stay on the frontier."""
    fit = _bt_fit({"a": 0.1, "b": 0.0}, {("a", "b"): "none"})
    cost = {"providers": [
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
        {"provider": "b", "dollars_per_1k_words_at": {"100K_words_per_month": 0.10}},
    ]}
    f = build_frontier(fit, survivors=["a", "b"], axis="cost", cost_payload=cost)
    by_prov = {p.provider: p for p in f.points}
    assert by_prov["a"].on_frontier is True
    assert by_prov["b"].on_frontier is True
    assert not f.dominations


def test_higher_cost_but_stronger_stays_on_frontier() -> None:
    """A pricier system with a strictly-better CI-excluded win is still
    on the frontier (the axis isn't 1D)."""
    fit = _bt_fit({"a": 1.0, "b": 0.0}, {("a", "b"): "a"})
    cost = {"providers": [
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.20}},
        {"provider": "b", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
    ]}
    f = build_frontier(fit, survivors=["a", "b"], axis="cost", cost_payload=cost)
    by_prov = {p.provider: p for p in f.points}
    # A is pricier so B is NOT dominated by A; both on frontier.
    assert by_prov["a"].on_frontier is True
    assert by_prov["b"].on_frontier is True


def test_missing_x_keeps_point_visible_but_off_frontier() -> None:
    fit = _bt_fit({"a": 1.0, "b": 0.5}, {("a", "b"): "a"})
    cost = {"providers": [
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
        # b has no cost row
    ]}
    f = build_frontier(fit, survivors=["a", "b"], axis="cost", cost_payload=cost)
    b = next(p for p in f.points if p.provider == "b")
    assert b.x_value is None
    assert b.on_frontier is False
    assert any("unavailable" in a for a in b.annotations)


def test_anchor_always_included_even_if_not_in_survivors() -> None:
    fit = _bt_fit({"anchor": 1.5, "a": 0.5}, {("anchor", "a"): "anchor"})
    cost = {"providers": [
        {"provider": "anchor", "dollars_per_1k_words_at": {"100K_words_per_month": 0.0}},
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
    ]}
    # Anchor is NOT in `survivors` (gates don't apply to a human) but must
    # still appear.
    f = build_frontier(fit, survivors=["a"], axis="cost", cost_payload=cost)
    anchor = next(p for p in f.points if p.provider == "anchor")
    assert anchor is not None
    assert any("anchor" in a.lower() for a in anchor.annotations)


def test_latency_axis_falls_back_to_total_ms_for_buffered_providers() -> None:
    fit = _bt_fit({"a": 1.0, "b": 0.5}, {("a", "b"): "a"})
    latency = {"by_provider": [
        {"provider": "a", "use_case": "conversational", "ttfa_p90_ms": 300},
        {"provider": "b", "use_case": "conversational",
         "ttfa_p90_ms": None, "total_p90_ms": 5000},
    ]}
    f = build_frontier(fit, survivors=["a", "b"], axis="latency", latency_payload=latency)
    by_prov = {p.provider: p for p in f.points}
    assert by_prov["a"].x_source == "ttfa_p90_ms"
    assert by_prov["b"].x_source.startswith("total_p90_ms")
    assert any("buffered" in a.lower() for a in by_prov["b"].annotations)


def test_exempt_gates_show_up_as_annotations() -> None:
    fit = _bt_fit({"orpheus": 0.0, "a": 0.5}, {("orpheus", "a"): "a"})
    cost = {"providers": [
        {"provider": "orpheus", "dollars_per_1k_words_at": {"100K_words_per_month": 0.005}},
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
    ]}
    f = build_frontier(
        fit, survivors=["orpheus", "a"], axis="cost",
        cost_payload=cost,
        exempt_providers={"orpheus": ["ttfa_p90_ms"]},
    )
    orpheus = next(p for p in f.points if p.provider == "orpheus")
    assert any("NA: ttfa_p90_ms" in a for a in orpheus.annotations)


def test_as_dict_round_trip() -> None:
    import json
    fit = _bt_fit({"a": 1.0, "b": 0.5}, {("a", "b"): "a"})
    cost = {"providers": [
        {"provider": "a", "dollars_per_1k_words_at": {"100K_words_per_month": 0.05}},
        {"provider": "b", "dollars_per_1k_words_at": {"100K_words_per_month": 0.10}},
    ]}
    f = build_frontier(fit, survivors=["a", "b"], axis="cost", cost_payload=cost)
    round_trip = json.loads(json.dumps(as_dict(f), default=str))
    assert round_trip["axis"] == "cost"
    assert len(round_trip["points"]) == 2
