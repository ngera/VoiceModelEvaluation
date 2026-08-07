"""Regression tests for `finalize_wav_header`.

The bug these exist for: a streamed WAV declared 44,737 seconds for a 2.80s
clip, and every duration-derived metric (RTF, silero-VAD, pyloudnorm, TTSDS2)
reads duration from that header. It failed silently — `veval doctor` reported
a green check over the corrupt file.

This is shared by every streaming adapter, so these tests cover all of Phase C
in advance, not just Deepgram.
"""

from __future__ import annotations

import io
import wave

from conftest import (
    STREAMING_PLACEHOLDER,
    find_data_chunk,
    pcm,
    wav_bytes,
    with_placeholder_size,
)

from veval.adapters.base import finalize_wav_header, pcm_to_wav


def _duration(raw: bytes) -> float:
    with wave.open(io.BytesIO(raw)) as w:
        return w.getnframes() / w.getframerate()


def test_placeholder_header_is_corrected_to_true_duration() -> None:
    payload = pcm(seconds=2.80)
    streamed = with_placeholder_size(wav_bytes(payload))

    # Precondition: the bug is present before the fix runs.
    assert _duration(streamed) > 40_000

    fixed = finalize_wav_header(streamed)

    assert _duration(fixed) == 2.80
    _, declared = find_data_chunk(fixed)
    assert declared == len(payload)


def test_riff_size_is_corrected_too() -> None:
    """A right data chunk under a wrong RIFF size still trips strict parsers."""
    fixed = finalize_wav_header(with_placeholder_size(wav_bytes(pcm())))
    assert int.from_bytes(fixed[4:8], "little") == len(fixed) - 8


def test_already_correct_header_is_unchanged() -> None:
    good = wav_bytes(pcm())
    assert finalize_wav_header(good) == good


def test_payload_bytes_are_never_altered() -> None:
    """Only size fields may change — audio must survive bit-exact."""
    payload = pcm(seconds=0.5)
    streamed = with_placeholder_size(wav_bytes(payload))
    pos, _ = find_data_chunk(streamed)

    fixed = finalize_wav_header(streamed)

    assert fixed[pos + 8 :] == payload
    assert len(fixed) == len(streamed)


def test_non_wav_bytes_pass_through() -> None:
    """mp3 responses must not be touched."""
    mp3ish = b"\xff\xfb\x90\x44" + b"\x00" * 200
    assert finalize_wav_header(mp3ish) == mp3ish


def test_truncated_input_passes_through() -> None:
    assert finalize_wav_header(b"RIFF") == b"RIFF"
    assert finalize_wav_header(b"") == b""


def test_riff_header_with_wrong_magic_passes_through() -> None:
    not_wave = b"RIFF" + (100).to_bytes(4, "little") + b"AVI " + b"\x00" * 100
    assert finalize_wav_header(not_wave) == not_wave


def test_pcm_to_wav_wraps_raw_samples_with_a_valid_header() -> None:
    """Google Cloud TTS LINEAR16 returns raw PCM; pcm_to_wav wraps it."""
    payload = pcm(seconds=1.0)  # 24000 samples × 2 bytes = 48000 bytes
    wrapped = pcm_to_wav(payload, sample_rate=24000)
    # Header is 44 bytes (RIFF + fmt + data chunk headers)
    assert len(wrapped) == 44 + len(payload)
    # Round-trip via the wave module
    with wave.open(io.BytesIO(wrapped)) as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 24000
        assert w.getnframes() == len(payload) // 2
        assert w.readframes(w.getnframes()) == payload


def test_pcm_to_wav_output_is_readable_by_finalize() -> None:
    """`pcm_to_wav` should produce a header that `finalize_wav_header` treats as
    already-correct (unchanged) — the two helpers must agree."""
    payload = pcm(seconds=0.5)
    wrapped = pcm_to_wav(payload, sample_rate=24000)
    assert finalize_wav_header(wrapped) == wrapped


def test_data_chunk_found_after_an_intervening_chunk() -> None:
    """Some providers emit LIST/fact chunks before data — the walk must skip them."""
    payload = pcm(seconds=0.25)
    fmt = (
        b"fmt " + (16).to_bytes(4, "little")
        + (1).to_bytes(2, "little")      # PCM
        + (1).to_bytes(2, "little")      # mono
        + (24000).to_bytes(4, "little")
        + (48000).to_bytes(4, "little")  # byte rate
        + (2).to_bytes(2, "little")      # block align
        + (16).to_bytes(2, "little")     # bits
    )
    # Odd-length LIST chunk exercises the word-alignment pad byte.
    list_chunk = b"LIST" + (5).to_bytes(4, "little") + b"INFOx" + b"\x00"
    data = b"data" + STREAMING_PLACEHOLDER.to_bytes(4, "little") + payload
    raw = b"RIFF" + (0xFFFFFFF).to_bytes(4, "little") + b"WAVE" + fmt + list_chunk + data

    fixed = finalize_wav_header(raw)

    _, declared = find_data_chunk(fixed)
    assert declared == len(payload)
    assert int.from_bytes(fixed[4:8], "little") == len(fixed) - 8
