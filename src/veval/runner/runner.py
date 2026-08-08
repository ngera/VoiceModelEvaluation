"""Runner core — orchestrates provider adapter calls across the corpus.

Design principles (CLAUDE.md conventions):
  - Errors as data: every synthesis attempt is logged to api_log.jsonl.
    ProviderErrors mark an item as failed but never crash the run.
  - Immutable run store: writes to runs/<run_id>/{manifest.json,audio/,
    api_log.jsonl}. One run per invocation; not appended.
  - Same run-store shape across all three modes (kind=campaign|variance|latency).
  - Adapters are sync (Phase A decision); this runner uses a threadpool
    executor to parallelise provider work while adapters stay simple.

Modes:
  campaign:  one generation per (provider, use_case, item)
  variance:  n_draws per (provider, use_case, item) — D.3
  latency:   n_trials per (provider, use_case, one_item), strictly serial — D.4

D.1 scope: campaign mode only. Variance + latency stubbed for later
sub-phases.
"""

from __future__ import annotations

import concurrent.futures
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal

from veval.adapters import ADAPTERS
from veval.adapters.base import (
    ProviderAdapter,
    ProviderError,
    SynthesisOptions,
    SynthesisResult,
)
from veval.config import (
    CorpusFile,
    CorpusItem,
    ProviderConfig,
    ProvidersFile,
    UseCase,
    VoiceSelection,
    VoicesFile,
    load_corpus,
    load_providers,
    load_voices,
)
from veval.store.run_store import Run, default_run_store

# --- Retry policy ---
MAX_RETRIES = 3
BACKOFF_BASE_S = 1.0  # exponential: 1s, 2s, 4s

# --- Per-provider concurrency defaults ---
# Free/starter-tier caps we've observed. Runner never exceeds these
# without explicit override. Cartesia's 2-cap is the tightest.
DEFAULT_PROVIDER_CONCURRENCY = {
    "cartesia": 2,   # 2 free / 3 Pro; conservative default
    "fish": 3,       # generous
    "openai": 5,
    "elevenlabs": 3,
    "deepgram": 3,
    "google": 5,
    "speechify": 3,
    "orpheus": 1,    # Replicate rate-limits without payment method
}


class RunMode(str, Enum):
    campaign = "campaign"
    variance = "variance"
    latency = "latency"


@dataclass
class ItemResult:
    """One (provider, use_case, item, draw) synthesis result."""

    provider: str
    use_case: UseCase
    item_id: str
    draw: int = 0
    ok: bool = False
    result: SynthesisResult | None = None
    error: str = ""
    attempts: int = 0
    audio_path: Path | None = None


@dataclass
class RunSummary:
    """Aggregate summary of a run."""

    mode: RunMode
    run_id: str
    run_dir: Path
    total: int = 0
    ok: int = 0
    failed: int = 0
    per_provider_ok: dict[str, int] = field(default_factory=dict)
    per_provider_failed: dict[str, int] = field(default_factory=dict)
    elapsed_s: float = 0.0


