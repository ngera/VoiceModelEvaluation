"""Pair builder — build the per-rater judgment manifest.

Plan v2 line 396: "9 systems (8 providers + anchor) → 36 pairs × 2 use
cases × 3 repetitions = 216 judgments target." Reps reduced from 5 to 3
in D-009 to preserve the original ~2-hour session budget after the
6→8 provider expansion.

Per (system_a, system_b, use_case) we schedule N repetitions, each
using a DIFFERENT corpus item. Items are chosen deterministically per
(a, b, use_case, rep_index) so the rating campaign is reproducible.

Two constraints from R8 (spec §3.4 point 8):
    1. Randomised across sessions rather than blocked by provider —
       inside each session the pair order is shuffled, but the SET of
       pairs is a partition of the full manifest so no pair is skipped.
    2. AB order is coin-flipped per-judgment so the rater can't build
       a "left is usually X" bias.

Both randomizations are seeded from the rater id, so the same rater
sees the same order on a re-run (idempotent re-judge) but different
raters get different orders (avoids shared-order bias if more than
one rater is used in future work).
"""

from __future__ import annotations

import hashlib
import itertools
import random
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from veval.config import CorpusFile, UseCase

REPS_PER_PAIR = 3  # D-009: reduced from spec-original 5 for 8-provider roster
ANCHOR_SYSTEM = "anchor"

Position = Literal["A", "B"]


@dataclass(frozen=True)
class Pair:
    system_a: str
    system_b: str
    use_case: UseCase


@dataclass
class Judgment:
    """One row of the per-rater manifest — everything the UI needs to
    display a blinded A/B comparison and record a winner.
    """

    judgment_id: str
    session_index: int
    use_case: UseCase
    item_id: str
    # Displayed order (already coin-flipped). system_left / system_right
    # are the TRUE identities; the UI shows them as "A" / "B" only.
    system_left: str
    system_right: str
    wav_left: str
    wav_right: str
    is_consistency_repeat: bool = False


@dataclass
class RatingManifest:
    rater_id: str
    seed: int
    total_judgments: int
    total_sessions: int
    reps_per_pair: int
    systems: list[str]
    use_cases: list[str]
    judgments: list[Judgment] = field(default_factory=list)


def enumerate_pairs(systems: Iterable[str], use_cases: Iterable[UseCase]) -> list[Pair]:
    """All C(N,2) system pairs × use cases. Order is deterministic
    (sorted systems, then use-case order given by caller)."""
    sys_sorted = sorted(systems)
    pairs: list[Pair] = []
    for uc in use_cases:
        for a, b in itertools.combinations(sys_sorted, 2):
            pairs.append(Pair(system_a=a, system_b=b, use_case=uc))
    return pairs


def pick_items_for_pair(
    pair: Pair,
    corpus: CorpusFile,
    n_reps: int,
    exclude_probe: bool = True,
) -> list[str]:
    """Deterministic corpus-item selection for a (a, b, use_case) pair.

    Hash of the pair identifier seeds a shuffle over the corpus's
    non-probe items; take the first `n_reps`. Same (a, b, use_case) →
    same items every time; different pairs get different items even
    when reps overlap.

    Probe items (P**) are excluded because they're the
    contamination-detection set — reserving them for D3 keeps the D4
    signal clean of pretraining-set overlaps.
    """
    key = f"{pair.system_a}|{pair.system_b}|{pair.use_case}"
    seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    pool = [
        i.id for i in corpus.items
        if not (exclude_probe and i.stratum == "probe")
    ]
    if len(pool) < n_reps:
        raise ValueError(
            f"Corpus for {pair.use_case} has {len(pool)} non-probe items "
            f"but need {n_reps} for one pair. Increase corpus or lower reps."
        )
    pool_copy = pool[:]  # avoid mutating shared corpus
    rng.shuffle(pool_copy)
    return pool_copy[:n_reps]


