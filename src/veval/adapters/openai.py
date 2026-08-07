"""OpenAI TTS adapter (gpt-4o-mini-tts / gpt-4o-tts / tts-1).

Docs:      https://platform.openai.com/docs/api-reference/audio/createSpeech
Auth:      Authorization: Bearer <OPENAI_API_KEY>
Endpoint:  POST https://api.openai.com/v1/audio/speech

Model:     Passed in JSON body as `model`. Two are in scope:
           - `gpt-4o-mini-tts` : conversational (latency-optimised)
           - `gpt-4o-tts`      : narration (quality-optimised)
           voices.yaml carries the correct model per use case; a buyer
           would swap them per use case, so we do too.

Voice:     One of 11 documented voices in the body's `voice` field:
           alloy · ash · ballad · coral · echo · fable · nova · onyx
           · sage · shimmer · verse.

Encoding:  `response_format` in body. Options: mp3 · opus · aac · flac
           · wav · pcm. We request wav directly so no PCM wrapping
           needed. Sample rate is fixed by OpenAI (24kHz for gpt-4o
           voices).

Streaming: OpenAI returns audio as raw bytes over chunked HTTP transfer.
           Use httpx `stream()` for a real TTFA measurement.

Billing:   Per character for tts-1; per second of audio for the gpt-4o
           variants. `chars_billed = len(opts.text)`;
           `billing_unit = "characters"` is a reasonable approximation
           for D6 cost modelling (the runner can cross-check against
           audio duration afterwards if per-second billing matters).

`instructions` parameter (gpt-4o-* only, for style guidance) NOT sent —
spec §3.4 requires sampling parameters at documented defaults; the
`instructions` field is a style modifier and sending one would be a
prereg deviation.

Added in prereg-v1.1 (2026-08-07, DEVIATIONS.md D-003).
"""

from __future__ import annotations

import time

import httpx

from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
)

DEFAULT_ENDPOINT = "https://api.openai.com/v1/audio/speech"
DEFAULT_TIMEOUT_S = 60.0


class OpenAIAdapter(ProviderAdapter):
    name = "openai"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        endpoint = self.endpoint or DEFAULT_ENDPOINT

        body: dict[str, object] = {
            "model": self.model,
            "input": opts.text,
            "voice": opts.voice_id,
            "response_format": opts.output_format,  # "wav" or "mp3"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
                            f"OpenAI HTTP {resp.status_code}: {body_text}",
                            provider=self.name,
                            status_code=resp.status_code,
                            retryable=resp.status_code in (429, 500, 502, 503, 504),
                            raw={
                                "body": body_text,
                                "model": self.model,
                                "voice": opts.voice_id,
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
                        or resp.headers.get("openai-request-id")
                    )
        except httpx.HTTPError as e:
            raise ProviderError(
                f"OpenAI network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0
        audio_bytes = b"".join(audio_chunks)

        if not audio_bytes:
            raise ProviderError(
                "OpenAI returned empty audio",
                provider=self.name,
                status_code=200,
                retryable=True,
            )

        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format=opts.output_format,
            sample_rate=opts.sample_rate,
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
            },
        )