class Runner:
    """Orchestrates adapter calls, respects concurrency caps, logs everything.

    Constructor loads configs once; call `run_campaign()` (or later
    `run_variance()` / `run_latency()`) to execute.
    """

    def __init__(
        self,
        providers_file: Path = Path("configs/providers.yaml"),
        voices_file: Path = Path("configs/voices.yaml"),
        corpus_dir: Path = Path("corpus"),
        provider_concurrency: dict[str, int] | None = None,
    ) -> None:
        self.providers: ProvidersFile = load_providers(providers_file)
        self.voices: VoicesFile = load_voices(voices_file)
        self.corpus_dir = corpus_dir
        self.provider_concurrency = provider_concurrency or DEFAULT_PROVIDER_CONCURRENCY

    # --- Config resolution ---

    def _load_corpus(self, use_case: UseCase) -> CorpusFile:
        return load_corpus(self.corpus_dir / f"{use_case}.yaml")

    def _resolve_voice_model(
        self, provider: str, use_case: UseCase, mode: RunMode
    ) -> tuple[str, str]:
        """Return (voice_id, model_string) for this (provider, use_case, mode).

        Split-model providers (Fish): mode selects which model.
          - `campaign` / `variance` (quality signals) → quality_model if set
          - `latency` → latency model (voice.model)
        Non-split providers: voice.model regardless of mode.
        """
        v = self.voices.get(provider, use_case)
        if v.split_model_from_quality and v.quality_model and mode != RunMode.latency:
            return v.voice_id, v.quality_model
        return v.voice_id, v.model

    def _build_adapter(self, p: ProviderConfig) -> ProviderAdapter:
        api_key = os.environ.get(p.env_key)
        if not api_key:
            raise RuntimeError(f"{p.name}: env var {p.env_key} not set")
        cls = ADAPTERS.get(p.name)
        if cls is None:
            raise RuntimeError(f"{p.name}: no adapter class registered")
        # NOTE: adapter model+voice_id are supplied per-call via SynthesisOptions;
        # here we pass model=<placeholder> because adapters read model from
        # SynthesisOptions in campaign mode. We hydrate the correct model when
        # calling synthesize(). For adapters that read from self.model at
        # construct time (they all do currently), we pass a dummy string that
        # will be overridden by the SynthesisOptions.voice_id when needed.
        # Cleaner alternative: build a new adapter per (provider, use_case) —
        # cheap because there's no shared connection state (each call opens
        # a new httpx.Client). Doing that below.
        return cls(api_key=api_key, model="", endpoint=p.endpoint, version=p.version)

    def _build_adapter_for_call(
        self, p: ProviderConfig, model: str
    ) -> ProviderAdapter:
        """Build an adapter with the model string this call needs."""
        api_key = os.environ.get(p.env_key)
        if not api_key:
            raise RuntimeError(f"{p.name}: env var {p.env_key} not set")
        cls = ADAPTERS.get(p.name)
        if cls is None:
            raise RuntimeError(f"{p.name}: no adapter class registered")
        return cls(api_key=api_key, model=model, endpoint=p.endpoint, version=p.version)

    # --- Single-item synthesis with retry + error-as-data ---

    def _synthesize_one(
        self,
        p: ProviderConfig,
        use_case: UseCase,
        item: CorpusItem,
        mode: RunMode,
        draw: int,
        run: Run,
    ) -> ItemResult:
        voice_id, model = self._resolve_voice_model(p.name, use_case, mode)
        try:
            adapter = self._build_adapter_for_call(p, model)
        except Exception as e:  # noqa: BLE001
            run.log_api({
                "provider": p.name, "use_case": use_case, "item_id": item.id,
                "draw": draw, "status": "error", "error_type": type(e).__name__,
                "message": str(e), "attempts": 0,
            })
            return ItemResult(
                provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
                ok=False, error=f"{type(e).__name__}: {e}",
            )

        opts = SynthesisOptions(
            text=item.text,
            voice_id=voice_id,
            output_format="wav",
            streaming=(mode == RunMode.latency),
        )

        # Retry loop for transport failures. Content failures (empty audio,
        # HTTP 4xx that isn't retryable) fail on the first attempt.
        last_error: str = ""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = adapter.synthesize(opts)
            except ProviderError as e:
                last_error = f"{type(e).__name__}: {e}"
                if e.retryable and attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE_S * (2 ** (attempt - 1)))
                    continue
                run.log_api({
                    "provider": p.name, "use_case": use_case, "item_id": item.id,
                    "draw": draw, "status": "error", "error_type": type(e).__name__,
                    "message": str(e), "status_code": e.status_code,
                    "retryable": e.retryable, "attempts": attempt,
                    "voice_id": voice_id, "model": model,
                })
                return ItemResult(
                    provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
                    ok=False, error=last_error, attempts=attempt,
                )
            except Exception as e:  # noqa: BLE001
                # Unexpected: never crash the run, but flag it distinctly
                last_error = f"unexpected {type(e).__name__}: {e}"
                run.log_api({
                    "provider": p.name, "use_case": use_case, "item_id": item.id,
                    "draw": draw, "status": "error", "error_type": type(e).__name__,
                    "message": str(e), "attempts": attempt,
                    "voice_id": voice_id, "model": model,
                })
                return ItemResult(
                    provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
                    ok=False, error=last_error, attempts=attempt,
                )

            # Success — write audio, log, return
            # Path layout: audio/<provider>/<use_case>/<item_id>[_dNN].wav
            provider_dir = run.dir / "audio" / p.name / use_case
            provider_dir.mkdir(parents=True, exist_ok=True)
            suffix = f"_d{draw:02d}" if mode == RunMode.variance else ""
            audio_path = provider_dir / f"{item.id}{suffix}.{result.audio_format}"
            audio_path.write_bytes(result.audio_bytes)

            # Update manifest tracking
            if p.name not in run.manifest.providers:
                run.manifest.providers.append(p.name)
            if item.id not in run.manifest.items:
                run.manifest.items.append(item.id)
            run.manifest.audio_count += 1

            run.log_api({
                "provider": p.name, "use_case": use_case, "item_id": item.id,
                "draw": draw, "status": "ok",
                "ttfa_ms": result.ttfa_ms, "total_ms": result.total_ms,
                "chars_billed": result.chars_billed,
                "billing_unit": result.billing_unit,
                "audio_bytes": len(result.audio_bytes),
                "audio_path": str(audio_path.relative_to(run.dir)),
                "voice_id": voice_id, "model": model,
                "attempts": attempt, "meta": result.meta,
            })
            return ItemResult(
                provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
                ok=True, result=result, attempts=attempt, audio_path=audio_path,
            )

        # Should never reach here — loop above returns in every path
        return ItemResult(
            provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
            ok=False, error=last_error, attempts=MAX_RETRIES,
        )

    # --- Public: campaign mode ---

    def run_campaign(
        self,
        use_cases: list[UseCase] | None = None,
        provider_names: list[str] | None = None,
        item_ids: list[str] | None = None,
    ) -> RunSummary:
        """Run the primary campaign: one generation per (provider, use_case, item).

        Args:
            use_cases: subset of use cases to run (default: both).
            provider_names: subset of providers to run (default: all in providers.yaml).
            item_ids: subset of item IDs to run (default: full corpus per use case).
                     Used for the $1 pilot (--items S01 S02 S03 S04 S05).
        """
        use_cases = use_cases or ["conversational", "narration"]
        providers = [
            p for p in self.providers.providers
            if provider_names is None or p.name in provider_names
        ]

        run = default_run_store().new_run(kind="campaign", extras={
            "mode": RunMode.campaign.value,
            "use_cases": use_cases,
            "provider_names": [p.name for p in providers],
            "item_ids_filter": item_ids,
        })
        started = time.perf_counter()

        # Build the full work list: (provider, use_case, item) tuples
        work: list[tuple[ProviderConfig, UseCase, CorpusItem]] = []
        for uc in use_cases:
            corpus = self._load_corpus(uc)  # type: ignore[arg-type]
            items = [i for i in corpus.items if item_ids is None or i.id in item_ids]
            for p in providers:
                for item in items:
                    work.append((p, uc, item))

        # Parallelise across providers with per-provider concurrency caps.
        # Simple approach: one submit-and-wait per provider, provider items
        # run inside a bounded threadpool sized to the provider's cap.
        results: list[ItemResult] = []

        for p in providers:
            provider_work = [w for w in work if w[0].name == p.name]
            if not provider_work:
                continue
            cap = self.provider_concurrency.get(p.name, 3)
            with concurrent.futures.ThreadPoolExecutor(max_workers=cap) as pool:
                futures = [
                    pool.submit(self._synthesize_one, prov, uc, item, RunMode.campaign, 0, run)
                    for (prov, uc, item) in provider_work
                ]
                for fut in concurrent.futures.as_completed(futures):
                    results.append(fut.result())

        elapsed = time.perf_counter() - started
        run.finalize()

        summary = RunSummary(
            mode=RunMode.campaign, run_id=run.manifest.run_id, run_dir=run.dir,
            total=len(results),
            ok=sum(1 for r in results if r.ok),
            failed=sum(1 for r in results if not r.ok),
            elapsed_s=elapsed,
        )
        for r in results:
            if r.ok:
                summary.per_provider_ok[r.provider] = summary.per_provider_ok.get(r.provider, 0) + 1
            else:
                summary.per_provider_failed[r.provider] = summary.per_provider_failed.get(r.provider, 0) + 1
        return summary

    # --- Public: variance mode (D.3, stubbed) ---

    def run_variance(self, use_cases: list[UseCase] | None = None) -> RunSummary:
        raise NotImplementedError("Variance mode lands in Phase D.3")

    # --- Public: latency mode (D.4, stubbed) ---

    def run_latency(
        self, provider_name: str, item_id: str, trials: int = 50,
    ) -> RunSummary:
        raise NotImplementedError("Latency mode lands in Phase D.4")