def _rater_rng(rater_id: str) -> random.Random:
    seed = int(hashlib.sha256(rater_id.encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def build_manifest(
    rater_id: str,
    systems: list[str],
    use_cases: list[UseCase],
    corpora: dict[UseCase, CorpusFile],
    audio_root: Path,
    reps_per_pair: int = REPS_PER_PAIR,
    session_size: int = 40,
    consistency_repeat_fraction: float = 0.10,
    restrict_to_items: set[str] | None = None,
) -> RatingManifest:
    """Build the full per-rater manifest.

    Steps:
        1. Enumerate all (system_a, system_b, use_case) pairs.
        2. For each pair, deterministically pick `reps_per_pair` items.
        3. For each (pair, item) → coin-flip which system is on the left.
        4. Shuffle the full judgment list per rater (R8 randomization).
        5. Insert a 10% consistency-repeat suffix (drawn from the
           already-scheduled set, re-shuffled) marked with
           `is_consistency_repeat=True`.
        6. Split into sessions of `session_size`.

    audio_root/{use_case}/{system}/{item_id}.wav is expected to exist
    for every scheduled judgment; the pair-builder does NOT check
    (that's the rating page's responsibility on load) so the manifest
    can be built without loudness-normalization having run first.
    """
    if reps_per_pair < 1:
        raise ValueError("reps_per_pair must be >= 1")

    pairs = enumerate_pairs(systems, use_cases)
    rng = _rater_rng(rater_id)

    # Step 1-3: build the base judgment set
    base: list[Judgment] = []
    for pair in pairs:
        corpus = corpora[pair.use_case]
        if restrict_to_items:
            # Filter corpus down to items the caller has audio for.
            # Preserves the deterministic-per-pair selection over the
            # restricted pool.
            filtered = CorpusFile(
                use_case=corpus.use_case,
                items=[i for i in corpus.items if i.id in restrict_to_items],
            )
            items = pick_items_for_pair(pair, filtered, reps_per_pair)
        else:
            items = pick_items_for_pair(pair, corpus, reps_per_pair)
        for rep_idx, item_id in enumerate(items):
            left_is_a = rng.random() < 0.5
            left = pair.system_a if left_is_a else pair.system_b
            right = pair.system_b if left_is_a else pair.system_a
            base.append(Judgment(
                judgment_id=(
                    f"{pair.system_a}__{pair.system_b}__{pair.use_case}__{item_id}__r{rep_idx}"
                ),
                session_index=0,  # assigned in step 6
                use_case=pair.use_case,
                item_id=item_id,
                system_left=left,
                system_right=right,
                wav_left=_audio_relpath(audio_root, pair.use_case, left, item_id),
                wav_right=_audio_relpath(audio_root, pair.use_case, right, item_id),
            ))

    # Step 4: shuffle across pairs (R8)
    rng.shuffle(base)

    # Step 5: consistency repeats (10% by default), taken from the same
    # base set and marked. Coin-flip re-happens so left/right can
    # differ from the first showing. Fraction=0 means skip entirely
    # (used by tests + the "fresh campaign, no re-judge planned" path).
    if consistency_repeat_fraction > 0:
        n_consistency = max(1, int(round(len(base) * consistency_repeat_fraction)))
    else:
        n_consistency = 0
    repeats_source = base[:]  # copy so we can shuffle independently
    rng.shuffle(repeats_source)
    repeats: list[Judgment] = []
    for j in repeats_source[:n_consistency]:
        # Re-flip left/right so the rater can't rely on visual memory
        flip = rng.random() < 0.5
        left = j.system_right if flip else j.system_left
        right = j.system_left if flip else j.system_right
        repeats.append(Judgment(
            judgment_id=j.judgment_id + "__repeat",
            session_index=0,  # assigned in step 6
            use_case=j.use_case,
            item_id=j.item_id,
            system_left=left,
            system_right=right,
            wav_left=(j.wav_right if flip else j.wav_left),
            wav_right=(j.wav_left if flip else j.wav_right),
            is_consistency_repeat=True,
        ))
    all_judgments = base + repeats

    # Step 6: session assignment. Consistency repeats live in the LAST
    # session so they're at least `session_size` steps away from the
    # original showing (the spec asks for ≥1 week; the session_index
    # is the closest proxy the manifest can enforce).
    for i, j in enumerate(all_judgments):
        j.session_index = i // session_size

    total_sessions = (
        (len(all_judgments) + session_size - 1) // session_size if all_judgments else 0
    )

    return RatingManifest(
        rater_id=rater_id,
        seed=int(hashlib.sha256(rater_id.encode()).hexdigest()[:8], 16),
        total_judgments=len(all_judgments),
        total_sessions=total_sessions,
        reps_per_pair=reps_per_pair,
        systems=sorted(systems),
        use_cases=list(use_cases),
        judgments=all_judgments,
    )


def _audio_relpath(root: Path, use_case: str, system: str, item_id: str) -> str:
    """Path relative to `root` — the rating page loads audio from a
    local directory rooted at itself, so relative paths are what the
    manifest needs to record."""
    return str(Path(root.name) / use_case / system / f"{item_id}.wav").replace("\\", "/")


def write_manifest(manifest: RatingManifest, path: Path) -> None:
    """Write manifest to JSON. Fields are dataclass-flat, easy to load
    from the static HTML rating page via `fetch()`."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **{k: v for k, v in asdict(manifest).items() if k != "judgments"},
        "judgments": [asdict(j) for j in manifest.judgments],
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
