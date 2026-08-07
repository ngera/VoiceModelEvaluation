"""Fish Audio S2.1-Pro adapter.

Docs:      https://docs.fish.audio/api-reference/endpoint/text-to-speech/text-to-speech
Auth:      Authorization: Bearer <FISH_API_KEY>
Endpoint:  POST https://api.fish.audio/v1/tts

Model:     Fish selects the tier via a `model` HTTP header (NOT the JSON
           body). Values in scope for this project:
           - `s2.1-pro`      : paid tier (latency measurement)
           - `s2.1-pro-free` : free tier — best-effort SLA, window closes
             2026-08-31 (spec §3.1 R9). Used for quality / WER.
           The split is declared in voices.yaml via `split_model_from_quality`
           + `quality_model`; the runner picks the right model per mode.

Voice:     `reference_id` in the JSON body maps to a Fish voice_id
           (32-char hex string, e.g. `9a9cf47702da476aa4629e2506d4a857`).

Billing:   Per UTF-8 byte. `chars_billed` is set to
           `len(text.encode("utf-8"))`, `billing_unit="bytes"`.
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

DEFAULT_ENDPOINT = "https://api.fish.audio/v1/tts"
DEFAULT_TIMEOUT_S = 60.0


class FishAdapter(ProviderAdapter):
    name = "fish"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        endpoint = self.endpoint or DEFAULT_ENDPOINT

        body: dict[str, object] = {
            "text": opts.text,
            "reference_id": opts.voice_id,
            "format": opts.output_format,  # "wav" or "mp3"
        }
        if opts.sample_rate:
            body["sample_rate"] = opts.sample_rate

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "model": self.model,  # tier routing lives here, not in body
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
                            f"Fish HTTP {resp.status_code}: {body_text}",
                            provider=self.name,
                            status_code=resp.status_code,
                            retryable=resp.status_code in (429, 500, 502, 503, 504),
                            raw={"body": body_text, "model": self.model},
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
                f"Fish network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0
        audio_bytes = b"".join(audio_chunks)
        if opts.output_format == "wav":
            # Streamed WAV — fix RIFF/data sizes so downstream analyzers
            # (RTF, VAD, LUFS, TTSDS2) read the real duration
            # (Phase A defect class, spec §Phase A closeout).
            audio_bytes = finalize_wav_header(audio_bytes)

        if not audio_bytes:
            raise ProviderError(
                "Fish returned empty audio",
                provider=self.name,
                status_code=200,
                retryable=True,
            )

        # Fish bills per UTF-8 byte for English text (spec Appendix B.2).
        chars_billed = len(opts.text.encode("utf-8"))

        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format=opts.output_format,
            sample_rate=opts.sample_rate,
            ttfa_ms=ttfa_ms,
            total_ms=total_ms,
            chars_billed=chars_billed,
            billing_unit="bytes",
            provider=self.name,
            model=self.model,
            voice_id=opts.voice_id,
            meta={"request_id": request_id, "endpoint": endpoint},
        )
