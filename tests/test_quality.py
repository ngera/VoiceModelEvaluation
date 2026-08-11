"""Regression tests for quality.py.

TTSDS2 and Audiobox model calls are mocked — real invocations download
gigabytes of references and benchmark weights. The tests cover:
    - Audiobox axis filtering (only PQ + CE reported per analyzers.yaml)
    - Aggregate rollup shape (means per provider × use case)
    - split_half_delta returns None for too-small file lists
    - run() writes quality.json with the pre-committed axes recorded
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from veval.analyze import quality
from veval.analyze.common import AudioRecord
from veval.analyze.quality import (
    DNSMOS_AXES,
    DNSMOS_ERROR_INPUT_CLIPPED,
    DNSMOS_ERROR_OTHER,
    FileQuality,
    _aggregate_audiobox,
    _aggregate_dnsmos,
    _merge_file_streams,
    analyze_file_audiobox,
    analyze_file_dnsmos,
    run,
    split_half_delta,
)


def test_aggregate_audiobox_means_by_provider_and_use_case() -> None:
    items = [
        FileQuality("faux", "conv", "S01", 0, "p1",
                    audiobox={"production_quality": 4.2, "content_enjoyment": 3.8}),
        FileQuality("faux", "conv", "M01", 0, "p2",
                    audiobox={"production_quality": 4.6, "content_enjoyment": 4.0}),
        FileQuality("faux", "narr", "L01", 0, "p3",
                    audiobox={"production_quality": 4.4}),
    ]
    out = _aggregate_audiobox(items)
    conv = next(r for r in out if r["use_case"] == "conv")
    narr = next(r for r in out if r["use_case"] == "narr")
    assert conv["audiobox_means"]["production_quality"] == pytest.approx(4.4)
    assert conv["audiobox_means"]["content_enjoyment"] == pytest.approx(3.9)
    assert narr["audiobox_means"]["production_quality"] == pytest.approx(4.4)
    assert "content_enjoyment" not in narr["audiobox_means"]


def test_aggregate_audiobox_ignores_error_rows() -> None:
    items = [
        FileQuality("faux", "conv", "S01", 0, "p1",
                    audiobox={"production_quality": 4.2}),
        FileQuality("faux", "conv", "M01", 0, "p2", error="audiobox_error=X"),
    ]
    out = _aggregate_audiobox(items)
    assert out[0]["n_valid"] == 1


def test_split_half_delta_returns_none_for_too_few_files() -> None:
    fake_paths = [Path("/nope") / f"{i}.wav" for i in range(5)]
    assert split_half_delta(fake_paths, "daps", "default") is None


def test_analyze_file_audiobox_filters_to_pre_committed_axes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Audiobox emits 4 axes; the analyzer must report only the ones in
    analyzers.audiobox_axes_reported. Reporting all four unlabelled
    would invite post-hoc selection (spec B.2)."""

    class FakePredictor:
        pass

    # Patch _audiobox_axes_for to return all 4
    from veval.analyze import quality as q
    monkeypatch.setattr(
        q, "_audiobox_axes_for",
        lambda rec, pred: {"CE": 3.8, "CU": 3.2, "PC": 2.5, "PQ": 4.2},
    )

    wav = tmp_path / "S01.wav"
    wav.write_bytes(b"RIFF" + b"\x00" * 40)
    rec = AudioRecord("faux", "conversational", "S01", 0, wav, api_row={})

    r = analyze_file_audiobox(rec, FakePredictor(), ["production_quality", "content_enjoyment"])
    # Only the two we asked for
    assert set(r.audiobox.keys()) == {"production_quality", "content_enjoyment"}
    assert r.audiobox["production_quality"] == 4.2
    assert r.audiobox["content_enjoyment"] == 3.8


def test_analyze_file_audiobox_flags_missing_wav(tmp_path: Path) -> None:
    rec = AudioRecord("faux", "conv", "S01", 0, tmp_path / "nope.wav", api_row={})
    r = analyze_file_audiobox(rec, object(), ["production_quality"])
    assert r.error == "wav_missing"


def test_run_writes_quality_json_with_mocked_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: skip all three heavy stages, verify the JSON scaffold
    is written correctly (axes committed + all three ran_* flags)."""
    from veval.config import load_analyzers
    from veval.analyze.common import AnalysisWriter

    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "campaign"}))
    (run_dir / "api_log.jsonl").write_text("")

    analyzers = load_analyzers(Path("configs/analyzers.yaml"))
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    payload = run(run_dir, analyzers=analyzers,
                  compute_ttsds=False, compute_audiobox=False,
                  compute_dnsmos=False, writer=writer)

    assert payload["ran_ttsds"] is False
    assert payload["ran_audiobox"] is False
    assert payload["ran_dnsmos"] is False
    assert set(payload["audiobox_axes_reported"]) == {"production_quality", "content_enjoyment"}
    assert set(payload["dnsmos_axes_reported"]) == set(DNSMOS_AXES)
    out = tmp_path / "analysis" / run_dir.name / "quality.json"
    assert out.exists()


# --- DNSMOS tests (Phase 2b) ------------------------------------------


def test_dnsmos_axes_constant_lists_all_four() -> None:
    """DNSMOS_AXES enumerates the 4 axes speechmos.dnsmos.run returns.
    Changing this silently would shift which columns appear in the
    frontier + memo tables."""
    assert set(DNSMOS_AXES) == {"p808_mos", "ovrl_mos", "sig_mos", "bak_mos"}


def test_analyze_file_dnsmos_populates_dnsmos_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real speechmos call is monkeypatched; verify field wiring."""
    from veval.analyze import quality as q
    monkeypatch.setattr(q, "_dnsmos_axes_for",
                        lambda rec: {"p808_mos": 3.5, "ovrl_mos": 3.7,
                                     "sig_mos": 3.9, "bak_mos": 4.1})
    wav = tmp_path / "S01.wav"
    wav.write_bytes(b"RIFF" + b"\x00" * 40)
    rec = AudioRecord("faux", "conv", "S01", 0, wav, api_row={})
    r = analyze_file_dnsmos(rec)
    assert r.dnsmos_error is None
    assert set(r.dnsmos.keys()) == set(DNSMOS_AXES)
    assert r.dnsmos["p808_mos"] == 3.5


