"""Regression tests for hygiene.py.

The gate math (clipping count, noise floor dBFS, long-stratum rollup) is
what we care about. VAD is stubbed so tests exercise the arithmetic
without depending on speech-shaped audio or the Silero download.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from veval.analyze import hygiene
from veval.analyze.common import AudioRecord
from veval.analyze.hygiene import (
    _clipping_stats,
    _pauses,
    _stratum_from_item_id,
    analyze_file,
    run,
)


# --- Silero-VAD stub: pretend the whole clip is speech --------------------


@pytest.fixture
def _stub_vad(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return one speech range covering the whole 16 kHz downsample."""

    def fake_get_speech_timestamps(
        tensor: object, _model: object, *, sampling_rate: int
    ) -> list[dict[str, int]]:
        length = tensor.shape[0]  # type: ignore[attr-defined]
        return [{"start": 0, "end": length}]

    import silero_vad

    monkeypatch.setattr(silero_vad, "get_speech_timestamps", fake_get_speech_timestamps)
    monkeypatch.setattr(hygiene, "_VAD_MODEL", object())


@pytest.fixture
def _stub_vad_split(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two speech regions with a 0.5s gap in the middle (@16 kHz)."""

    def fake(tensor: object, _m: object, *, sampling_rate: int) -> list[dict[str, int]]:
        length = tensor.shape[0]  # type: ignore[attr-defined]
        half = length // 2
        return [
            {"start": 0, "end": half - 4000},
            {"start": half + 4000, "end": length},
        ]

    import silero_vad

    monkeypatch.setattr(silero_vad, "get_speech_timestamps", fake)
    monkeypatch.setattr(hygiene, "_VAD_MODEL", object())


def _write_sine(path: Path, seconds: float, sr: int = 24000, amp: float = 0.2) -> None:
    n = int(sr * seconds)
    samples = (amp * np.sin(2 * np.pi * 440 * np.arange(n) / sr)).astype(np.float32)
    sf.write(str(path), samples, sr, subtype="PCM_16")


# --- unit primitives -----------------------------------------------------


def test_stratum_from_item_id_maps_prefixes() -> None:
    assert _stratum_from_item_id("S01") == "short"
    assert _stratum_from_item_id("L03") == "long"
    assert _stratum_from_item_id("E07") == "edge"
    assert _stratum_from_item_id("J01") == "jargon"
    assert _stratum_from_item_id("M12") == "medium"
    assert _stratum_from_item_id("P02") == "probe"


def test_stratum_from_item_id_unknown_returns_none() -> None:
    assert _stratum_from_item_id("X01") is None
    assert _stratum_from_item_id("") is None


def test_clipping_stats_zero_when_clean() -> None:
    samples = 0.5 * np.sin(np.linspace(0, 10, 4000)).astype(np.float32)
    n, runs = _clipping_stats(samples)
    assert n == 0
    assert runs == 0


def test_clipping_stats_counts_saturation_plateau() -> None:
    # Two saturated plateaus of length 10 each, separated by clean audio
    samples = np.zeros(1000, dtype=np.float32)
    samples[100:110] = 1.0
    samples[500:510] = -1.0
    n, runs = _clipping_stats(samples)
    assert n == 20
    assert runs == 2


def test_pauses_returns_none_for_single_speech_run() -> None:
    pauses, long_pauses, max_pause = _pauses([(0, 24000)], sr=24000)
    assert pauses == 0
    assert long_pauses == 0
    assert max_pause is None


def test_pauses_flags_long_gap() -> None:
    # Two runs with a 3-second gap between them at 24 kHz
    pauses, long_pauses, max_pause = _pauses(
        [(0, 24000), (24000 + 3 * 24000, 24000 + 3 * 24000 + 24000)],
        sr=24000,
        long_threshold_s=2.0,
    )
    assert pauses == 1
    assert long_pauses == 1
    assert max_pause == pytest.approx(3.0, rel=0.01)


def test_pauses_ignores_short_gap() -> None:
    pauses, long_pauses, max_pause = _pauses(
        [(0, 24000), (24000 + int(0.3 * 24000), 24000 + int(0.3 * 24000) + 24000)],
        sr=24000,
    )
    assert pauses == 1
    assert long_pauses == 0
    assert max_pause == pytest.approx(0.3, rel=0.05)


# --- analyze_file (per-file end-to-end) ---------------------------------


def test_analyze_file_clean_wav_reports_no_clipping(
    tmp_path: Path, _stub_vad: None
) -> None:
    p = tmp_path / "clean.wav"
    _write_sine(p, seconds=1.0, amp=0.2)
    record = AudioRecord("faux", "conversational", "S01", 0, p, api_row={"chars_billed": 25})
    r = analyze_file(record)
    assert r.error is None
    assert r.clipped_samples == 0
    assert r.stratum == "short"
    assert r.lufs is not None
    # With full-speech stub, non-speech region is empty → noise floor is None
    assert r.acoustic_noise_floor_dbfs is None
    assert r.total_seconds == pytest.approx(1.0, rel=0.01)


def test_analyze_file_detects_clipping(
    tmp_path: Path, _stub_vad: None
) -> None:
    p = tmp_path / "clipped.wav"
    # Hot signal, deliberately clipped
    sr = 24000
    samples = (1.5 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)).astype(np.float32)
    samples = np.clip(samples, -1.0, 1.0)
    sf.write(str(p), samples, sr, subtype="PCM_16")

    record = AudioRecord("faux", "conversational", "S01", 0, p, api_row={"chars_billed": 25})
    r = analyze_file(record)
    assert r.error is None
    assert r.clipped_samples > 0
    assert r.clipped_runs > 0


def test_analyze_file_noise_floor_from_non_speech_region(
    tmp_path: Path, _stub_vad_split: None
) -> None:
    p = tmp_path / "with_gap.wav"
    _write_sine(p, seconds=1.0, sr=24000, amp=0.2)
    record = AudioRecord("faux", "narration", "L01", 0, p, api_row={"chars_billed": 25})
    r = analyze_file(record)
    assert r.error is None
    assert r.stratum == "long"
    # With a middle gap, non-speech region has samples → noise floor measurable
    assert r.acoustic_noise_floor_dbfs is not None
    assert r.pause_count == 1


def test_analyze_file_missing_wav_sets_error(tmp_path: Path, _stub_vad: None) -> None:
    record = AudioRecord(
        "faux", "conversational", "S01", 0, tmp_path / "nope.wav", api_row={"chars_billed": 25}
    )
    r = analyze_file(record)
    assert r.error == "wav_missing"


# --- run() end-to-end -----------------------------------------------------


def _make_run(tmp_path: Path, item_ids: list[str]) -> Path:
    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": run_dir.name, "kind": "campaign"})
    )
    rows = []
    for iid in item_ids:
        wav = run_dir / "audio" / "faux" / "conversational" / f"{iid}.wav"
        _write_sine(wav, seconds=0.5)
        rows.append(
            {
                "provider": "faux",
                "use_case": "conversational",
                "item_id": iid,
                "draw": 0,
                "status": "ok",
                "chars_billed": 25,
                "audio_path": f"audio/faux/conversational/{iid}.wav",
            }
        )
    (run_dir / "api_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return run_dir


def test_run_writes_hygiene_json_with_gate_pass(
    tmp_path: Path, _stub_vad: None
) -> None:
    from veval.analyze.common import AnalysisWriter
    from veval.config import load_gates

    run_dir = _make_run(tmp_path, ["S01", "L01"])
    gates = load_gates(Path("configs/gates.yaml"))
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, gates=gates, writer=writer)

    assert payload["total_files"] == 2
    assert payload["n_errors"] == 0
    assert len(payload["by_provider"]) == 1
    rollup = payload["by_provider"][0]
    assert rollup["provider"] == "faux"
    assert rollup["gate_clipped_samples_pass"] is True
    # Long stratum present → the long-stratum gate is either bool or None
    # (None means "not measurable — no non-speech region"); either is fine
    assert rollup["long_stratum"]["n"] == 1

    out = tmp_path / "analysis" / run_dir.name / "hygiene.json"
    assert out.exists()
    parsed = json.loads(out.read_text())
    assert parsed["gate_thresholds"]["acoustic_noise_floor_dbfs_max"] == -40.0
    assert parsed["gate_thresholds"]["max_clipped_samples"] == 0
