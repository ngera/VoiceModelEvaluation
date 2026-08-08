"""SpendTracker regression tests.

Invariants:
  - Conservative estimate: picks the highest-rate row when a provider
    has multiple pricing entries (e.g. Fish free vs paid; ElevenLabs
    Flash vs Multilingual).
  - Threadsafe (multiple charges from parallel provider work).
  - Raises SpendCapExceeded BEFORE recording, so a call that would
    trip the cap is refused.
  - warn_fraction crossing fires exactly once.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from veval.config import PricingFile, load_pricing
from veval.runner.spend import SpendCapExceeded, SpendTracker


@pytest.fixture
def pricing() -> PricingFile:
    return load_pricing(Path("configs/pricing.yaml"))


def test_estimate_cost_char_billed_provider(pricing: PricingFile) -> None:
    # Deepgram is $30/1M chars — 5000 chars = $0.15
    tracker = SpendTracker(cap_usd=100.0, pricing=pricing)
    cost = tracker.estimate_cost("deepgram", "characters", 5000)
    assert cost == pytest.approx(0.15, rel=1e-4)


def test_estimate_cost_picks_highest_rate_for_multi_row_providers(pricing: PricingFile) -> None:
    """ElevenLabs has both Flash ($50/1M) and Multilingual ($100/1M) rows.
    Conservative estimate uses the higher rate ($100)."""
    tracker = SpendTracker(cap_usd=100.0, pricing=pricing)
    cost = tracker.estimate_cost("elevenlabs", "characters", 1_000_000)
    assert cost == pytest.approx(100.0, rel=1e-4)


def test_estimate_cost_per_generation_provider(pricing: PricingFile) -> None:
    # Orpheus is $0.003/generation
    tracker = SpendTracker(cap_usd=100.0, pricing=pricing)
    cost = tracker.estimate_cost("orpheus", "generation", 1)
    assert cost == pytest.approx(0.003, rel=1e-4)


def test_estimate_cost_bytes_billed_provider(pricing: PricingFile) -> None:
    # Fish paid is $15/1M bytes — 5000 bytes = $0.075
    tracker = SpendTracker(cap_usd=100.0, pricing=pricing)
    cost = tracker.estimate_cost("fish", "bytes", 5000)
    assert cost == pytest.approx(0.075, rel=1e-4)


def test_charge_accumulates(pricing: PricingFile) -> None:
    tracker = SpendTracker(cap_usd=100.0, pricing=pricing)
    tracker.charge("deepgram", "characters", 5000)
    tracker.charge("deepgram", "characters", 5000)
    assert tracker.per_provider_usd["deepgram"] == pytest.approx(0.30, rel=1e-4)


def test_charge_raises_when_cap_would_be_exceeded(pricing: PricingFile) -> None:
    # Cap of $0.01. First tiny call is fine; big call trips.
    tracker = SpendTracker(cap_usd=0.01, pricing=pricing)
    tracker.charge("deepgram", "characters", 100)  # $0.003 — under cap
    with pytest.raises(SpendCapExceeded):
        tracker.charge("elevenlabs", "characters", 10_000)  # $1.00 — would trip


def test_should_warn_fires_once_at_threshold(pricing: PricingFile) -> None:
    tracker = SpendTracker(cap_usd=1.00, pricing=pricing, warn_fraction=0.80)
    tracker.charge("deepgram", "characters", 20_000)  # $0.60 — below 80%
    assert not tracker.should_warn()
    tracker.charge("deepgram", "characters", 10_000)  # $0.30 → total $0.90, above 80%
    assert tracker.should_warn()
    assert not tracker.should_warn()  # idempotent


def test_from_env_falls_back_to_default_when_env_unset(pricing: PricingFile, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VEVAL_SPEND_CAP_USD", raising=False)
    tracker = SpendTracker.from_env(pricing=pricing)
    assert tracker.cap_usd == 100.0


def test_from_env_reads_env_var(pricing: PricingFile, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEVAL_SPEND_CAP_USD", "25.5")
    tracker = SpendTracker.from_env(pricing=pricing)
    assert tracker.cap_usd == 25.5


def test_from_env_cli_override_wins(pricing: PricingFile, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEVAL_SPEND_CAP_USD", "25.5")
    tracker = SpendTracker.from_env(pricing=pricing, cap_usd_override=10.0)
    assert tracker.cap_usd == 10.0