def test_analyze_file_dnsmos_flags_missing_wav(tmp_path: Path) -> None:
    rec = AudioRecord("faux", "conv", "S01", 0, tmp_path / "nope.wav", api_row={})
    r = analyze_file_dnsmos(rec)
    assert r.error == "wav_missing"
    assert not r.dnsmos


def test_analyze_file_dnsmos_captures_inference_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Inference errors go to dnsmos_error (not top-level error) so a
    file with successful Audiobox + failed DNSMOS still contributes
    to the Audiobox aggregate."""
    from veval.analyze import quality as q

    def boom(rec: Any) -> dict[str, float]:
        raise RuntimeError("onnx failed")

    monkeypatch.setattr(q, "_dnsmos_axes_for", boom)
    wav = tmp_path / "S01.wav"
    wav.write_bytes(b"RIFF" + b"\x00" * 40)
    rec = AudioRecord("faux", "conv", "S01", 0, wav, api_row={})
    r = analyze_file_dnsmos(rec)
    assert r.dnsmos_error is not None
    assert r.dnsmos_error.startswith(f"{DNSMOS_ERROR_OTHER}=")
    assert "RuntimeError" in r.dnsmos_error
    assert r.error is None  # top-level unchanged; Audiobox on same file still counts


def test_analyze_file_dnsmos_classifies_clipping_specifically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clipped audio (peaks > 1) trips speechmos's `must be between -1
    and 1` ValueError. Our wrapper detects that specific case and
    classifies as `input_clipped_out_of_range` so the report can
    group Cartesia's DNSMOS failures by cause rather than parsing
    raw exception strings. Peak amplitude is captured for the
    'how far over' reporting angle."""
    from veval.analyze import quality as q

    def clipped_ValueError(rec: Any) -> dict[str, float]:
        raise ValueError("np.ndarray values must be between -1 and 1.")

    monkeypatch.setattr(q, "_dnsmos_axes_for", clipped_ValueError)
    # Write a real WAV with peak > 1 so _peak_abs_amplitude returns
    # a value the wrapper can attach to the error string.
    import numpy as np
    import soundfile as sf
    wav = tmp_path / "hot.wav"
    samples = np.array([1.2, -1.15, 0.9], dtype=np.float32)
    sf.write(str(wav), samples, 24000, subtype="FLOAT")

    rec = AudioRecord("faux", "conv", "S01", 0, wav, api_row={})
    r = analyze_file_dnsmos(rec)
    assert r.dnsmos_error is not None
    assert r.dnsmos_error.startswith(f"{DNSMOS_ERROR_INPUT_CLIPPED}=")
    assert "peak_abs=1.2" in r.dnsmos_error  # peak amplitude captured
    assert r.error is None


def test_aggregate_dnsmos_means_by_provider_and_use_case() -> None:
    items = [
        FileQuality("faux", "conv", "S01", 0, "p1",
                    dnsmos={"p808_mos": 3.5, "ovrl_mos": 3.6}),
        FileQuality("faux", "conv", "M01", 0, "p2",
                    dnsmos={"p808_mos": 3.7, "ovrl_mos": 3.8}),
    ]
    out = _aggregate_dnsmos(items)
    conv = next(r for r in out if r["use_case"] == "conv")
    assert conv["dnsmos_means"]["p808_mos"] == pytest.approx(3.6)
    assert conv["dnsmos_means"]["ovrl_mos"] == pytest.approx(3.7)
    assert conv["n_valid"] == 2


def test_aggregate_dnsmos_ignores_dnsmos_errored_rows() -> None:
    items = [
        FileQuality("faux", "conv", "S01", 0, "p1",
                    dnsmos={"p808_mos": 3.5}),
        FileQuality("faux", "conv", "M01", 0, "p2",
                    dnsmos_error="RuntimeError: onnx failed"),
    ]
    out = _aggregate_dnsmos(items)
    assert out[0]["n_valid"] == 1


def test_merge_file_streams_combines_by_key() -> None:
    audiobox = [
        FileQuality("faux", "conv", "S01", 0, "p1",
                    audiobox={"production_quality": 4.2}),
    ]
    dnsmos = [
        FileQuality("faux", "conv", "S01", 0, "p1",
                    dnsmos={"p808_mos": 3.5}),
    ]
    merged = _merge_file_streams(audiobox, dnsmos)
    assert len(merged) == 1
    assert merged[0].audiobox["production_quality"] == 4.2
    assert merged[0].dnsmos["p808_mos"] == 3.5


def test_merge_file_streams_falls_back_when_one_stream_empty() -> None:
    only_dnsmos = [FileQuality("faux", "conv", "S01", 0, "p1",
                                dnsmos={"p808_mos": 3.5})]
    assert _merge_file_streams([], only_dnsmos) is only_dnsmos
    only_audiobox = [FileQuality("faux", "conv", "S01", 0, "p1",
                                  audiobox={"production_quality": 4.2})]
    assert _merge_file_streams(only_audiobox, []) is only_audiobox
