"""Regression tests for wer.py.

ASR judges (Parakeet + faster-whisper) are stubbed — loading them in CI
takes minutes and downloads gigabytes. What we test here:
    - normalise_v1 is stable (its hash pins to analyzers.yaml)
    - span detection (numeric/currency/date)
    - catastrophic-event detectors (truncation, repetition, deletion, hallucination)
    - two-judge agreement + failure incidence + band assignment
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from veval.analyze import wer
from veval.analyze.common import AudioRecord
from veval.analyze.wer import (
    NORMALISER_HASH,
    WerItem,
    analyze_file,
    detect_agreed_deletion_run,
    detect_agreed_insertion_run,
    detect_repetition_loop,
    detect_truncation,
    extract_spans,
    normalise_v1,
    run,
)


# --- normaliser_v1 -------------------------------------------------------


def test_normalise_v1_lowercases_and_strips_punctuation() -> None:
    assert normalise_v1("Hello, World!") == "hello world"
    assert normalise_v1("The quick BROWN fox.") == "the quick brown fox"


def test_normalise_v1_expands_common_contractions() -> None:
    assert normalise_v1("Don't do that") == "do not do that"
    assert normalise_v1("I'll be there") == "i will be there"
    assert normalise_v1("can't stop") == "cannot stop"


def test_normalise_v1_preserves_numbers_but_drops_percent_sign() -> None:
    # Number expansion is intentionally NOT done here (spec §A.2 —
    # forcing a representation would advantage the judge that matches).
    assert normalise_v1("Increased by 0.25%") == "increased by 0 25"


def test_normaliser_hash_is_stable() -> None:
    """If this test fails, normalise_v1 was edited — the hash in
    analyzers.yaml must be updated to match (spec §A.2)."""
    assert len(NORMALISER_HASH) == 64
    # Hash is deterministic; regenerating on the same source gives the same value
    import hashlib
    import inspect
    assert NORMALISER_HASH == hashlib.sha256(
        inspect.getsource(normalise_v1).encode("utf-8")
    ).hexdigest()


# --- span detection ------------------------------------------------------


def test_extract_spans_finds_all_three_types() -> None:
    text = "Balance is $1,299.99 as of March 15, 2025."
    spans = extract_spans(text)
    types = {t for t, _ in spans}
    assert "currency" in types
    assert "date" in types
    assert "numeric" in types


def test_extract_spans_returns_empty_for_plain_text() -> None:
    assert extract_spans("The quick brown fox jumps over the lazy dog") == []


# --- catastrophic-event detectors ---------------------------------------


def test_detect_repetition_loop_flags_the_the_the() -> None:
    assert detect_repetition_loop(["one", "two"] * 20, ngram=2, min_repeats=3)


def test_detect_repetition_loop_ignores_normal_speech() -> None:
    tokens = "the quick brown fox jumps over the lazy dog".split()
    assert not detect_repetition_loop(tokens, ngram=4, min_repeats=3)


def test_detect_truncation_true_when_audio_too_short() -> None:
    # 100 chars → ~8 seconds predicted; 1 second decoded = 0.125 ratio
    assert detect_truncation(decoded_seconds=1.0, reference_chars=100, ratio_threshold=0.60)


def test_detect_truncation_false_when_full_length() -> None:
    assert not detect_truncation(decoded_seconds=8.0, reference_chars=100, ratio_threshold=0.60)


def test_detect_truncation_false_on_missing_inputs() -> None:
    assert not detect_truncation(None, 100)
    assert not detect_truncation(5.0, 0)


def test_detect_agreed_deletion_run_counts_missing_span() -> None:
    ref = ["one", "two", "three", "four", "five"]
    hyp = ["one", "five"]  # three consecutive missing
    assert detect_agreed_deletion_run(ref, hyp, min_run=2) >= 1


def test_detect_agreed_insertion_run_counts_hallucinated_span() -> None:
    ref = ["hello", "world"]
    hyp = ["hello", "there", "beautiful", "amazing", "world"]  # 3 inserted
    assert detect_agreed_insertion_run(ref, hyp, min_run=3) >= 1


# --- analyze_file (end-to-end with mocked ASRs) -------------------------


class _FakePara:
    def __init__(self, transcript: str) -> None:
        self.transcript = transcript

    def __call__(self, path: str) -> dict[str, str]:
        return {"text": self.transcript}


class _FakeWhisper:
    def __init__(self, transcript: str) -> None:
        self.transcript = transcript

    def transcribe(
        self, path: str, language: str, beam_size: int
    ) -> tuple[list[Any], dict[str, Any]]:
        class Seg:
            def __init__(self, t: str) -> None:
                self.text = t

        return [Seg(self.transcript)], {"info": None}


@pytest.fixture
def _gates() -> Any:
    from veval.config import load_gates
    return load_gates(Path("configs/gates.yaml"))


def _record(tmp_path: Path, item_id: str = "S01") -> AudioRecord:
    import numpy as np
    import soundfile as sf

    wav = tmp_path / f"{item_id}.wav"
    samples = (0.1 * np.sin(2 * np.pi * 440 * np.arange(24000) / 24000)).astype("float32")
    sf.write(str(wav), samples, 24000, subtype="PCM_16")
    return AudioRecord("faux", "conversational", item_id, 0, wav, api_row={"chars_billed": 25})


def test_analyze_file_band_A_when_both_judges_agree_with_reference(
    tmp_path: Path, _gates: Any
) -> None:
    rec = _record(tmp_path)
    reference = "the quick brown fox jumps over the lazy dog"
    para = _FakePara(reference)
    whi = _FakeWhisper(reference)

    r = analyze_file(rec, reference_text=reference, judge_1_pipe=para,
                     whisper_model=whi, gates=_gates)
    assert r.error is None
    assert r.agreement_wer == pytest.approx(0.0)
    assert r.band == "A"
    assert not r.failure


def test_analyze_file_band_C_and_failure_when_wildly_wrong(
    tmp_path: Path, _gates: Any
) -> None:
    rec = _record(tmp_path)
    reference = "the quick brown fox jumps over the lazy dog"
    para = _FakePara("cat")
    whi = _FakeWhisper("cat")
    r = analyze_file(rec, reference_text=reference, judge_1_pipe=para,
                     whisper_model=whi, gates=_gates)
    assert r.agreement_wer is not None and r.agreement_wer > 0.5
    assert r.band == "C"
    assert r.failure
    assert any("agreement_wer" in x for x in r.failure_reasons)


def test_analyze_file_span_hard_fail_on_currency_miss(
    tmp_path: Path, _gates: Any
) -> None:
    rec = _record(tmp_path)
    reference = "The invoice total is $1,299.99 due Friday"
    # Both judges agree but drop the currency amount
    para = _FakePara("the invoice total is due friday")
    whi = _FakeWhisper("the invoice total is due friday")
    r = analyze_file(rec, reference_text=reference, judge_1_pipe=para,
                     whisper_model=whi, gates=_gates)
    assert r.failure
    assert "span_agreed_miss" in r.failure_reasons


# --- run() end-to-end ----------------------------------------------------


def _make_corpus(tmp_path: Path) -> Path:
    p = tmp_path / "conversational.yaml"
    import yaml
    p.write_text(yaml.safe_dump({
        "use_case": "conversational",
        "items": [
            {"id": "S01", "stratum": "short", "text": "the quick brown fox",
             "word_count": 4, "tags": []},
        ],
    }))
    return p


def test_run_writes_wer_json_with_stubbed_judges(
    tmp_path: Path, _gates: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Stub the loaders so no models are pulled
    reference = "the quick brown fox"
    monkeypatch.setattr(wer, "_load_judge_1", lambda mid, rev: _FakePara(reference))
    monkeypatch.setattr(wer, "_load_whisper", lambda mid, rev: _FakeWhisper(reference))

    # Minimal run dir
    run_dir = tmp_path / "campaign-20260808T000000Z"
    (run_dir / "audio" / "faux" / "conversational").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_dir.name, "kind": "campaign"}))

    import numpy as np
    import soundfile as sf
    wav = run_dir / "audio" / "faux" / "conversational" / "S01.wav"
    samples = (0.1 * np.sin(2 * np.pi * 440 * np.arange(24000) / 24000)).astype("float32")
    sf.write(str(wav), samples, 24000, subtype="PCM_16")

    api_row = {
        "provider": "faux", "use_case": "conversational", "item_id": "S01",
        "draw": 0, "status": "ok", "chars_billed": 20,
        "audio_path": "audio/faux/conversational/S01.wav",
    }
    (run_dir / "api_log.jsonl").write_text(json.dumps(api_row) + "\n")

    # Corpus + analyzers config
    from veval.config import load_corpus, load_analyzers
    corpus = {"conversational": load_corpus(_make_corpus(tmp_path))}
    analyzers = load_analyzers(Path("configs/analyzers.yaml"))

    from veval.analyze.common import AnalysisWriter
    writer = AnalysisWriter(run_dir.name, base_dir=tmp_path / "analysis")
    payload = run(run_dir, gates=_gates, analyzers=analyzers,
                  corpus_by_use_case=corpus, writer=writer)

    assert payload["normaliser_hash"] == NORMALISER_HASH
    assert len(payload["by_provider"]) == 1
    rollup = payload["by_provider"][0]
    assert rollup["provider"] == "faux"
    assert rollup["agreement_wer_mean"] == pytest.approx(0.0)
    assert rollup["failure_incidence_pct"] == 0.0
    assert rollup["band_counts"]["A"] == 1
    out = tmp_path / "analysis" / run_dir.name / "wer.json"
    assert out.exists()
