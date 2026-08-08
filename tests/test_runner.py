"""Runner regression tests.

Covers the low-risk stuff that doesn't need live API calls:
  - Voice/model resolution (split-model providers use quality_model in
    campaign/variance modes, latency mode uses paid model)
  - Variance mode raises loudly if variance_subset.yaml references items
    not in the corpus
  - Concurrency default map has entries for every registered provider

Live-API-touching behaviour is validated by `veval doctor` + the $1
pilot (D.7). Nothing here talks to a real provider.
"""

from __future__ import annotations

from pathlib import Path

from veval.adapters import ADAPTERS
from veval.runner import Runner, RunMode
from veval.runner.runner import DEFAULT_PROVIDER_CONCURRENCY


def test_runner_loads_shipped_configs() -> None:
    r = Runner()
    assert len(r.providers.providers) == 8
    assert len(r.voices.voices) == 16
    assert r.cache is None  # default: no cache


def test_split_model_provider_campaign_uses_quality_model() -> None:
    """Fish: campaign/variance → free tier (quality_model); latency → paid."""
    r = Runner()
    v, m = r._resolve_voice_model("fish", "conversational", RunMode.campaign)
    assert m == "s2.1-pro-free"
    v, m = r._resolve_voice_model("fish", "conversational", RunMode.variance)
    assert m == "s2.1-pro-free"
    v, m = r._resolve_voice_model("fish", "conversational", RunMode.latency)
    assert m == "s2.1-pro"


def test_non_split_provider_uses_same_model_regardless_of_mode() -> None:
    r = Runner()
    for mode in (RunMode.campaign, RunMode.variance, RunMode.latency):
        v, m = r._resolve_voice_model("deepgram", "conversational", mode)
        assert m == "aura-2-thalia-en"


def test_provider_concurrency_defaults_cover_every_registered_adapter() -> None:
    """If a new provider is registered without a concurrency default, the
    runner falls back to 3 — that's OK but flag when it happens so we
    don't accidentally rate-limit ourselves."""
    for name in ADAPTERS:
        assert name in DEFAULT_PROVIDER_CONCURRENCY, (
            f"Provider {name} missing from DEFAULT_PROVIDER_CONCURRENCY; "
            f"runner will use fallback of 3 (see runner.py)"
        )


def test_variance_subset_items_all_exist_in_corpus() -> None:
    """Loud failure guarantee: if variance_subset.yaml references an
    item ID not present in the corpus file, the runner refuses to
    start rather than silently produce fewer files than expected."""
    from veval.config import load_corpus, load_variance_subset

    subsets = load_variance_subset(Path("corpus/variance_subset.yaml"))
    for uc in ("conversational", "narration"):
        corpus = load_corpus(Path(f"corpus/{uc}.yaml"))
        corpus_ids = {i.id for i in corpus.items}
        subset_ids = subsets.item_ids_for(uc)  # type: ignore[arg-type]
        missing = [iid for iid in subset_ids if iid not in corpus_ids]
        assert not missing, f"variance subset for {uc} references missing items: {missing}"
        assert len(subset_ids) == 10, f"expected 10 items for {uc}, got {len(subset_ids)}"
