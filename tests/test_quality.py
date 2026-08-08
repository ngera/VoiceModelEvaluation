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
    FileQuality,
    _aggregate_audiobox,
    analyze_file_audiobox,
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
    """End-to-end: skip both heavy stages, verify the JSON scaffold is
    written correctly (axes committed, ran_ttsds/ran_audiobox flags)."""
    from veval.config import load_analyzers
    from veval.analyze.common import AnalysisWriter

    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "campaign"}))
    (run_dir / "api_log.jsonl").write_text("")

    analyzers = load_analyzers(Path("configs/analyzers.yaml"))
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")

    payload = run(run_dir, analyzers=analyzers,
                  compute_ttsds=False, compute_audiobox=False, writer=writer)

    assert payload["ran_ttsds"] is False
    assert payload["ran_audiobox"] is False
    assert set(payload["audiobox_axes_reported"]) == {"production_quality", "content_enjoyment"}
    out = tmp_path / "analysis" / run_dir.name / "quality.json"
    assert out.exists()
