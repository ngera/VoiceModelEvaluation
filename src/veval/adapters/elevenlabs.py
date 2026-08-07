"""ElevenLabs adapter (Flash v2.5 conversational · Multilingual v2/v3 narration).

Docs:      https://elevenlabs.io/docs/api-reference/text-to-speech-stream
Auth:      `xi-api-key` header (ElevenLabs' own scheme, not Bearer).
Endpoint:  POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream

Model:     Passed in the JSON body as `model_id`. Two are in scope:
           - `eleven_flash_v2_5`      : conversational (latency-optimised)
           - `eleven_multilingual_v2` : narration (quality-optimised)
           voices.yaml carries the correct model per use case; a buyer
           would swap them per use case, so we do too.

Voice:     Voice UUID goes in the URL path, not the body. 20-char
           alphanumeric strings like `g6xIsTj2HwM6VR4iXFCw`.

Encoding:  Request `pcm_24000` (raw PCM at 24kHz) via `output_format`
           query param; wrap in WAV header via `pcm_to_wav()` for
           downstream analyzer uniformity. MP3 (`mp3_44100_128`) also
           supported if opts.output_format == "mp3".

Billing:   Per character. `chars_billed = len(opts.text)`.
"""

from __future__ import annotations

import time

import httpx

from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
    pcm_to_wav,
)

DEFAULT_ENDPOINT_TEMPLATE = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
DEFAULT_TIMEOUT_S = 60.0
DEFAULT_SAMPLE_RATE = 24000


class ElevenLabsAdapter(ProviderAdapter):
    name = "elevenlabs"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        sample_rate = opts.sample_rate or DEFAULT_SAMPLE_RATE

        # Voice UUID goes in the path. Allow endpoint override for testing
        # but default to the standard streaming endpoint.
        if self.endpoint:
            endpoint = self.endpoint
        else:
            endpoint = DEFAULT_ENDPOINT_TEMPLATE.format(voice_id=opts.voice_id)

        # output_format is a QUERY parameter, not body.
        if opts.output_format == "wav":
            output_format = f"pcm_{sample_rate}"
        elif opts.output_format == "mp3":
            output_format = "mp3_44100_128"
        else:
            raise ValueError(f"Unsupported output_format for ElevenLabs: {opts.output_format}")

        params = {"output_format": output_format}

        body: dict[str, object] = {
            "text": opts.text,
            "model_id": self.model,
        }
        # Note: voice_settings (stability, similarity_boost, style) left at
        # ElevenLabs defaults per spec §3.4 ("sampling parameters left at
        # documented defaults"). Adding them here would be a prereg deviation.

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/*",
        }

        start = time.perf_counter()
        ttfa_ms: float | None = None
        audio_chunks: list[bytes] = []
        request_id: str | None = None

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
                with client.stream(
                    "POST", endpoint, params=params, headers=headers, json=body
                ) as resp:
                    if resp.status_code != 200:
                        body_text = resp.read().decode("utf-8", errors="replace")[:500]
                        raise ProviderError(
                            f"ElevenLabs HTTP {resp.status_code}: {body_text}",
                            provider=self.name,
                            status_code=resp.status_code,
                            retryable=resp.status_code in (429, 500, 502, 503, 504),
                            raw={
                                "body": body_text,
                                "model_id": self.model,
                                "voice_id": opts.voice_id,
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
                f"ElevenLabs network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0
        raw_bytes = b"".join(audio_chunks)

        if not raw_bytes:
            raise ProviderError(
                "ElevenLabs returned empty audio",
                provider=self.name,
                status_code=200,
                retryable=True,
            )

        # PCM is raw samples; wrap in WAV header. MP3 is self-contained.
        if opts.output_format == "wav":
            audio_bytes = pcm_to_wav(raw_bytes, sample_rate=sample_rate)
        else:
            audio_bytes = raw_bytes

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
                "output_format": output_format,
            },
        )
