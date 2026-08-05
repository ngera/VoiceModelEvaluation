"""Shared fixtures and WAV builders.

Deliberately small suite: pure functions and store/config invariants only.
Adapter HTTP is exercised live by `veval doctor`, not mocked here — see
documentation/IMPLEMENTATION_PLAN.md for why that line was drawn.
"""

from __future__ import annotations

import io
import wave

SAMPLE_RATE = 24000

#: What Deepgram actually sends as the data-chunk size when streaming, because
#: it can't know the length at header time. 44,737s declared for a 2.8s clip.
STREAMING_PLACEHOLDER = 0x7FFFAC00


def pcm(seconds: float = 0.1, rate: int = SAMPLE_RATE) -> bytes:
    """Silent 16-bit mono PCM payload of a known duration."""
    return b"\x00\x00" * int(rate * seconds)


def wav_bytes(payload: bytes, *, rate: int = SAMPLE_RATE) -> bytes:
    """A well-formed WAV wrapping `payload`."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(payload)
    return buf.getvalue()


def find_data_chunk(raw: bytes) -> tuple[int, int]:
    """Return (offset_of_data_chunk_header, declared_size)."""
    pos = 12
    while pos + 8 <= len(raw):
        chunk_id = raw[pos : pos + 4]
        declared = int.from_bytes(raw[pos + 4 : pos + 8], "little")
        if chunk_id == b"data":
            return pos, declared
        pos += 8 + declared + (declared % 2)
    raise AssertionError("no data chunk found")


def with_placeholder_size(raw: bytes, declared: int = STREAMING_PLACEHOLDER) -> bytes:
    """Rewrite a good WAV's size fields to a streaming placeholder."""
    buf = bytearray(raw)
    pos, _ = find_data_chunk(raw)
    buf[pos + 4 : pos + 8] = declared.to_bytes(4, "little")
    buf[4:8] = (declared + pos + 4).to_bytes(4, "little")
    return bytes(buf)
