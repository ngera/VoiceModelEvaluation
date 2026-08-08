"""Regression tests for score/{robustness,hi_loader,correlations}.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veval.config import load_gates
from veval.score.correlations import spearman
from veval.score.hi_loader import compare, load_snapshot, HISnapshot
from veval.score.robustness import sweep_all, sweep_gate


# --- robustness --------------------------------------------------------


def _minimal_analyses(clip_count: int = 0, ttfa: float = 250.0) -> dict:
    """Minimal analyses payload for gate application."""
    return {
        "latency.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational", "ttfa_p90_ms": ttfa,
             "long_stratum_rtf_p10": 10.0, "long_stratum_rtf_p50": 12.0},
            {"provider": "faux", "use_case": "narration",
             "long_stratum_rtf_p10": 10.0, "long_stratum_rtf_p50": 12.0},
        ]},
        "wer.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational", "failure_incidence_pct": 0.5},
            {"provider": "faux", "use_case": "narration", "failure_incidence_pct": 0.5},
        ]},
        "hygiene.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational",
             "total_clipped_samples": clip_count, "long_stratum": {"n": 0}},
            {"provider": "faux", "use_case": "narration",
             "total_clipped_samples": 0,
             "long_stratum": {"n": 2, "worst_noise_floor_dbfs": -55.0,
                              "gate_long_stratum_clipped_pass": True}},
        ]},
        "drift.json": {"by_provider": [{"provider": "faux", "gate_pass": True}]},
    }


def test_sweep_gate_is_stable_when_provider_passes_at_all_points() -> None:
    gates = load_gates(Path("configs/gates.yaml"))
    conv = next(u for u in gates.use_cases if u.use_case == "conversational")
    ttfa_gate = next(g for g in conv.gates if g.metric == "ttfa_p90_ms")
    # ttfa 250ms passes at 300/400/500/600 sweep points
    r = sweep_gate(ttfa_gate, "conversational", ["faux"], gates, _minimal_analyses(ttfa=250))
    assert r.is_stable
    for pt in r.robustness_points:
        assert "faux" in r.survivors_per_point[str(pt)]


def test_sweep_gate_reveals_instability_at_tight_threshold() -> None:
    gates = load_gates(Path("configs/gates.yaml"))
    conv = next(u for u in gates.use_cases if u.use_case == "conversational")
    ttfa_gate = next(g for g in conv.gates if g.metric == "ttfa_p90_ms")
    # ttfa 450ms fails at 300 and 400 but passes at 500 and 600
    r = sweep_gate(ttfa_gate, "conversational", ["faux"], gates, _minimal_analyses(ttfa=450))
    assert not r.is_stable  # survivor set changes across the sweep


def test_sweep_all_only_returns_gates_with_robustness_points_defined() -> None:
    gates = load_gates(Path("configs/gates.yaml"))
    results = sweep_all(["faux"], gates, _minimal_analyses())
    # Every returned result has robustness_points
    for r in results:
        assert r.robustness_points


# --- hi_loader ---------------------------------------------------------


def test_hi_snapshot_round_trip(tmp_path: Path) -> None:
    p = tmp_path / "hi.json"
    p.write_text(json.dumps({
        "captured_at": "2026-08-08",
        "source": "https://example.com",
        "scores": {
            "openai": {"rank": 3, "score": 91.5},
            "cartesia": {"rank": 5, "score": 88.2},
        },
    }))
    snap = load_snapshot(p)
    assert snap.captured_at == "2026-08-08"
    assert snap.scores["openai"]["rank"] == 3


def test_compare_reports_reproduces_yes_when_top3_matches() -> None:
    snap = HISnapshot(
        captured_at="x", source="x",
        scores={
            "openai": {"rank": 1, "score": 95},
            "cartesia": {"rank": 2, "score": 92},
            "elevenlabs": {"rank": 3, "score": 89},
            "google": {"rank": 4, "score": 85},
        },
    )
    # Our ranking has the same top-3 in the same order
    our = {"openai": 1.5, "cartesia": 1.0, "elevenlabs": 0.5, "google": 0.0}
    result = compare(snap, our)
    top3 = [p for p in ("openai", "cartesia", "elevenlabs") if p in result]
    assert all(result[p].reproduces == "yes" for p in top3)


def test_compare_reports_reproduces_no_when_top3_differs() -> None:
    snap = HISnapshot(
        captured_at="x", source="x",
        scores={
            "openai": {"rank": 1, "score": 95},
            "cartesia": {"rank": 2, "score": 92},
            "elevenlabs": {"rank": 3, "score": 89},
        },
    )
    our = {"deepgram": 2.0, "fish": 1.5, "google": 1.0, "openai": 0.5}
    result = compare(snap, our)
    # top-3 completely different -> reproduces = "no" for those in the union
    assert result["openai"].reproduces == "no"


def test_compare_excludes_anchor_from_ranking() -> None:
    snap = HISnapshot(
        captured_at="x", source="x",
        scores={"openai": {"rank": 1, "score": 95}},
    )
    our = {"anchor": 5.0, "openai": 1.0}
    result = compare(snap, our)
    # Anchor gets a rank position but should not push openai out of top3
    assert result["openai"].our_rank in (1, 2)


# --- spearman ----------------------------------------------------------


def test_spearman_perfect_positive_agreement() -> None:
    left = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    right = {"a": 10.0, "b": 20.0, "c": 30.0, "d": 40.0}
    r = spearman(left, right, left_axis="D3", right_axis="D4")
    assert r.rho == pytest.approx(1.0)
    assert r.interpretation == "strong"
    assert r.n_shared == 4


def test_spearman_perfect_negative_agreement() -> None:
    left = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    right = {"a": 40.0, "b": 30.0, "c": 20.0, "d": 10.0}
    r = spearman(left, right, left_axis="D3", right_axis="HI")
    assert r.rho == pytest.approx(-1.0)


def test_spearman_returns_none_when_too_few_shared() -> None:
    left = {"a": 1.0, "b": 2.0}  # only 2 shared -> Spearman not defined
    right = {"a": 10.0, "b": 20.0}
    r = spearman(left, right, left_axis="x", right_axis="y")
    assert r.rho is None
    assert r.interpretation.startswith("too few")


def test_spearman_excludes_anchor_by_default() -> None:
    left = {"a": 1.0, "b": 2.0, "c": 3.0, "anchor": 10.0}
    right = {"a": 10.0, "b": 20.0, "c": 30.0, "anchor": 100.0}
    r = spearman(left, right, left_axis="D3", right_axis="D4")
    assert "anchor" not in r.shared_providers
    assert r.n_shared == 3
