"""Canopy Orpheus (Replicate-hosted) adapter.

Docs:      https://replicate.com/docs/reference/http#create-a-prediction
Model:     https://replicate.com/canopyai/orpheus-3b
Auth:      `Authorization: Bearer <REPLICATE_API_TOKEN>` (or legacy `Token`
           scheme — Bearer is the current form; older `Token <key>` also works).
Endpoint:  POST https://api.replicate.com/v1/models/{owner}/{name}/predictions
           (or `/v1/predictions` with explicit `version` SHA — used for pinning).

Flow:      Replicate is asynchronous by default.
             1. POST creates a prediction; response has `id` + `status`
                (`starting`, `processing`, `succeeded`, `failed`, `canceled`).
             2. `Prefer: wait=<sec>` (max 60) holds the connection open
                until the prediction terminates or the wait expires.
             3. If not terminal after Prefer wait, poll GET
                `/v1/predictions/{id}` until status is terminal.
             4. On success, `output` contains a URL (or list of URLs) to
                the generated audio; fetch that URL to get the bytes.

D1:        **N/A-hosted per spec §3.1.** Hosted inference measures
           Replicate's cold-start and queue behaviour, not Orpheus's
           first-token time. `ttfa_ms` is always `None`; `total_ms`
           covers the full submit + wait + poll + download pipeline.
           `meta.transport = "hosted-inference-poll"` so results tables
           can drop Orpheus from the D1 axis explicitly.

Billing:   Per generation on Replicate (~$0.003/gen at L40S GPU-seconds,
           spec §8 + DEFECT_REGISTER 3.6). `chars_billed = len(opts.text)`
           (informational for text volume); `billing_unit = "generation"`
           tells the D6 cost analyzer to multiply by the per-generation
           rate rather than per-character.

Version pinning: Replicate lets you either use the latest model version
           (`/v1/models/{owner}/{name}/predictions` — used here for the
           doctor probe) or a pinned SHA (`/v1/predictions` with
           `"version": "<sha>"`). For the campaign we should pin the SHA;
           doctor probe uses latest for simplicity. TODO(Phase-C): pin
           version SHA and log in analyzers.yaml before Phase D.
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

DEFAULT_ENDPOINT = "https://api.replicate.com/v1/predictions"
DEFAULT_TIMEOUT_S = 120.0
DEFAULT_WAIT_SEC = 60         # Prefer: wait= up to 60s (Replicate cap)
POLL_INTERVAL_S = 2.0
MAX_POLL_ATTEMPTS = 30        # 60s of polling after Prefer wait exits
TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}


class OrpheusAdapter(ProviderAdapter):
    name = "orpheus"

    def synthesize(self, opts: SynthesisOptions) -> SynthesisResult:
        # Always use the version-explicit endpoint /v1/predictions with
        # `version` in the body. The auto-latest pattern
        # `/v1/models/{owner}/{name}/predictions` returns HTTP 404 for
        # this community model (verified 2026-08-07 — see D-005). Version
        # SHA is pinned in providers.yaml -> ProviderConfig.version and
        # threaded through as self.version, which also strengthens the
        # prereg (specific SHA in config rather than "whatever Replicate
        # serves right now").
        if not self.version:
            raise ProviderError(
                "Orpheus requires a pinned version SHA (providers.yaml "
                "`version`). The auto-latest endpoint returns 404 for "
                "community models.",
                provider=self.name,
                status_code=None,
                retryable=False,
            )
        endpoint = self.endpoint or DEFAULT_ENDPOINT

        # Orpheus (lucataco/orpheus-3b-0.1-ft) input schema — verified
        # 2026-08-07 via GET /v1/models/lucataco/orpheus-3b-0.1-ft:
        #   text: the text to synthesize (NOT `prompt` — earlier draft
        #         had this wrong; fixed in D-004)
        #   voice: one of {tara, dan, josh, emma}
        #   top_p, temperature, max_new_tokens, repetition_penalty:
        #     left at documented defaults per spec §3.4
        body: dict[str, object] = {
            "version": self.version,
            "input": {
                "text": opts.text,
                "voice": opts.voice_id,
            },
        }

        auth_headers = {"Authorization": f"Bearer {self.api_key}"}
        create_headers = {
            **auth_headers,
            "Content-Type": "application/json",
            "Prefer": f"wait={DEFAULT_WAIT_SEC}",
        }

        start = time.perf_counter()

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
                resp = client.post(endpoint, headers=create_headers, json=body)
                # Replicate returns 200 or 201 when Prefer:wait terminates
                # inside the wait window; 202 Accepted when it hands back
                # a `status: "starting"` prediction to poll. All three are
                # valid create-responses; the polling loop below handles
                # the 202 case.
                if resp.status_code not in (200, 201, 202):
                    body_text = resp.text[:500]
                    # Replicate throttles by predictions-per-minute; the
                    # 429 body contains a JSON `detail` string but rarely
                    # a numeric wait. When Retry-After IS in the response
                    # header we honor it; otherwise default to a 60s
                    # wait for 429 (one throttle window). Any other
                    # status uses the runner's exponential fallback.
                    retry_after: float | None = None
                    if resp.status_code == 429:
                        header_val = (
                            resp.headers.get("retry-after")
                            or resp.headers.get("Retry-After")
                        )
                        if header_val:
                            try:
                                retry_after = float(header_val)
                            except ValueError:
                                retry_after = 60.0
                        else:
                            retry_after = 60.0
                    raise ProviderError(
                        f"Replicate HTTP {resp.status_code}: {body_text}",
                        provider=self.name,
                        status_code=resp.status_code,
                        retryable=resp.status_code in (429, 500, 502, 503, 504),
                        retry_after_s=retry_after,
                        raw={"body": body_text, "model": self.model, "version": self.version},
                    )
                prediction = resp.json()
                pred_id = prediction.get("id", "")
                status = prediction.get("status", "unknown")

                # Poll if not yet terminal after Prefer wait
                poll_url = f"https://api.replicate.com/v1/predictions/{pred_id}"
                for _ in range(MAX_POLL_ATTEMPTS):
                    if status in TERMINAL_STATUSES:
                        break
                    time.sleep(POLL_INTERVAL_S)
                    poll_resp = client.get(poll_url, headers=auth_headers)
                    if poll_resp.status_code != 200:
                        raise ProviderError(
                            f"Replicate poll HTTP {poll_resp.status_code}",
                            provider=self.name,
                            status_code=poll_resp.status_code,
                            retryable=True,
                        )
                    prediction = poll_resp.json()
                    status = prediction.get("status", "unknown")

                if status != "succeeded":
                    err = prediction.get("error") or "no error message"
                    raise ProviderError(
                        f"Replicate prediction status={status}: {err}",
                        provider=self.name,
                        status_code=None,
                        retryable=(status in {"failed"}),
                        raw={"prediction": prediction},
                    )

                output = prediction.get("output")
                if not output:
                    raise ProviderError(
                        "Replicate succeeded but returned no output",
                        provider=self.name,
                        status_code=200,
                        retryable=False,
                        raw={"prediction": prediction},
                    )
                # `output` is either a URL string or list of URLs (model-dependent)
                audio_url = output[0] if isinstance(output, list) else output

                # Download the audio from the output URL
                dl_resp = client.get(audio_url)
                if dl_resp.status_code != 200:
                    raise ProviderError(
                        f"Replicate output download HTTP {dl_resp.status_code}",
                        provider=self.name,
                        status_code=dl_resp.status_code,
                        retryable=True,
                    )
                audio_bytes = dl_resp.content

        except httpx.HTTPError as e:
            raise ProviderError(
                f"Replicate network error: {e}",
                provider=self.name,
                retryable=True,
            ) from e

        total_ms = (time.perf_counter() - start) * 1000.0

        if not audio_bytes:
            raise ProviderError(
                "Replicate returned empty audio bytes",
                provider=self.name,
                status_code=200,
                retryable=True,
            )

        # Orpheus's output URL typically points at a .wav file. If a future
        # model version returns a different container, we can detect via the
        # first bytes (RIFF header) but leave format as declared. Most
        # analyzers use ffmpeg to normalise inputs anyway.

        return SynthesisResult(
            audio_bytes=audio_bytes,
            audio_format="wav",
            sample_rate=None,  # decoded by downstream analyzers
            ttfa_ms=None,      # spec §3.1 — N/A-hosted, never populated
            total_ms=total_ms,
            chars_billed=len(opts.text),
            billing_unit="generation",  # Replicate bills per prediction
            provider=self.name,
            model=self.model,
            voice_id=opts.voice_id,
            meta={
                "prediction_id": pred_id,
                "output_url": audio_url,
                "endpoint": endpoint,
                "version": self.version,
                "transport": "hosted-inference-poll",
            },
        )
