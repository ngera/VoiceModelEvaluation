"""Regression tests for variance.py.

The noise-floor formula (1.96 × SD / √n) is what gates.yaml
`measurement_noise_floor` refers to. Getting the arithmetic wrong by
a factor of √n was defect 3.19, which suppressed almost every real
difference in an earlier draft.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from veval.analyze.variance import (
    _extract_wer_by_item_by_draw,
    _noise_floor,
    _within_provider_sd,
    run,
)


def test_within_provider_sd_none_when_no_variance() -> None:
    got, n = _within_provider_sd({"S01": [0.05], "M01": [0.02]})  # only 1 draw
    assert got is None
    assert n == 0


def test_within_provider_sd_two_items_two_draws() -> None:
    # Item S01: [0.05, 0.07] → SD = 0.01414
    # Item M01: [0.02, 0.04] → SD = 0.01414
    # Pooled RMS: sqrt((0.01414^2 + 0.01414^2)/2) = 0.01414
    sd, n = _within_provider_sd({"S01": [0.05, 0.07], "M01": [0.02, 0.04]})
    assert sd == pytest.approx(0.01414, rel=0.01)
    assert n == 2


def test_noise_floor_formula() -> None:
    # z=1.96, SD=0.1, n=10 → 1.96 × 0.1 / √10 ≈ 0.062
    got = _noise_floor(0.1, 10, 1.96)
    assert got == pytest.approx(0.0620, rel=0.01)


def test_noise_floor_none_when_no_data() -> None:
    assert _noise_floor(None, 10, 1.96) is None
    assert _noise_floor(0.1, 0, 1.96) is None


def test_extract_wer_by_item_by_draw_shape() -> None:
    wer_payload = {
        "items": [
            {"provider": "faux", "use_case": "conv", "item_id": "S01", "agreement_wer": 0.05},
            {"provider": "faux", "use_case": "conv", "item_id": "S01", "agreement_wer": 0.06},
            {"provider": "faux", "use_case": "conv", "item_id": "M01", "agreement_wer": 0.02},
            {"provider": "bar", "use_case": "conv", "item_id": "S01", "agreement_wer": 0.10},
        ],
    }
    got = _extract_wer_by_item_by_draw(wer_payload, "faux", "conv")
    assert got == {"S01": [0.05, 0.06], "M01": [0.02]}


def test_run_flags_determinism_from_identical_bytes(tmp_path: Path) -> None:
    """Same audio bytes across draws → deterministic=True."""
    run_dir = tmp_path / "variance-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "variance"}))

    same_bytes = b"RIFF" + b"\x00" * 40 + b"\x11" * 100
    rows = []
    for draw in range(3):
        wav = run_dir / "audio" / "faux" / "conversational" / f"S01_d{draw}.wav"
        wav.write_bytes(same_bytes)
        rows.append({
            "provider": "faux", "use_case": "conversational", "item_id": "S01",
            "draw": draw, "status": "ok", "chars_billed": 20,
            "audio_path": f"audio/faux/conversational/S01_d{draw}.wav",
        })
    (run_dir / "api_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    from veval.analyze.common import AnalysisWriter
    from veval.config import load_gates
    gates = load_gates(Path("configs/gates.yaml"))
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    payload = run(run_dir, gates=gates, writer=writer)
    assert payload["z_multiplier"] == 1.96
    rollup = payload["by_provider"][0]
    # All draws share bytes → deterministic
    assert rollup["deterministic"] is True
    assert rollup["identical_across_draws_fraction"] == 1.0


def test_run_flags_nondeterminism_when_bytes_differ(tmp_path: Path) -> None:
    run_dir = tmp_path / "variance-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "variance"}))

    rows = []
    for draw in range(3):
        wav = run_dir / "audio" / "faux" / "conversational" / f"S01_d{draw}.wav"
        # Different bytes each draw
        wav.write_bytes(b"RIFF" + b"\x00" * 40 + bytes([draw] * 100))
        rows.append({
            "provider": "faux", "use_case": "conversational", "item_id": "S01",
            "draw": draw, "status": "ok", "chars_billed": 20,
            "audio_path": f"audio/faux/conversational/S01_d{draw}.wav",
        })
    (run_dir / "api_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    from veval.analyze.common import AnalysisWriter
    from veval.config import load_gates
    gates = load_gates(Path("configs/gates.yaml"))
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    payload = run(run_dir, gates=gates, writer=writer)
    rollup = payload["by_provider"][0]
    assert rollup["deterministic"] is False
    assert rollup["identical_across_draws_fraction"] == 0.0
