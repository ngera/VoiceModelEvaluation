"""Google Cloud TTS adapter (Chirp3-HD).

Docs:      https://cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize
Auth:      API key via `?key=<KEY>` query parameter (or `X-Goog-Api-Key` header).
           Path A per Phase C decision (2026-08-07): raw httpx + API key for
           transport uniformity across all 6 adapters. Service-account auth
           (GOOGLE_APPLICATION_CREDENTIALS) would need `google.auth` for JWT
           minting and gives Google-only overhead on D1 measurements.
Endpoint:  POST https://texttospeech.googleapis.com/v1/text:synthesize

Model:     Chirp3-HD voices encode the model in the voice name
           (`en-US-Chirp3-HD-Achernar` etc.). Both self.model and
           opts.voice_id contain the full voice name; they should match.

Response:  JSON with base64-encoded audio in `audioContent`. **Buffered
           only** on REST (streaming is gRPC-only and Preview status per
           spec §3.1 — defect 3.15 keeps the option open to probe
           streaming later, but v1 ships buffered REST). TTFA on Google
           therefore equals total_ms and is NOT comparable to streaming
           providers' TTFA; every results-table row for Google carries
           an on-chart footnote. `meta.transport = "buffered-rest"` so
           downstream can enforce this.

Encoding:  Request LINEAR16 (raw PCM); wrap in WAV header via
           `pcm_to_wav()` so audio_bytes matches Deepgram/Fish WAV output.

Billing:   Per character; response body doesn't include the billed count,
           so `chars_billed = len(opts.text)` is the approximation
           (Google counts spaces and SSML tags — for plain text this is
           accurate to ±0 characters).
"""

from __future__ import annotations

import base64
import time

import httpx

from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
    pcm_to_wav,
)

DEFAULT_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
DEFAULT_TIMEOUT_S = 60.0
DEFAULT_SAMPLE_RATE = 24000  # Chirp3-HD LINEAR16 default


class GoogleAdapter(ProviderAdapter):
    name = "google"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        endpoint = self.endpoint or DEFAULT_ENDPOINT
        sample_rate = opts.sample_rate or DEFAULT_SAMPLE_RATE

        # Language code is the first two dash-separated segments of the voice
        # name — e.g. `en-US-Chirp3-HD-Achernar` -> `en-US`.
        # This is a Google requirement; the voice name alone is not enough.
        voice_name = opts.voice_id
        language_code = "-".join(voice_name.split("-")[:2]) if "-" in voice_name else "en-US"

        body: dict[str, object] = {
            "input": {"text": opts.text},
            "voice": {
                "languageCode": language_code,
                "name": voice_name,
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16" if opts.output_format == "wav" else "MP3",
                "sampleRateHertz": sample_rate,
            },
        }

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
                resp = client.post(endpoint, params=params, headers=headers, json=body)
        except httpx.HTTPError as e:
            raise ProviderError(
                f"Google network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0

        if resp.status_code != 200:
            body_text = resp.text[:500]
            raise ProviderError(
                f"Google HTTP {resp.status_code}: {body_text}",
                provider=self.name,
                status_code=resp.status_code,
                retryable=resp.status_code in (429, 500, 502, 503, 504),
                raw={"body": body_text},
            )

        try:
            payload = resp.json()
            audio_b64 = payload["audioContent"]
        except (ValueError, KeyError) as e:
            raise ProviderError(
                f"Google response missing audioContent: {e}",
                provider=self.name,
                status_code=200,
                retryable=False,
                raw={"body": resp.text[:500]},
            ) from e

        try:
            pcm_or_encoded = base64.b64decode(audio_b64)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(
                f"Google audioContent base64 decode failed: {e}",
                provider=self.name,
                status_code=200,
                retryable=False,
            ) from e

        if not pcm_or_encoded:
            raise ProviderError(
                "Google returned empty audio",
                provider=self.name,
                status_code=200,
                retryable=True,
            )

        # Wrap raw PCM in WAV header when we requested LINEAR16; MP3 is
        # already self-contained and doesn't need wrapping.
        if opts.output_format == "wav":
            audio_bytes = pcm_to_wav(pcm_or_encoded, sample_rate=sample_rate)
        else:
            audio_bytes = pcm_or_encoded

        # Buffered REST: TTFA is undefined (all bytes arrive together).
        # Report None if the caller asked for streaming — the doctor and
        # runner know how to interpret None.
        ttfa_ms = None if opts.streaming else None

        request_id = (
            resp.headers.get("x-request-id")
            or resp.headers.get("request-id")
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
            model=voice_name,
            voice_id=voice_name,
            meta={
                "request_id": request_id,
                "endpoint": endpoint,
                "transport": "buffered-rest",  # footnote D1 for Google
                "language_code": language_code,
            },
        )
