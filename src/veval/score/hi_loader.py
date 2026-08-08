"""Humanness Index snapshot loader.

Spec Sec 5: "HI snapshot loader (hand-scraped JSON) -> Delta and
'Reproduces?' columns." HI is a public leaderboard (ArtificialAnalysis.ai
et al.); we hand-scrape a snapshot at analysis time so the comparison is
against a frozen point in time (the leaderboard moves).

Snapshot format (`configs/hi_snapshot.json`):
    {
      "captured_at": "2026-08-08",
      "source": "https://...",
      "scores": {
        "openai":     {"rank": 3, "score": 91.5},
        "cartesia":   {"rank": 5, "score": 88.2},
        ...
      },
      "notes": "..."
    }

"Reproduces?" is a coarse yes/no from comparing our BT rank to HI's:
    - YES: ours and HI put the same 3 providers at top-3 in the same
      order (allowing 1 swap).
    - MOSTLY: same top-3 set, different order.
    - NO: different top-3 set.

The interesting story is where our data diverges from HI. This module
just loads and diffs; the report layer writes the narrative.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class HISnapshot:
    captured_at: str
    source: str
    scores: dict[str, dict[str, float]]  # provider -> {rank, score}
    notes: str = ""


@dataclass
class HIComparison:
    hi_rank: int | None
    our_rank: int | None
    hi_score: float | None
    our_strength: float | None
    delta_rank: int | None  # our_rank - hi_rank; positive = we ranked lower
    reproduces: str  # "yes" | "mostly" | "no" | "unknown"


def load_snapshot(path: Path) -> HISnapshot:
    if not path.exists():
        raise FileNotFoundError(f"HI snapshot not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return HISnapshot(
        captured_at=data["captured_at"],
        source=data["source"],
        scores=data["scores"],
        notes=data.get("notes", ""),
    )


def _classify_top3(hi_top3: list[str], our_top3: list[str]) -> str:
    hi_set = set(hi_top3)
    our_set = set(our_top3)
    if hi_top3 == our_top3:
        return "yes"
    if hi_set == our_set:
        return "mostly"  # same 3, different order
    # "yes" also allowed for a 1-swap edit distance
    diff_count = sum(
        1 for a, b in zip(hi_top3, our_top3, strict=False) if a != b
    )
    if diff_count <= 1 and hi_set == our_set:
        return "yes"
    return "no"


def compare(
    snapshot: HISnapshot,
    our_strengths: dict[str, float],
) -> dict[str, HIComparison]:
    """Return {provider: HIComparison} for the union of providers.

    `our_strengths` is a flat provider -> BT strength dict from a
    single BTFit's (systems, strengths). Cross-use-case comparison is
    the caller's decision (HI is single-index so per-use-case
    comparison requires picking one; convention: conversational).
    """
    # Our ranking (higher strength = better rank)
    our_sorted = sorted(our_strengths.items(), key=lambda kv: -kv[1])
    our_rank_map = {p: i + 1 for i, (p, _) in enumerate(our_sorted)}
    our_top3 = [p for p, _ in our_sorted[:3] if p != "anchor"][:3]

    # HI ranking - lower rank number = better
    hi_sorted = sorted(
        snapshot.scores.items(), key=lambda kv: kv[1].get("rank", 999),
    )
    hi_top3 = [p for p, _ in hi_sorted[:3]]

    reproduces = _classify_top3(hi_top3, our_top3)

    out: dict[str, HIComparison] = {}
    all_providers = set(snapshot.scores) | set(our_strengths)
    for provider in sorted(all_providers):
        hi_entry = snapshot.scores.get(provider, {})
        hi_rank = hi_entry.get("rank")
        hi_score = hi_entry.get("score")
        our_rank = our_rank_map.get(provider)
        out[provider] = HIComparison(
            hi_rank=int(hi_rank) if hi_rank is not None else None,
            our_rank=our_rank,
            hi_score=float(hi_score) if hi_score is not None else None,
            our_strength=our_strengths.get(provider),
            delta_rank=(
                (our_rank - int(hi_rank)) if our_rank and hi_rank is not None else None
            ),
            reproduces=reproduces if provider in set(hi_top3) | set(our_top3) else "unknown",
        )
    return out


def as_dicts(comparisons: dict[str, HIComparison]) -> dict[str, dict[str, Any]]:
    return {p: asdict(c) for p, c in comparisons.items()}
