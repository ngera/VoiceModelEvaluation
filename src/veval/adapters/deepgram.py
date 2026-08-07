"""Deepgram Aura-2 adapter — the easiest onboarding, so it goes first.

Docs: https://developers.deepgram.com/reference/text-to-speech-api
Auth:  `Authorization: Token <API_KEY>`
Endpoint: POST https://api.deepgram.com/v1/speak?model=aura-2-<voice>
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

DEFAULT_ENDPOINT = "https://api.deepgram.com/v1/speak"
DEFAULT_TIMEOUT_S = 60.0


class DeepgramAdapter(ProviderAdapter):
    name = "deepgram"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        endpoint = self.endpoint or DEFAULT_ENDPOINT

        # Deepgram's model string embeds the voice, e.g. `aura-2-thalia-en`.
        # We accept either the full model in `self.model` (from providers.yaml)
        # or `opts.voice_id` overrides it for the doctor smoke test.
        model = opts.voice_id or self.model

        # Encoding: request wav (linear16) unless caller asked mp3.
        encoding, container = _encoding_for_format(opts.output_format)
        params: dict[str, str] = {"model": model, "encoding": encoding, "container": container}
        if opts.sample_rate:
            params["sample_rate"] = str(opts.sample_rate)

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {"text": opts.text}

        start = time.perf_counter()
        ttfa_ms: float | None = None
        audio_chunks: list[bytes] = []

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
                with client.stream(
                    "POST", endpoint, params=params, headers=headers, json=body
                ) as resp:
                    if resp.status_code != 200:
                        body_text = resp.read().decode("utf-8", errors="replace")[:500]
                        raise ProviderError(
                            f"Deepgram HTTP {resp.status_code}: {body_text}",
                            provider=self.name,
                            status_code=resp.status_code,
                            retryable=resp.status_code in (429, 500, 502, 503, 504),
                            raw={"body": body_text, "params": params},
                        )
                    for chunk in resp.iter_bytes():
                        if not chunk:
                            continue
                        if ttfa_ms is None and opts.streaming:
                            ttfa_ms = (time.perf_counter() - start) * 1000.0
                        audio_chunks.append(chunk)

                    request_id = resp.headers.get("dg-request-id") or resp.headers.get(
                        "x-dg-request-id"
                    )

        except httpx.HTTPError as e:
            raise ProviderError(
                f"Deepgram network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0
        # Streamed WAV carries a placeholder length header — patch it to reality.
        audio_bytes = finalize_wav_header(b"".join(audio_chunks))

        if not audio_bytes:
            raise ProviderError(
                "Deepgram returned empty audio",
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
            chars_billed=len(opts.text),  # Deepgram bills per character
            billing_unit="characters",
            provider=self.name,
            model=model,
            voice_id=opts.voice_id,
            meta={"request_id": request_id, "endpoint": endpoint},
        )


def _encoding_for_format(fmt: str) -> tuple[str, str]:
    """Map generic format → Deepgram (encoding, container)."""
    fmt = fmt.lower()
    if fmt == "wav":
        return "linear16", "wav"
    if fmt == "mp3":
        return "mp3", "none"
    raise ValueError(f"Unsupported output_format for Deepgram: {fmt}")
