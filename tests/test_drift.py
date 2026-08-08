"""Regression tests for drift.py.

Drift analysis operates on long-stratum narration audio only. The
monotonic-degradation flag reads from the coarse first-pass rule
(LUFS decrease across thirds > 3 dB, or RMS dBFS increase > 6 dB).
Tests exercise both paths + the "only narration L-items" filter.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from veval.analyze.common import AudioRecord
from veval.analyze.drift import analyze_file, run


def _write_wav(path: Path, samples: np.ndarray, sr: int = 24000) -> None:
    sf.write(str(path), samples.astype(np.float32), sr, subtype="PCM_16")


def test_analyze_file_thirds_shape(tmp_path: Path) -> None:
    p = tmp_path / "L01.wav"
    # 3 seconds of a stable sine
    sr = 24000
    samples = 0.2 * np.sin(2 * np.pi * 440 * np.arange(3 * sr) / sr)
    _write_wav(p, samples, sr)
    rec = AudioRecord("faux", "narration", "L01", 0, p, api_row={})
    r = analyze_file(rec)
    assert r.error is None
    assert len(r.thirds) == 3
    assert r.monotonic_degradation is False


def test_analyze_file_flags_lufs_decrease(tmp_path: Path) -> None:
    """Amplitude fading across the clip → LUFS drops monotonically."""
    p = tmp_path / "L01.wav"
    sr = 24000
    n = 6 * sr
    envelope = np.linspace(1.0, 0.01, n)  # linear fade from full to near-silence
    samples = 0.5 * envelope * np.sin(2 * np.pi * 440 * np.arange(n) / sr)
    _write_wav(p, samples, sr)
    rec = AudioRecord("faux", "narration", "L01", 0, p, api_row={})
    r = analyze_file(rec)
    assert r.error is None
    assert r.monotonic_degradation is True


def test_analyze_file_missing_wav_error(tmp_path: Path) -> None:
    rec = AudioRecord("faux", "narration", "L01", 0, tmp_path / "nope.wav", api_row={})
    r = analyze_file(rec)
    assert r.error == "wav_missing"


def test_run_filters_to_narration_L_items_only(tmp_path: Path) -> None:
    run_dir = tmp_path / "campaign-20260808T000000Z"
    for iid, use_case in [("L01", "narration"), ("L01", "conversational"), ("S01", "narration")]:
        wav_dir = run_dir / "audio" / "faux" / use_case
        wav_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(wav_dir / f"{iid}.wav", 0.2 * np.sin(2 * np.pi * 440 * np.arange(24000) / 24000))
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "campaign"}))
    rows = [
        {"provider": "faux", "use_case": "narration", "item_id": "L01", "draw": 0,
         "status": "ok", "chars_billed": 200, "audio_path": "audio/faux/narration/L01.wav"},
        {"provider": "faux", "use_case": "conversational", "item_id": "L01", "draw": 0,
         "status": "ok", "chars_billed": 200, "audio_path": "audio/faux/conversational/L01.wav"},
        {"provider": "faux", "use_case": "narration", "item_id": "S01", "draw": 0,
         "status": "ok", "chars_billed": 20, "audio_path": "audio/faux/narration/S01.wav"},
    ]
    (run_dir / "api_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    from veval.analyze.common import AnalysisWriter
    from veval.config import load_gates
    gates = load_gates(Path("configs/gates.yaml"))
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    payload = run(run_dir, gates=gates, writer=writer)
    # Only narration/L01 should have been analyzed
    assert len(payload["items"]) == 1
    assert payload["items"][0]["use_case"] == "narration"
    assert payload["items"][0]["item_id"] == "L01"
    rollup = payload["by_provider"][0]
    assert rollup["n_long_items"] == 1
    assert rollup["gate_pass"] is True
