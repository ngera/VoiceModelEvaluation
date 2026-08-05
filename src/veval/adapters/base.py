"""Common adapter interface. Every provider adapter subclasses `ProviderAdapter`.

Contract from eval_harness_architecture.mermaid:
    synthesize(text, opts) -> {audio_bytes, ttfa_ms, chars_billed, meta}
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SynthesisOptions(BaseModel):
    """What we ask the provider to synthesize."""

    model_config = ConfigDict(extra="forbid")

    text: str
    voice_id: str
    output_format: str = Field(default="wav", description="`wav` or `mp3`")
    sample_rate: int | None = None
    streaming: bool = Field(
        default=False,
        description="If True, adapter must record TTFA (time to first audio byte)",
    )


class SynthesisResult(BaseModel):
    """What the adapter returns after a synthesize() call."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio_bytes: bytes
    audio_format: str
    sample_rate: int | None = None

    # Timing (milliseconds)
    ttfa_ms: float | None = Field(
        default=None,
        description="Time to first audio byte; None if not streaming",
    )
    total_ms: float = Field(description="Wall-clock request-to-last-byte time")

    # Billing
    chars_billed: int = Field(description="Provider-reported billed unit count")
    billing_unit: str = Field(
        default="characters", description="`characters`, `bytes`, `tokens`..."
    )

    # Provenance
    provider: str
    model: str
    voice_id: str

    # Freeform provider-specific metadata (request-id, region, etc.)
    meta: dict[str, Any] = Field(default_factory=dict)


class ProviderError(Exception):
    """Raised by adapters for provider-side failures.

    Adapters should convert HTTP errors, timeouts, and quota problems into
    this so the runner can log them as data rather than crash.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: int | None = None,
        retryable: bool = False,
        raw: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable
        self.raw = raw or {}


def finalize_wav_header(audio: bytes) -> bytes:
    """Rewrite RIFF/data sizes to match the bytes actually received.

    Providers that stream WAV don't know the length when they emit the header,
    so they ship a placeholder (Deepgram sends 0x7FFFAC00 — a declared 44,737s
    for a 2.8s clip). Anything that trusts the header — RTF, silero-VAD,
    pyloudnorm, TTSDS2 — then reads that lie instead of the real duration.

    We buffer the whole response anyway, so the true size is known here.
    No-op for non-WAV bytes or headers that are already correct.
    """
    if len(audio) < 44 or audio[0:4] != b"RIFF" or audio[8:12] != b"WAVE":
        return audio

    buf = bytearray(audio)
    pos = 12
    while pos + 8 <= len(buf):
        chunk_id = bytes(buf[pos : pos + 4])
        declared = int.from_bytes(buf[pos + 4 : pos + 8], "little")
        if chunk_id == b"data":
            actual = len(buf) - (pos + 8)
            if declared != actual:
                buf[pos + 4 : pos + 8] = actual.to_bytes(4, "little")
                buf[4:8] = (len(buf) - 8).to_bytes(4, "little")
            return bytes(buf)
        pos += 8 + declared + (declared % 2)  # chunks are word-aligned
    return bytes(buf)


class ProviderAdapter(ABC):
    """Base class every provider adapter subclasses."""

    #: Short key; must match the `name` field in providers.yaml
    name: str = ""

    def __init__(self, api_key: str, model: str, endpoint: str | None = None) -> None:
        if not api_key:
            raise ValueError(f"{self.name}: api_key is required")
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint

    @abstractmethod
    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        """Synthesize `opts.text` and return audio + timing + billing metadata.

        Adapters MUST:
        - Raise `ProviderError` on any provider-side failure (never bare exceptions)
        - Set `total_ms` to real wall-clock time
        - Set `chars_billed` from provider response if available, else len(text)
        - Populate `meta` with request-id / region / any provider-specific info
        """
        ...
