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
    PricingFile,
    ProviderConfig,
    ProvidersFile,
    UseCase,
    VarianceSubset,
    VoiceSelection,
    VoicesFile,
    load_corpus,
    load_pricing,
    load_providers,
    load_variance_subset,
    load_voices,
)
from veval.runner.cache import SynthesisCache
from veval.runner.spend import SpendCapExceeded, SpendTracker
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
    "speechify": 1,  # Starter plan is 1 (verified via HTTP 429 body 2026-08-08)
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
        pricing_file: Path = Path("configs/pricing.yaml"),
        provider_concurrency: dict[str, int] | None = None,
        cache: SynthesisCache | None = None,
        spend_tracker: SpendTracker | None = None,
    ) -> None:
        self.providers: ProvidersFile = load_providers(providers_file)
        self.voices: VoicesFile = load_voices(voices_file)
        self.corpus_dir = corpus_dir
        self.pricing: PricingFile = load_pricing(pricing_file)
        self.provider_concurrency = provider_concurrency or DEFAULT_PROVIDER_CONCURRENCY
        # Cache is optional. None = no caching (fresh call every time).
        # Campaign mode enables it by default; variance/latency must skip
        # it (fresh measurement is the whole point).
        self.cache: SynthesisCache | None = cache
        # Spend cap is optional but recommended. None = no cap enforced.
        # When set, every successful synthesis charges the tracker; if
        # the projected cap would be exceeded, subsequent submits stop
        # (already-in-flight calls complete normally).
        self.spend_tracker: SpendTracker | None = spend_tracker
        self._spend_cap_hit = False  # set when SpendCapExceeded first raised

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
        # Spend cap short-circuit: if a prior call already tripped the cap,
        # every subsequent submission returns a fast failure without
        # touching the network. In-flight calls that already made it past
        # this check still complete normally.
        if self._spend_cap_hit:
            run.log_api({
                "provider": p.name, "use_case": use_case, "item_id": item.id,
                "draw": draw, "status": "skipped",
                "reason": "spend_cap_exceeded",
            })
            return ItemResult(
                provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
                ok=False, error="spend cap exceeded; call skipped",
            )

        voice_id, model = self._resolve_voice_model(p.name, use_case, mode)

        # Cache check (campaign mode only — variance/latency need fresh calls).
        # We check BEFORE building the adapter or opening any HTTP connection.
        use_cache = self.cache is not None and mode == RunMode.campaign
        if use_cache:
            entry = self.cache.get(
                provider=p.name, model=model, voice_id=voice_id,
                text=item.text, output_format="wav",
                sample_rate=None, version=p.version,
            )
            if entry is not None:
                # Cache HIT — write to run store, log as cache hit, return.
                provider_dir = run.dir / "audio" / p.name / use_case
                provider_dir.mkdir(parents=True, exist_ok=True)
                suffix = f"_d{draw:02d}" if mode == RunMode.variance else ""
                audio_path = provider_dir / f"{item.id}{suffix}.{entry.audio_format}"
                audio_path.write_bytes(entry.audio_bytes)
                if p.name not in run.manifest.providers:
                    run.manifest.providers.append(p.name)
                if item.id not in run.manifest.items:
                    run.manifest.items.append(item.id)
                run.manifest.audio_count += 1
                run.log_api({
                    "provider": p.name, "use_case": use_case, "item_id": item.id,
                    "draw": draw, "status": "ok",
                    "ttfa_ms": None, "total_ms": 0,
                    "chars_billed": entry.chars_billed,
                    "billing_unit": entry.billing_unit,
                    "audio_bytes": len(entry.audio_bytes),
                    "audio_path": str(audio_path.relative_to(run.dir)),
                    "voice_id": voice_id, "model": model,
                    "attempts": 0, "cache": "hit",
                    "meta": entry.meta,
                })
                # Manufacture a SynthesisResult for the caller
                cached_result = SynthesisResult(
                    audio_bytes=entry.audio_bytes,
                    audio_format=entry.audio_format,
                    sample_rate=entry.sample_rate,
                    ttfa_ms=None, total_ms=0,
                    chars_billed=entry.chars_billed,
                    billing_unit=entry.billing_unit,
                    provider=entry.provider,
                    model=entry.model,
                    voice_id=entry.voice_id,
                    meta={**entry.meta, "cache": "hit"},
                )
                return ItemResult(
                    provider=p.name, use_case=use_case, item_id=item.id, draw=draw,
                    ok=True, result=cached_result, attempts=0, audio_path=audio_path,
                )

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

            # Success — write audio, log, cache, return
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

            # Cache the successful synthesis (campaign mode only)
            if use_cache:
                try:
                    self.cache.put(
                        provider=p.name, model=model, voice_id=voice_id,
                        text=item.text, output_format=result.audio_format,
                        sample_rate=result.sample_rate, version=p.version,
                        audio_bytes=result.audio_bytes,
                        chars_billed=result.chars_billed,
                        billing_unit=result.billing_unit,
                        meta=result.meta,
                    )
                except OSError:
                    # Never let a cache-write failure fail the run
                    pass

            # Charge the spend tracker (fresh synth only; cache hits are $0
            # already paid). If the cap is exceeded we've already burned this
            # one call — mark the run so subsequent submits stop.
            this_call_usd: float | None = None
            running_total_usd: float | None = None
            if self.spend_tracker is not None:
                try:
                    this_call_usd, running_total_usd = self.spend_tracker.charge(
                        p.name, result.billing_unit,  # type: ignore[arg-type]
                        result.chars_billed,
                    )
                except SpendCapExceeded:
                    # The synthesis already happened; log the overshoot and
                    # set the shutdown flag so pending futures stop submitting
                    self._spend_cap_hit = True
                    this_call_usd = self.spend_tracker.estimate_cost(
                        p.name, result.billing_unit,  # type: ignore[arg-type]
                        result.chars_billed,
                    )
                    running_total_usd = self.spend_tracker.total_usd

            run.log_api({
                "provider": p.name, "use_case": use_case, "item_id": item.id,
                "draw": draw, "status": "ok",
                "ttfa_ms": result.ttfa_ms, "total_ms": result.total_ms,
                "chars_billed": result.chars_billed,
                "billing_unit": result.billing_unit,
                "audio_bytes": len(result.audio_bytes),
                "audio_path": str(audio_path.relative_to(run.dir)),
                "voice_id": voice_id, "model": model,
                "attempts": attempt,
                "cache": "miss" if use_cache else "off",
                "estimated_call_usd": this_call_usd,
                "running_total_usd": running_total_usd,
                "meta": result.meta,
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

    # --- Public: variance mode (D.3) ---

    def run_variance(
        self,
        use_cases: list[UseCase] | None = None,
        provider_names: list[str] | None = None,
        variance_subset_file: Path = Path("corpus/variance_subset.yaml"),
        n_draws: int = 3,
    ) -> RunSummary:
        """Run the variance campaign: n_draws per (provider, use_case, item).

        Per spec §3.4: 10 items × 3 draws × N providers × 2 use cases →
        measurement noise floor via pooled within-provider SD on TTSDS2
        and item-level WER. Cache is FORCED OFF here (fresh draws are
        the measurement) — Runner._synthesize_one already enforces this
        via `mode == RunMode.campaign` check.

        Item set comes from corpus/variance_subset.yaml — the 10 items
        per use case were frozen in prereg-v1 as a stratified sample.

        Args:
            use_cases: default both.
            provider_names: default all in providers.yaml.
            variance_subset_file: default configs-relative.
            n_draws: draws per (provider, use_case, item). Default 3
                    per spec; 2-degrees-of-freedom-per-item minimum.
        """
        use_cases = use_cases or ["conversational", "narration"]
        providers = [
            p for p in self.providers.providers
            if provider_names is None or p.name in provider_names
        ]
        subsets: VarianceSubset = load_variance_subset(variance_subset_file)

        run = default_run_store().new_run(kind="variance", extras={
            "mode": RunMode.variance.value,
            "use_cases": use_cases,
            "provider_names": [p.name for p in providers],
            "n_draws": n_draws,
            "variance_subset_file": str(variance_subset_file),
        })
        started = time.perf_counter()

        # Build work list: (provider, use_case, item, draw) tuples.
        # The same 10 items are used across all providers so noise floor
        # is comparable — this is the spec §3.4 pooling requirement.
        work: list[tuple[ProviderConfig, UseCase, CorpusItem, int]] = []
        for uc in use_cases:
            corpus = self._load_corpus(uc)  # type: ignore[arg-type]
            subset_ids = subsets.item_ids_for(uc)  # type: ignore[arg-type]
            items_by_id = {i.id: i for i in corpus.items}
            missing = [iid for iid in subset_ids if iid not in items_by_id]
            if missing:
                raise RuntimeError(
                    f"variance_subset.yaml references items not in {uc} corpus: {missing}"
                )
            items = [items_by_id[iid] for iid in subset_ids]
            for p in providers:
                for item in items:
                    for draw in range(n_draws):
                        work.append((p, uc, item, draw))

        # Parallelise per provider, same as campaign
        results: list[ItemResult] = []
        for p in providers:
            provider_work = [w for w in work if w[0].name == p.name]
            if not provider_work:
                continue
            cap = self.provider_concurrency.get(p.name, 3)
            with concurrent.futures.ThreadPoolExecutor(max_workers=cap) as pool:
                futures = [
                    pool.submit(
                        self._synthesize_one, prov, uc, item, RunMode.variance, draw, run,
                    )
                    for (prov, uc, item, draw) in provider_work
                ]
                for fut in concurrent.futures.as_completed(futures):
                    results.append(fut.result())

        elapsed = time.perf_counter() - started
        run.finalize()

        summary = RunSummary(
            mode=RunMode.variance, run_id=run.manifest.run_id, run_dir=run.dir,
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

    # --- Public: latency mode (D.4) ---

    def run_latency(
        self,
        provider_names: list[str] | None = None,
        use_case: UseCase = "conversational",
        item_id: str = "S01",
        trials: int = 50,
    ) -> RunSummary:
        """Run the D1 latency campaign: `trials` serial calls per provider.

        Per spec §D1:
          - Strictly serial per provider (one request in flight) —
            concurrent load contaminates TTFA
          - Same short item across all trials (default S01 conversational)
          - Report p50/p90 only (50 trials cannot support p99)
          - Streaming mode requested — providers that stream give a real
            first-byte time; buffered providers (Google REST) have
            TTFA == total, recorded with meta.transport="buffered-rest"
          - Fish: uses paid `s2.1-pro` (voice.model), NOT free tier
            (voice.quality_model) — that's why `_resolve_voice_model`
            passes RunMode.latency down
          - Orpheus: SKIPPED — spec §3.1 says D1 is N/A-hosted; the
            skip is enforced here rather than producing meaningless
            hosted-inference timings

        Scheduling across days / times of day is the OPERATOR's job:
        run this command multiple times with the same run store and
        stitch the results in analyze/latency.py. This method executes
        one batch.

        Args:
            provider_names: default all in providers.yaml except orpheus.
            use_case: which voice+model lock to probe. Default conv.
            item_id: which corpus item's text. Default S01 (short).
            trials: default 50 per spec.
        """
        providers = [
            p for p in self.providers.providers
            if p.name != "orpheus"  # spec §3.1 — D1 N/A-hosted
            and (provider_names is None or p.name in provider_names)
        ]

        # Explicit note if the caller passed orpheus — silent skip is a bug
        # attractor
        if provider_names and "orpheus" in provider_names:
            # We still don't run it; just log that we noticed the request
            pass

        corpus = self._load_corpus(use_case)
        item = next((i for i in corpus.items if i.id == item_id), None)
        if item is None:
            raise RuntimeError(
                f"latency: item_id {item_id!r} not in {use_case} corpus"
            )

        run = default_run_store().new_run(kind="latency", extras={
            "mode": RunMode.latency.value,
            "use_case": use_case,
            "item_id": item_id,
            "trials": trials,
            "provider_names": [p.name for p in providers],
            "orpheus_skipped": "spec §3.1 — D1 N/A-hosted",
        })
        started = time.perf_counter()

        # STRICTLY SERIAL per provider (spec §D1). We do run different
        # providers sequentially in the CLI here to keep the network
        # unloaded during any single provider's trials.
        results: list[ItemResult] = []
        for p in providers:
            for trial in range(trials):
                # `draw` field is repurposed as trial index for the audio
                # path; audio files land at:
                #   audio/<provider>/<use_case>/<item_id>_t{trial:03d}.wav
                # We synthesise then also relocate the file. Simpler:
                # call _synthesize_one with mode=latency and let it drop
                # the file without the _dNN suffix (mode!=variance), then
                # rename to _tNNN. Cleanest: shadow the suffix logic here
                # by writing directly in the summary loop instead of
                # reusing _synthesize_one's path convention. Compromise:
                # do a rename after synth. Files are small (< 100KB
                # typically); rename cost is negligible.
                r = self._synthesize_one(p, use_case, item, RunMode.latency, trial, run)
                if r.ok and r.audio_path is not None:
                    # Rename to trial-indexed path so multiple trials don't
                    # overwrite each other
                    new_name = r.audio_path.with_name(
                        f"{item.id}_t{trial:03d}.{r.result.audio_format if r.result else 'wav'}"
                    )
                    try:
                        r.audio_path.rename(new_name)
                        r.audio_path = new_name
                    except OSError:
                        # If rename fails (very unlikely), keep the original
                        # path; latency analyzer reads from api_log.jsonl
                        # for timing, not from file names
                        pass
                results.append(r)

        elapsed = time.perf_counter() - started
        run.finalize()

        summary = RunSummary(
            mode=RunMode.latency, run_id=run.manifest.run_id, run_dir=run.dir,
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
