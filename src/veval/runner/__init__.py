"""Runner — orchestrates provider adapter calls across the corpus.

Phase D module. Called by `veval generate`.

Three modes:
  campaign: 75 items × 2 use cases × 8 providers = 1200 files (D.1)
  variance: 10 items × 3 draws × 8 providers × 2 use cases = 480 gens (D.3)
  latency:  50 serial trials per provider from pinned VM (D.4)
"""

from veval.runner.cache import CacheEntry, SynthesisCache
from veval.runner.runner import (
    ItemResult,
    RunMode,
    Runner,
    RunSummary,
)
from veval.runner.spend import SpendCapExceeded, SpendTracker

__all__ = [
    "CacheEntry",
    "ItemResult",
    "RunMode",
    "Runner",
    "RunSummary",
    "SpendCapExceeded",
    "SpendTracker",
    "SynthesisCache",
]
