"""Speechify Simba 3.2 adapter.

Docs:      https://docs.sws.speechify.com/reference/getspeech
Auth:      Authorization: Bearer <SPEECHIFY_API_KEY>
Endpoint:  POST https://api.sws.speechify.com/v1/audio/speech

Endpoint choice (2026-08-08, DEVIATIONS.md D-008):
  Speechify offers two endpoints. `/v1/audio/speech` returns a JSON
  envelope `{"audio_data": "<base64WAV>", ...}` — lossless WAV. The
  sibling `/v1/audio/stream` returns raw bytes but only in MP3
  (ID3/Lavf-tagged) regardless of `audio_format`. For a comparability
  study we hold audio format constant across providers, so we take
  WAV via the envelope and accept that TTFA is not measurable
  (buffered response). D8 latency for Speechify is `total_ms` only;
  the frontier charts annotate this the same way Fish's split-model
  is annotated.

Model:     `simba-3.2` (Speechify's flagship — HI #1 at score 99).
           Passed in JSON body via `model` field.

Voice:     `voice_id` in the body. Simba voice IDs are typically short
           strings (e.g. `simba-english`, or per-voice UUIDs from the
           Speechify voice library at platform.speechify.ai).

Encoding:  `audio_format: "wav"` in the request body. Response body
           is JSON; `audio_data` field is base64-encoded WAV.

Language:  `language` in body — "en-US" for our English-only campaign.

Billing:   Per character. `chars_billed = len(opts.text)`;
           `billing_unit = "characters"`. Starter plan required
           ($10/mo, 1M chars) — free tier (50K chars/mo) insufficient
           for campaign volume.

Added in prereg-v1.1 (2026-08-07, DEVIATIONS.md D-003) as the
"audit HI #1" archetype.
"""

from __future__ import annotations

import base64
import binascii
import json
import time

import httpx

from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
    finalize_wav_header,
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
            "audio_format": opts.output_format,  # "wav" (envelope) or "mp3"
            "language": "en-US",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start = time.perf_counter()
        request_id: str | None = None

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
                resp = client.post(endpoint, headers=headers, json=body)
                total_ms = (time.perf_counter() - start) * 1000.0
                if resp.status_code != 200:
                    body_text = resp.text[:500]
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
                request_id = resp.headers.get("x-request-id") or resp.headers.get(
                    "request-id"
                )
                try:
                    envelope = resp.json()
                except json.JSONDecodeError as e:
                    raise ProviderError(
                        f"Speechify returned non-JSON response: {e}",
                        provider=self.name,
                        status_code=200,
                        retryable=True,
                        raw={"body_head": resp.text[:200]},
                    ) from e
        except httpx.HTTPError as e:
            raise ProviderError(
                f"Speechify network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        audio_b64 = envelope.get("audio_data") if isinstance(envelope, dict) else None
        if not isinstance(audio_b64, str) or not audio_b64:
            raise ProviderError(
                "Speechify envelope missing `audio_data`",
                provider=self.name,
                status_code=200,
                retryable=True,
                raw={"envelope_keys": list(envelope) if isinstance(envelope, dict) else None},
            )
        try:
            raw = base64.b64decode(audio_b64)
        except (binascii.Error, ValueError) as e:
            raise ProviderError(
                f"Speechify audio_data base64 decode failed: {e}",
                provider=self.name,
                status_code=200,
                retryable=False,
            ) from e

        if not raw:
            raise ProviderError(
                "Speechify returned empty audio_data",
                provider=self.name,
                status_code=200,
                retryable=True,
            )
        # Speechify's WAV envelope carries 0xFFFFFFFF in both the RIFF size
        # and the data-chunk size — placeholder from their streaming
        # backend. Same Phase A defect class Deepgram/OpenAI had; caught
        # by the acceptance gate 2026-08-08.
        audio_bytes = (
            finalize_wav_header(raw) if opts.output_format.lower() == "wav" else raw
        )

        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format=opts.output_format,
            sample_rate=opts.sample_rate,
            # Buffered response — no streaming, so no TTFA. Annotated
            # in the frontier chart per D-008.
            ttfa_ms=None,
            total_ms=total_ms,
            chars_billed=len(opts.text),
            billing_unit="characters",
            provider=self.name,
            model=self.model,
            voice_id=opts.voice_id,
            meta={
                "request_id": request_id,
                "endpoint": endpoint,
                "buffered_response": True,
            },
        )
