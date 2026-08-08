"""Regression tests for latency.py.

Cached rows must not contribute to timing percentiles (they have no real
timing). Fresh rows with ttfa_ms=None (buffered providers, or campaign-
mode runs) go into `total_p*` but not `ttfa_p*`. RTF is computed only
for long-stratum items where audio duration and total_ms are both
present.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

from veval.analyze.latency import _stratum, run


def _pcm_wav(path: Path, duration_s: float = 1.0, sr: int = 24000) -> None:
    """Write a minimal PCM_16 mono WAV — just enough for soundfile.info()."""
    import numpy as np
    import soundfile as sf

    samples = (0.1 * np.sin(2 * np.pi * 440 * np.arange(int(sr * duration_s)) / sr)).astype(
        np.float32
    )
    sf.write(str(path), samples, sr, subtype="PCM_16")


def _make_run(tmp_path: Path, rows: list[dict], kind: str = "campaign") -> Path:
    run_dir = tmp_path / f"{kind}-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": run_dir.name, "kind": kind, "hostname": "test", "platform": "test"})
    )
    for row in rows:
        wav = run_dir / row["audio_path"]
        wav.parent.mkdir(parents=True, exist_ok=True)
        _pcm_wav(wav, duration_s=row.get("_wav_seconds", 1.0))
    (run_dir / "api_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return run_dir


def test_stratum_lookup() -> None:
    assert _stratum("S01") == "short"
    assert _stratum("L07") == "long"
    assert _stratum("X01") is None


def test_run_skips_cached_rows_in_percentiles(tmp_path: Path) -> None:
    rows = [
        {
            "provider": "faux",
            "use_case": "conversational",
            "item_id": "S01",
            "draw": 0,
            "status": "ok",
            "ttfa_ms": None,      # cached rows have no real timing
            "total_ms": 0,
            "cache": "hit",
            "attempts": 0,
            "audio_path": "audio/faux/conversational/S01.wav",
        },
        {
            "provider": "faux",
            "use_case": "conversational",
            "item_id": "M01",
            "draw": 0,
            "status": "ok",
            "ttfa_ms": 250,
            "total_ms": 900,
            "cache": "miss",
            "attempts": 1,
            "audio_path": "audio/faux/conversational/M01.wav",
        },
    ]
    run_dir = _make_run(tmp_path, rows, kind="latency")
    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, writer=writer)

    assert payload["total_items"] == 2
    rollup = payload["by_provider"][0]
    assert rollup["n_cached"] == 1
    assert rollup["n_fresh"] == 1
    assert rollup["ttfa_p50_ms"] == 250
    assert rollup["ttfa_p90_ms"] == 250
    assert rollup["total_p50_ms"] == 900
    assert rollup["ttfa_measured"] is True


def test_campaign_mode_flags_ttfa_unmeasured(tmp_path: Path) -> None:
    rows = [
        {
            "provider": "faux",
            "use_case": "conversational",
            "item_id": "S01",
            "draw": 0,
            "status": "ok",
            "ttfa_ms": None,       # campaign mode never streams
            "total_ms": 1500,
            "cache": "miss",
            "attempts": 1,
            "audio_path": "audio/faux/conversational/S01.wav",
        },
    ]
    run_dir = _make_run(tmp_path, rows, kind="campaign")
    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, writer=writer)

    assert payload["context"]["kind"] == "campaign"
    assert payload["context"]["ttfa_captured_by_mode"] is False
    rollup = payload["by_provider"][0]
    assert rollup["ttfa_measured"] is False
    assert rollup["ttfa_p50_ms"] is None
    assert rollup["total_p50_ms"] == 1500


def test_rtf_computed_only_for_long_stratum(tmp_path: Path) -> None:
    # Short and long items — RTF should only aggregate the long one
    rows = [
        {
            "provider": "faux",
            "use_case": "narration",
            "item_id": "S01",
            "draw": 0,
            "status": "ok",
            "ttfa_ms": 100,
            "total_ms": 200,
            "cache": "miss",
            "attempts": 1,
            "audio_path": "audio/faux/narration/S01.wav",
            "_wav_seconds": 0.5,
        },
        {
            "provider": "faux",
            "use_case": "narration",
            "item_id": "L01",
            "draw": 0,
            "status": "ok",
            "ttfa_ms": 100,
            "total_ms": 10000,
            "cache": "miss",
            "attempts": 1,
            "audio_path": "audio/faux/narration/L01.wav",
            "_wav_seconds": 60.0,
        },
    ]
    # Strip helper key before writing
    rows_on_disk = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    tmp_kind = "latency"
    run_dir = tmp_path / f"{tmp_kind}-20260808T000000Z"
    (run_dir / "audio" / "faux" / "narration").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": run_dir.name, "kind": tmp_kind})
    )
    for r in rows:
        _pcm_wav(run_dir / r["audio_path"], duration_s=r["_wav_seconds"])
    (run_dir / "api_log.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows_on_disk) + "\n"
    )

    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, writer=writer)
    rollup = payload["by_provider"][0]

    # RTF only from the long item: 60s decoded / 10s synth = 6.0
    assert rollup["long_stratum_n"] == 1
    assert rollup["long_stratum_rtf_p50"] == 6.0


def test_error_rows_do_not_break_percentiles(tmp_path: Path) -> None:
    rows = [
        {
            "provider": "faux",
            "use_case": "conversational",
            "item_id": "S01",
            "draw": 0,
            "status": "error",
            "ttfa_ms": None,
            "total_ms": None,
            "cache": "miss",
            "attempts": 3,
            "error": "HTTP 500",
            # Errors have no audio_path — RunReader skips them
        },
        {
            "provider": "faux",
            "use_case": "conversational",
            "item_id": "M01",
            "draw": 0,
            "status": "ok",
            "ttfa_ms": 300,
            "total_ms": 1000,
            "cache": "miss",
            "attempts": 1,
            "audio_path": "audio/faux/conversational/M01.wav",
        },
    ]
    # Only the ok row has a WAV
    wav = tmp_path / "campaign-20260808T000000Z" / "audio/faux/conversational/M01.wav"
    wav.parent.mkdir(parents=True)
    _pcm_wav(wav)

    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "latency"}))
    (run_dir / "api_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, writer=writer)
    # Error row filtered out by RunReader (only_status="ok" default is None
    # here because latency uses only_status=None; but rows without
    # audio_path are still dropped by the RunReader loop).
    rollup = payload["by_provider"][0]
    assert rollup["ttfa_p50_ms"] == 300
