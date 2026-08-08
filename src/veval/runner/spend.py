"""Spend cap tracker.

Phase D.5. Safety net so an accidental full-campaign run against a
provider you forgot to sanity-check doesn't burn the budget.

Semantics:
  - Cost estimate is CONSERVATIVE: assumes paid-tier pricing even when
    a free monthly allowance is available. Overestimates spend rather
    than underestimating it. Better to trip the cap slightly early
    than to skip it and blow the ceiling.
  - Per-provider running total in USD.
  - Warn at `warn_fraction` (default 0.80).
  - Abort at 1.0 — subsequent calls to `charge()` raise SpendCapExceeded.
    In-flight synthesis calls (already submitted to the threadpool)
    complete; nothing new starts.
  - Env override: VEVAL_SPEND_CAP_USD (default 100.0).
  - CLI override: --spend-cap 25.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Literal

from veval.config import PricingCell, PricingFile


class SpendCapExceeded(RuntimeError):
    """Raised by `SpendTracker.charge()` when the cap has been reached."""


BillingUnit = Literal["characters", "bytes", "generation", "tokens", "seconds"]


@dataclass
class SpendTracker:
    """Threadsafe tracker: incremental per-call charge + cumulative check.

    Rate lookup happens once at init from the pricing.yaml PricingFile.
    Providers with multiple pricing rows (Fish free vs paid, Google free
    vs paid, ElevenLabs Flash vs Multilingual) — the tracker picks the
    MOST EXPENSIVE row per unit-type by default so the estimate errs on
    the side of caution.
    """

    cap_usd: float
    pricing: PricingFile
    warn_fraction: float = 0.80
    per_provider_usd: dict[str, float] = field(default_factory=dict)
    warned: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def from_env(cls, pricing: PricingFile, cap_usd_override: float | None = None) -> SpendTracker:
        env_cap = os.environ.get("VEVAL_SPEND_CAP_USD")
        if cap_usd_override is not None:
            cap = cap_usd_override
        elif env_cap:
            try:
                cap = float(env_cap)
            except ValueError:
                cap = 100.0
        else:
            cap = 100.0
        return cls(cap_usd=cap, pricing=pricing)

    def _pick_rate(self, provider: str, billing_unit: BillingUnit) -> PricingCell | None:
        """Return the most-conservative (highest-rate) row matching this unit."""
        rows = self.pricing.for_provider(provider)
        if billing_unit == "characters":
            candidates = [r for r in rows if r.unit == "per_1M_chars"]
        elif billing_unit == "bytes":
            candidates = [r for r in rows if r.unit == "per_1M_bytes"]
        elif billing_unit == "generation":
            candidates = [r for r in rows if r.unit == "per_generation"]
        elif billing_unit == "tokens":
            candidates = [r for r in rows if r.unit == "per_1M_tokens"]
        elif billing_unit == "seconds":
            candidates = [r for r in rows if r.unit == "per_1M_seconds"]
        else:
            candidates = []
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.rate_usd)

    def estimate_cost(
        self,
        provider: str,
        billing_unit: BillingUnit,
        billed_units: int,
    ) -> float:
        """Estimate USD cost of a single call. Returns 0.0 if no matching
        pricing row (unknown = free, but this only happens if pricing.yaml
        is stale for a provider)."""
        cell = self._pick_rate(provider, billing_unit)
        if cell is None:
            return 0.0
        rate = cell.rate_usd
        if cell.unit in ("per_1M_chars", "per_1M_bytes", "per_1M_tokens", "per_1M_seconds"):
            return billed_units / 1_000_000 * rate
        if cell.unit == "per_generation":
            return rate
        return 0.0

    def charge(
        self,
        provider: str,
        billing_unit: BillingUnit,
        billed_units: int,
    ) -> tuple[float, float]:
        """Record a charge; return (this_call_usd, running_total_usd).

        Raises SpendCapExceeded if the projected total after this charge
        would exceed self.cap_usd — caller MUST not perform the API
        call in that case. Call estimate_cost() BEFORE the API call
        and gate on the return.
        """
        this_call = self.estimate_cost(provider, billing_unit, billed_units)
        with self._lock:
            new_total = sum(self.per_provider_usd.values()) + this_call
            if new_total > self.cap_usd:
                raise SpendCapExceeded(
                    f"Spend cap ${self.cap_usd:.2f} exceeded: "
                    f"running ${sum(self.per_provider_usd.values()):.2f} + "
                    f"this call ${this_call:.2f} for {provider} would total "
                    f"${new_total:.2f}"
                )
            self.per_provider_usd[provider] = (
                self.per_provider_usd.get(provider, 0.0) + this_call
            )
            total = sum(self.per_provider_usd.values())
        return this_call, total

    @property
    def total_usd(self) -> float:
        with self._lock:
            return sum(self.per_provider_usd.values())

    def should_warn(self) -> bool:
        """True when running total crosses warn_fraction × cap. Idempotent:
        returns True only on the first crossing to avoid spamming."""
        with self._lock:
            total = sum(self.per_provider_usd.values())
            if not self.warned and total >= self.warn_fraction * self.cap_usd:
                self.warned = True
                return True
            return False
