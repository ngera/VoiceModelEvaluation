"""Regression tests for the synthesis content-hash cache.

Cache invariants we lock:
  - Cache key depends on all billable + rendering inputs (provider, model,
    voice_id, text, output_format, sample_rate, version). Any change in
    any of these invalidates.
  - Round-trip preserves audio bytes exactly.
  - Corrupted cache = treated as miss (never crashes the runner).
  - Idempotent puts (overwrites are safe).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veval.runner.cache import SynthesisCache


@pytest.fixture
def cache(tmp_path: Path) -> SynthesisCache:
    return SynthesisCache(cache_dir=tmp_path / "synthesis")


def _put_sample(
    cache: SynthesisCache,
    text: str = "hello world",
    version: str | None = None,
    audio: bytes = b"RIFF\x00\x00\x00\x00WAVEfake",
) -> None:
    cache.put(
        provider="deepgram",
        model="aura-2-thalia-en",
        voice_id="aura-2-thalia-en",
        text=text,
        output_format="wav",
        sample_rate=None,
        version=version,
        audio_bytes=audio,
        chars_billed=len(text),
        billing_unit="characters",
        meta={"request_id": "abc123"},
    )


def _get(
    cache: SynthesisCache, text: str = "hello world", version: str | None = None
) -> object:
    return cache.get(
        provider="deepgram",
        model="aura-2-thalia-en",
        voice_id="aura-2-thalia-en",
        text=text,
        output_format="wav",
        sample_rate=None,
        version=version,
    )


def test_empty_cache_returns_none(cache: SynthesisCache) -> None:
    assert _get(cache) is None


def test_put_then_get_roundtrips_audio_bytes(cache: SynthesisCache) -> None:
    audio = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 200
    _put_sample(cache, audio=audio)
    hit = _get(cache)
    assert hit is not None
    assert hit.audio_bytes == audio


def test_get_preserves_billing_metadata(cache: SynthesisCache) -> None:
    _put_sample(cache)
    hit = _get(cache)
    assert hit.chars_billed == len("hello world")
    assert hit.billing_unit == "characters"
    assert hit.meta["request_id"] == "abc123"


def test_different_text_is_a_miss(cache: SynthesisCache) -> None:
    _put_sample(cache, text="hello world")
    assert _get(cache, text="different text") is None


def test_different_version_is_a_miss(cache: SynthesisCache) -> None:
    """Orpheus SHA bump must invalidate its cache entries."""
    _put_sample(cache, version="sha-A")
    assert _get(cache, version="sha-B") is None


def test_put_is_idempotent(cache: SynthesisCache) -> None:
    _put_sample(cache, audio=b"first")
    _put_sample(cache, audio=b"second")
    hit = _get(cache)
    assert hit.audio_bytes == b"second"
    assert cache.stats()["entries"] == 1


def test_corrupted_metadata_is_treated_as_miss(cache: SynthesisCache) -> None:
    _put_sample(cache)
    # Corrupt the metadata JSON
    meta_files = list(cache.cache_dir.glob("*.json"))
    assert len(meta_files) == 1
    meta_files[0].write_text("{not-valid-json", encoding="utf-8")
    assert _get(cache) is None  # miss, not crash


def test_missing_audio_file_is_treated_as_miss(cache: SynthesisCache) -> None:
    _put_sample(cache)
    audio_files = [p for p in cache.cache_dir.iterdir() if p.suffix != ".json"]
    assert len(audio_files) == 1
    audio_files[0].unlink()
    assert _get(cache) is None


def test_metadata_stores_text_hash_not_text(cache: SynthesisCache) -> None:
    """Belt: text is not stored in cache metadata; the hash is enough for
    integrity checking and keeps large corpus items out of the cache dir."""
    _put_sample(cache, text="a rather long piece of test text " * 50)
    meta_files = list(cache.cache_dir.glob("*.json"))
    payload = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert "text_hash" in payload
    assert "text" not in payload
    assert len(payload["text_hash"]) == 16  # first 16 chars of sha256


def test_stats_reports_entry_count(cache: SynthesisCache) -> None:
    assert cache.stats()["entries"] == 0
    _put_sample(cache, text="one")
    _put_sample(cache, text="two")
    _put_sample(cache, text="three")
    assert cache.stats()["entries"] == 3
