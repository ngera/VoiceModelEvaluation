"""Regression tests for the Phase E WAV acceptance gate.

The gate exists to catch the Phase A silent-corruption class before any
analyzer runs. Each test below encodes a specific defect the gate must
either recover from (chunk walker) or flag (placeholder header, tiny
files, decode errors).
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from veval.analyze import acceptance
from veval.analyze.acceptance import _header_duration_seconds, analyze_file, run
from veval.analyze.common import AudioRecord


@pytest.fixture(autouse=True)
def _stub_vad(monkeypatch: pytest.MonkeyPatch) -> None:
    """Silero-VAD rejects synthetic sine waves as non-speech, which is
    correct in the wild but noise here — these tests exercise the header
    walker, LUFS check, and api_log wiring, not the VAD itself. Stub the
    VAD to report "there was speech" so the other checks are what fails
    or passes.
    """

    def fake_get_speech_timestamps(*_args: object, **_kwargs: object) -> list[dict[str, int]]:
        return [{"start": 0, "end": 16000}]

    import silero_vad

    monkeypatch.setattr(silero_vad, "get_speech_timestamps", fake_get_speech_timestamps)
    # Also stop `load_silero_vad()` from downloading the model when it hasn't
    # already been cached by another test in the session.
    monkeypatch.setattr(acceptance, "_VAD_MODEL", object())


def _write_wav(path: Path, seconds: float = 1.0, sr: int = 24000) -> None:
    """Write a plain 16-bit PCM mono WAV via soundfile."""
    samples = (0.1 * np.sin(2 * np.pi * 440 * np.arange(int(sr * seconds)) / sr)).astype(
        np.float32
    )
    sf.write(str(path), samples, sr, subtype="PCM_16")


def _make_run(tmp_path: Path) -> Path:
    """Bare-minimum run dir the RunReader will accept."""
    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": run_dir.name, "kind": "campaign"})
    )
    return run_dir


# --- _header_duration_seconds --------------------------------------------


def test_header_duration_reads_plain_wav(tmp_path: Path) -> None:
    p = tmp_path / "plain.wav"
    _write_wav(p, seconds=2.0, sr=24000)
    dur = _header_duration_seconds(p)
    assert dur is not None
    assert abs(dur - 2.0) < 0.01


def test_header_duration_skips_list_chunk(tmp_path: Path) -> None:
    """Cartesia emits `LIST` metadata BEFORE `data`. Naive reader that
    trusts bytes 40-44 reads the LIST size and computes 0-second duration.
    """
    p = tmp_path / "with_list.wav"
    _write_wav(p, seconds=1.5, sr=24000)
    original = p.read_bytes()

    # Rebuild with a LIST chunk inserted between fmt and data.
    fmt_end = 12 + 8 + 16  # RIFF header + fmt chunk header + fmt body
    fmt_section = original[:fmt_end]
    data_section = original[fmt_end:]
    list_payload = b"INFOICMT" + struct.pack("<I", 12) + b"Cartesia\x00\x00\x00\x00"
    list_chunk = b"LIST" + struct.pack("<I", len(list_payload)) + list_payload
    new_body = fmt_section + list_chunk + data_section
    # Fix RIFF size = total - 8
    new_body = new_body[:4] + struct.pack("<I", len(new_body) - 8) + new_body[8:]
    p.write_bytes(new_body)

    dur = _header_duration_seconds(p)
    assert dur is not None, "chunk walker must skip LIST and find data"
    assert abs(dur - 1.5) < 0.01


def test_header_duration_flags_streaming_placeholder(tmp_path: Path) -> None:
    """OpenAI streamed WAVs ship 0xFFFFFFFF in the data-chunk-size field."""
    p = tmp_path / "streaming.wav"
    _write_wav(p, seconds=1.0, sr=24000)
    raw = bytearray(p.read_bytes())
    raw[40:44] = b"\xff\xff\xff\xff"
    p.write_bytes(raw)
    assert _header_duration_seconds(p) is None


def test_header_duration_rejects_non_wav(tmp_path: Path) -> None:
    p = tmp_path / "not_a_wav.bin"
    p.write_bytes(b"NOT A RIFF FILE AT ALL")
    assert _header_duration_seconds(p) is None


# --- analyze_file (single-record checks) ---------------------------------


def test_analyze_file_passes_clean_wav(tmp_path: Path) -> None:
    p = tmp_path / "clean.wav"
    _write_wav(p, seconds=1.0)
    record = AudioRecord(
        provider="faux",
        use_case="conversational",
        item_id="S01",
        draw=0,
        wav_path=p,
        api_row={"chars_billed": 25},
    )
    r = analyze_file(record)
    assert r.passed, r.issues
    assert r.header_duration_s is not None
    assert r.decoded_duration_s is not None
    assert abs(r.header_duration_s - r.decoded_duration_s) < 0.05
    assert r.chars_billed == 25


def test_analyze_file_flags_missing_wav(tmp_path: Path) -> None:
    record = AudioRecord(
        provider="faux",
        use_case="conversational",
        item_id="S01",
        draw=0,
        wav_path=tmp_path / "nope.wav",
        api_row={"chars_billed": 25},
    )
    r = analyze_file(record)
    assert not r.passed
    assert "wav_missing" in r.issues


def test_analyze_file_flags_json_envelope(tmp_path: Path) -> None:
    """Speechify defect: JSON envelope written to disk instead of audio."""
    p = tmp_path / "envelope.wav"
    p.write_bytes(b'{"audio_data":"UklGRi..."}\n' * 20)
    record = AudioRecord(
        provider="speechify",
        use_case="conversational",
        item_id="S01",
        draw=0,
        wav_path=p,
        api_row={"chars_billed": 25},
    )
    r = analyze_file(record)
    assert not r.passed
    # Either header unreadable OR soundfile decode error is acceptable
    # detection — both flag the file as unusable downstream.
    assert any(
        "header_unreadable" in i or "soundfile_decode_error" in i for i in r.issues
    )


def test_analyze_file_flags_missing_chars_billed(tmp_path: Path) -> None:
    p = tmp_path / "clean.wav"
    _write_wav(p, seconds=1.0)
    record = AudioRecord(
        provider="faux",
        use_case="conversational",
        item_id="S01",
        draw=0,
        wav_path=p,
        api_row={},  # no chars_billed
    )
    r = analyze_file(record)
    assert not r.passed
    assert "chars_billed_missing" in r.issues


def test_analyze_file_flags_missing_api_row(tmp_path: Path) -> None:
    p = tmp_path / "clean.wav"
    _write_wav(p, seconds=1.0)
    record = AudioRecord(
        provider="faux",
        use_case="conversational",
        item_id="S01",
        draw=0,
        wav_path=p,
        api_row=None,
    )
    r = analyze_file(record)
    assert not r.passed
    assert "api_log_row_missing" in r.issues


# --- run (end-to-end over a mock run dir) --------------------------------


def test_run_writes_acceptance_json(tmp_path: Path) -> None:
    run_dir = _make_run(tmp_path)
    wav = run_dir / "audio" / "faux" / "conversational" / "S01.wav"
    _write_wav(wav, seconds=1.0)
    api_row = {
        "provider": "faux",
        "use_case": "conversational",
        "item_id": "S01",
        "draw": 0,
        "status": "ok",
        "chars_billed": 25,
        "audio_path": "audio/faux/conversational/S01.wav",
    }
    (run_dir / "api_log.jsonl").write_text(json.dumps(api_row) + "\n")

    monkey_analysis = tmp_path / "analysis"
    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=monkey_analysis)
    payload = run(run_dir, writer=writer)

    assert payload["gate_ok"] is True
    assert payload["total_files"] == 1
    out = monkey_analysis / run_dir.name / "acceptance.json"
    assert out.exists()
    parsed = json.loads(out.read_text())
    assert parsed["files"][0]["passed"]


def test_run_flags_placeholder_header_wav(tmp_path: Path) -> None:
    """End-to-end: an OpenAI-style 0xFFFFFFFF placeholder WAV fails the gate."""
    run_dir = _make_run(tmp_path)
    wav = run_dir / "audio" / "faux" / "conversational" / "S01.wav"
    _write_wav(wav, seconds=1.0)
    raw = bytearray(wav.read_bytes())
    raw[40:44] = b"\xff\xff\xff\xff"
    wav.write_bytes(raw)

    api_row = {
        "provider": "faux",
        "use_case": "conversational",
        "item_id": "S01",
        "draw": 0,
        "status": "ok",
        "chars_billed": 25,
        "audio_path": "audio/faux/conversational/S01.wav",
    }
    (run_dir / "api_log.jsonl").write_text(json.dumps(api_row) + "\n")

    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, writer=writer)
    assert payload["gate_ok"] is False
    assert payload["failed"] == 1
    issues = payload["files"][0]["issues"]
    assert "header_unreadable" in issues


@pytest.mark.parametrize(
    "path_style", ["audio/faux/conversational/S01.wav", "audio\\faux\\conversational\\S01.wav"]
)
def test_run_normalises_path_separators(tmp_path: Path, path_style: str) -> None:
    """api_log stores audio_path with the platform sep used when writing.
    Analyzer must read either. Windows runs on Linux and vice versa.
    """
    run_dir = _make_run(tmp_path)
    wav = run_dir / "audio" / "faux" / "conversational" / "S01.wav"
    _write_wav(wav, seconds=1.0)
    api_row = {
        "provider": "faux",
        "use_case": "conversational",
        "item_id": "S01",
        "draw": 0,
        "status": "ok",
        "chars_billed": 25,
        "audio_path": path_style,
    }
    (run_dir / "api_log.jsonl").write_text(json.dumps(api_row) + "\n")

    from veval.analyze.common import AnalysisWriter

    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, writer=writer)
    assert payload["total_files"] == 1
    assert payload["files"][0]["passed"]
