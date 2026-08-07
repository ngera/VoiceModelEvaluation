"""Cartesia Sonic-2 adapter.

Docs:      https://docs.cartesia.ai/api-reference/tts/bytes
Auth:      `X-API-Key` header (Cartesia's own scheme, not Bearer).
Endpoint:  POST https://api.cartesia.ai/tts/bytes

Required header: `Cartesia-Version` — Cartesia's API is date-versioned;
every request must pin the API version. If Cartesia rolls the pinned
date forward we will need to update this constant and log a
DEVIATION.

Voice:     UUID passed under `voice.id` (mode `"id"`) — Cartesia clones
           and shipped voices both use the same UUID convention.
Model:     `sonic-2` (Cartesia's latency-optimised model — see
           `voices.yaml` reasoning).

Streaming: `/tts/bytes` streams the audio as chunked WAV. First chunk
           carries the WAV header with a placeholder length (same
           Phase A defect class as Deepgram) — `finalize_wav_header()`
           patches it after the buffer completes.

Billing:   Per character (1 credit ≈ 1 character). `chars_billed` set
           to `len(opts.text)`.

Concurrency: Cartesia caps at 2 (free) / 3 (Pro) simultaneous requests
             — the runner (Phase D) enforces serialised D1 trials and
             capped campaign concurrency. This adapter does not enforce
             concurrency; it trusts the caller.
"""

from __future__ import annotations

import time

import httpx

from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
    finalize_wav_header,
)

DEFAULT_ENDPOINT = "https://api.cartesia.ai/tts/bytes"
DEFAULT_TIMEOUT_S = 60.0
DEFAULT_SAMPLE_RATE = 24000

# Cartesia-Version header pin. This is an ASSUMPTION verified live in
# Phase C; if Cartesia rejects it we bump and log to DEVIATIONS.md.
CARTESIA_VERSION = "2024-11-13"


class CartesiaAdapter(ProviderAdapter):
    name = "cartesia"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        endpoint = self.endpoint or DEFAULT_ENDPOINT
        sample_rate = opts.sample_rate or DEFAULT_SAMPLE_RATE

        # Output-format block: wav container with LINEAR16 PCM samples.
        # Cartesia also accepts "raw" or "mp3"; we standardise on wav for
        # downstream analyzer uniformity.
        if opts.output_format == "wav":
            output_format: dict[str, object] = {
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": sample_rate,
            }
        elif opts.output_format == "mp3":
            output_format = {"container": "mp3", "sample_rate": sample_rate}
        else:
            raise ValueError(f"Unsupported output_format for Cartesia: {opts.output_format}")

        body = {
            "model_id": self.model,          # "sonic-2" per voices.yaml
            "transcript": opts.text,
            "voice": {"mode": "id", "id": opts.voice_id},
            "output_format": output_format,
            "language": "en",
        }

        headers = {
            "X-API-Key": self.api_key,
            "Cartesia-Version": CARTESIA_VERSION,
            "Content-Type": "application/json",
        }

        start = time.perf_counter()
        ttfa_ms: float | None = None
        audio_chunks: list[bytes] = []
        request_id: str | None = None

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
                with client.stream(
                    "POST", endpoint, headers=headers, json=body
                ) as resp:
                    if resp.status_code != 200:
                        body_text = resp.read().decode("utf-8", errors="replace")[:500]
                        raise ProviderError(
                            f"Cartesia HTTP {resp.status_code}: {body_text}",
                            provider=self.name,
                            status_code=resp.status_code,
                            retryable=resp.status_code in (429, 500, 502, 503, 504),
                            raw={
                                "body": body_text,
                                "cartesia_version": CARTESIA_VERSION,
                                "model": self.model,
                            },
                        )
                    for chunk in resp.iter_bytes():
                        if not chunk:
                            continue
                        if ttfa_ms is None and opts.streaming:
                            ttfa_ms = (time.perf_counter() - start) * 1000.0
                        audio_chunks.append(chunk)

                    request_id = (
                        resp.headers.get("x-request-id")
                        or resp.headers.get("request-id")
                    )
        except httpx.HTTPError as e:
            raise ProviderError(
                f"Cartesia network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0
        audio_bytes = b"".join(audio_chunks)
        if opts.output_format == "wav":
            audio_bytes = finalize_wav_header(audio_bytes)

        if not audio_bytes:
            raise ProviderError(
                "Cartesia returned empty audio",
                provider=self.name,
                status_code=200,
                retryable=True,
            )

        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format=opts.output_format,
            sample_rate=sample_rate,
            ttfa_ms=ttfa_ms,
            total_ms=total_ms,
            chars_billed=len(opts.text),
            billing_unit="characters",
            provider=self.name,
            model=self.model,
            voice_id=opts.voice_id,
            meta={
                "request_id": request_id,
                "endpoint": endpoint,
                "cartesia_version": CARTESIA_VERSION,
            },
        )
