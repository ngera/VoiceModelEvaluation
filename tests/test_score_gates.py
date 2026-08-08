"""Regression tests for score/gates.py.

Load-bearing behaviour tested here:
    - Op dispatch (lt/lte/gt/gte/eq)
    - Missing measurement policy (fail vs exempt-and-annotate)
    - "Provider survives use case iff every gate passes or is exempt"
      (a single hard fail = out of the use case, spec Sec 5)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veval.config import load_gates
from veval.score.gates import (
    _apply_op,
    apply_gate,
    apply_gates,
    load_analyses,
    as_dicts,
)


def test_apply_op_all_variants() -> None:
    assert _apply_op(3, "lt", 5)
    assert not _apply_op(5, "lt", 5)
    assert _apply_op(5, "lte", 5)
    assert _apply_op(6, "gt", 5)
    assert _apply_op(5, "gte", 5)
    assert _apply_op(5, "eq", 5)
    assert not _apply_op(6, "eq", 5)


def test_apply_op_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown gate op"):
        _apply_op(1, "bogus", 1)


# --- apply_gate --------------------------------------------------------

def _gates_yaml() -> Path:
    return Path("configs/gates.yaml")


def _find_gate(use_case: str, metric: str):
    gates = load_gates(_gates_yaml())
    uc = next(u for u in gates.use_cases if u.use_case == use_case)
    return next(g for g in uc.gates if g.metric == metric)


def test_apply_gate_pass_on_clean_measurement() -> None:
    gate = _find_gate("conversational", "ttfa_p90_ms")   # lt 400
    latency = {
        "by_provider": [
            {"provider": "faux", "use_case": "conversational", "ttfa_p90_ms": 250},
        ],
    }
    r = apply_gate(gate, "faux", "conversational", {"latency.json": latency})
    assert r.passed is True
    assert r.measured == 250


def test_apply_gate_fail_on_over_threshold() -> None:
    gate = _find_gate("conversational", "ttfa_p90_ms")
    latency = {
        "by_provider": [
            {"provider": "faux", "use_case": "conversational", "ttfa_p90_ms": 800},
        ],
    }
    r = apply_gate(gate, "faux", "conversational", {"latency.json": latency})
    assert r.passed is False


def test_apply_gate_exempt_when_measurement_missing_and_policy_exempt() -> None:
    gate = _find_gate("conversational", "ttfa_p90_ms")  # na_policy = exempt-and-annotate
    # No latency payload at all
    r = apply_gate(gate, "orpheus", "conversational", {})
    assert r.passed is None
    assert "exempt" in r.reason.lower()


def test_apply_gate_fail_when_measurement_missing_and_policy_fail() -> None:
    gate = _find_gate("conversational", "clipped_samples")  # na_policy = fail
    r = apply_gate(gate, "faux", "conversational", {})
    assert r.passed is False


# --- apply_gates (per-provider survival) ------------------------------

def test_provider_survives_when_all_gates_pass() -> None:
    gates = load_gates(_gates_yaml())
    analyses = {
        "latency.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational", "ttfa_p90_ms": 200,
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
             "total_clipped_samples": 0, "long_stratum": {"n": 0}},
            {"provider": "faux", "use_case": "narration",
             "total_clipped_samples": 0,
             "long_stratum": {"n": 2, "worst_noise_floor_dbfs": -55.0,
                              "gate_long_stratum_clipped_pass": True}},
        ]},
        "drift.json": {"by_provider": [{"provider": "faux", "gate_pass": True}]},
    }
    survivals = apply_gates(["faux"], gates, analyses)
    conv = next(s for s in survivals if s.use_case == "conversational")
    narr = next(s for s in survivals if s.use_case == "narration")
    assert conv.survives is True
    assert narr.survives is True


def test_provider_falls_out_on_one_hard_fail() -> None:
    gates = load_gates(_gates_yaml())
    # Clipping > 0 on conversational -> gate fails; provider drops out
    # of conversational but might survive narration if that has clean data.
    analyses = {
        "latency.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational", "ttfa_p90_ms": 200,
             "long_stratum_rtf_p10": 10.0, "long_stratum_rtf_p50": 12.0},
        ]},
        "wer.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational", "failure_incidence_pct": 0.5},
        ]},
        "hygiene.json": {"by_provider": [
            {"provider": "faux", "use_case": "conversational",
             "total_clipped_samples": 15,  # <- clip fail
             "long_stratum": {"n": 0}},
        ]},
    }
    survivals = apply_gates(["faux"], gates, analyses)
    conv = next(s for s in survivals if s.use_case == "conversational")
    assert conv.survives is False
    hard_fails = [o for o in conv.gate_outcomes if o.passed is False]
    assert any(o.gate_metric == "clipped_samples" for o in hard_fails)


def test_exempt_gate_does_not_break_survival() -> None:
    """Structurally-unmeasurable metric with na_policy=exempt-and-annotate
    must NOT fail the provider (spec defect 3.22)."""
    gates = load_gates(_gates_yaml())
    # No latency payload for orpheus (N/A-hosted); wer + hygiene fine.
    analyses = {
        "wer.json": {"by_provider": [
            {"provider": "orpheus", "use_case": "conversational", "failure_incidence_pct": 0.5},
        ]},
        "hygiene.json": {"by_provider": [
            {"provider": "orpheus", "use_case": "conversational",
             "total_clipped_samples": 0, "long_stratum": {"n": 0}},
        ]},
    }
    survivals = apply_gates(["orpheus"], gates, analyses)
    conv = next(s for s in survivals if s.use_case == "conversational")
    assert conv.survives is True  # exempt gates don't kill you
    assert "ttfa_p90_ms" in conv.exempt_gates


# --- load_analyses -----------------------------------------------------

def test_load_analyses_reads_json_files(tmp_path: Path) -> None:
    (tmp_path / "hygiene.json").write_text(json.dumps({"by_provider": []}))
    (tmp_path / "latency.json").write_text(json.dumps({"foo": "bar"}))
    (tmp_path / "notjson.txt").write_text("skipme")
    out = load_analyses(tmp_path)
    assert "hygiene.json" in out
    assert "latency.json" in out
    assert "notjson.txt" not in out


def test_load_analyses_skips_corrupt_json(tmp_path: Path) -> None:
    (tmp_path / "hygiene.json").write_text("{ not valid json")
    out = load_analyses(tmp_path)
    assert "hygiene.json" not in out


# --- as_dicts ----------------------------------------------------------

def test_as_dicts_is_json_serialisable() -> None:
    gates = load_gates(_gates_yaml())
    analyses = {}  # everything exempt or fail
    survivals = apply_gates(["faux"], gates, analyses)
    dumped = as_dicts(survivals)
    # Round-trip through json to confirm no non-serialisable objects
    round_trip = json.loads(json.dumps(dumped))
    assert isinstance(round_trip, list)
    assert "gate_outcomes" in round_trip[0]
