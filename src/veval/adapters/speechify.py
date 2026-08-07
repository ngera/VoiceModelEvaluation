"""Speechify Simba 3.2 adapter.

Docs:      https://docs.sws.speechify.com/reference/getspeech
Auth:      Authorization: Bearer <SPEECHIFY_API_KEY>
Endpoint:  POST https://api.sws.speechify.com/v1/audio/speech

Model:     `simba-3.2` (Speechify's flagship — HI #1 at score 99).
           Passed in JSON body via `model` field.

Voice:     `voice_id` in the body. Simba voice IDs are typically short
           strings (e.g. `simba-english`, or per-voice UUIDs from the
           Speechify voice library at platform.speechify.ai).

Encoding:  `audio_format` in body: "mp3" | "wav" | "ogg" | "aac".
           We request wav directly so no PCM wrapping needed.

Language:  `language` in body — "en-US" for our English-only campaign.

Streaming: Speechify returns audio as raw bytes over chunked HTTP.
           Use httpx `stream()` for TTFA measurement.

Billing:   Per character. `chars_billed = len(opts.text)`;
           `billing_unit = "characters"`. Starter plan required
           ($10/mo, 1M chars) — free tier (50K chars/mo) insufficient
           for campaign volume.

Added in prereg-v1.1 (2026-08-07, DEVIATIONS.md D-003) as the
"audit HI #1" archetype.
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

DEFAULT_ENDPOINT = "https://api.sws.speechify.com/v1/audio/speech"
DEFAULT_TIMEOUT_S = 60.0


class SpeechifyAdapter(ProviderAdapter):
    name = "speechify"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        endpoint = self.endpoint or DEFAULT_ENDPOINT

        body: dict[str, object] = {
            "model": self.model,          # "simba-3.2"
            "input": opts.text,
            "voice_id": opts.voice_id,
            "audio_format": opts.output_format,  # "wav" or "mp3"
            "language": "en-US",
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
                            f"Speechify HTTP {resp.status_code}: {body_text}",
                            provider=self.name,
                            status_code=resp.status_code,
                            retryable=resp.status_code in (429, 500, 502, 503, 504),
                            raw={
                                "body": body_text,
                                "model": self.model,
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
                f"Speechify network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0
        audio_bytes = b"".join(audio_chunks)

        if not audio_bytes:
            raise ProviderError(
                "Speechify returned empty audio",
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
