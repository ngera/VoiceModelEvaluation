"""Regression tests for human/pair_builder.py.

Reproducibility is load-bearing: same rater_id must give the same
manifest across re-runs (idempotent re-judge). Different raters must
diverge (avoid shared-order bias). Consistency repeats must be marked
and land in a later session than the original.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from veval.config import CorpusFile, CorpusItem, UseCase
from veval.human.pair_builder import (
    ANCHOR_SYSTEM,
    REPS_PER_PAIR,
    build_manifest,
    enumerate_pairs,
    pick_items_for_pair,
    Pair,
    write_manifest,
)


def _fake_corpus(use_case: UseCase, n_items: int = 20) -> CorpusFile:
    """20 novel items + 5 probes so pick_items has a real pool."""
    items = []
    for i in range(n_items):
        text = f"item {use_case} number {i:03d} words placeholder"
        items.append(CorpusItem(
            id=f"S{i:02d}", stratum="short", text=text,
            word_count=len(text.split()),
        ))
    for i in range(5):
        text = f"probe {use_case} item {i:03d} for test"
        items.append(CorpusItem(
            id=f"P{i:02d}", stratum="probe", text=text,
            word_count=len(text.split()),
        ))
    return CorpusFile(use_case=use_case, items=items)


def test_reps_per_pair_default_is_three() -> None:
    """D-009: default reduced from 5 to 3 for the expanded 8-provider
    roster. Changing silently breaks the receipt in prereg-v1.7."""
    assert REPS_PER_PAIR == 3


def test_enumerate_pairs_yields_c_n_2_times_use_cases() -> None:
    systems = ["a", "b", "c", "d"]  # 4 systems → C(4,2) = 6 pairs
    pairs = enumerate_pairs(systems, ["conversational", "narration"])
    assert len(pairs) == 6 * 2
    # Each pair is (a,b) with a < b lexically (canonicalisation)
    for p in pairs:
        assert p.system_a < p.system_b


def test_pick_items_deterministic_across_runs() -> None:
    corpus = _fake_corpus("conversational")
    pair = Pair("openai", "cartesia", "conversational")
    a = pick_items_for_pair(pair, corpus, n_reps=3)
    b = pick_items_for_pair(pair, corpus, n_reps=3)
    assert a == b


def test_pick_items_excludes_probe_stratum_by_default() -> None:
    corpus = _fake_corpus("narration")
    pair = Pair("openai", "cartesia", "narration")
    picks = pick_items_for_pair(pair, corpus, n_reps=5)
    assert not any(iid.startswith("P") for iid in picks)


def test_pick_items_raises_when_pool_too_small() -> None:
    tiny = CorpusFile(
        use_case="conversational",
        items=[CorpusItem(id=f"S{i:02d}", stratum="short",
                          text=f"item {i:03d} placeholder", word_count=3)
               for i in range(2)],
    )
    with pytest.raises(ValueError, match="but need 3"):
        pick_items_for_pair(Pair("a", "b", "conversational"), tiny, n_reps=3)


def test_build_manifest_reproducible_per_rater(tmp_path: Path) -> None:
    corpora = {"conversational": _fake_corpus("conversational"),
               "narration": _fake_corpus("narration")}
    systems = ["openai", "cartesia", "elevenlabs", ANCHOR_SYSTEM]
    m1 = build_manifest(
        rater_id="njg", systems=systems, use_cases=["conversational"],
        corpora=corpora, audio_root=Path("rating/audio"),
    )
    m2 = build_manifest(
        rater_id="njg", systems=systems, use_cases=["conversational"],
        corpora=corpora, audio_root=Path("rating/audio"),
    )
    assert [j.judgment_id for j in m1.judgments] == [j.judgment_id for j in m2.judgments]
    assert [j.system_left for j in m1.judgments] == [j.system_left for j in m2.judgments]


def test_build_manifest_diverges_per_rater() -> None:
    corpora = {"conversational": _fake_corpus("conversational")}
    systems = ["openai", "cartesia", "elevenlabs", ANCHOR_SYSTEM]
    # consistency_repeat_fraction=0 so the non-repeat sets are identical
    # by construction and only the order can differ.
    m1 = build_manifest("njg", systems, ["conversational"], corpora,
                        audio_root=Path("rating/audio"),
                        consistency_repeat_fraction=0.0)
    m2 = build_manifest("other-rater", systems, ["conversational"], corpora,
                        audio_root=Path("rating/audio"),
                        consistency_repeat_fraction=0.0)
    ids_1 = [j.judgment_id for j in m1.judgments]
    ids_2 = [j.judgment_id for j in m2.judgments]
    assert sorted(ids_1) == sorted(ids_2)  # same underlying pair set
    assert ids_1 != ids_2                  # different presentation order


def test_build_manifest_216_judgments_for_9_systems_2_use_cases_3_reps() -> None:
    """D-009 headline number: 216 judgments for the 8-provider roster."""
    corpora = {"conversational": _fake_corpus("conversational"),
               "narration": _fake_corpus("narration")}
    systems = [f"prov{i}" for i in range(8)] + [ANCHOR_SYSTEM]  # 9 systems
    m = build_manifest("njg", systems, ["conversational", "narration"],
                       corpora, audio_root=Path("rating/audio"),
                       reps_per_pair=3, consistency_repeat_fraction=0.0)
    assert m.total_judgments == 9 * 8 // 2 * 2 * 3  # C(9,2) × 2 × 3 = 216


def test_build_manifest_marks_consistency_repeats() -> None:
    corpora = {"conversational": _fake_corpus("conversational")}
    systems = ["a", "b", "c", "d"]  # 6 pairs × 1 UC × 3 reps = 18 base
    m = build_manifest("njg", systems, ["conversational"], corpora,
                       audio_root=Path("rating/audio"),
                       consistency_repeat_fraction=0.10)
    repeats = [j for j in m.judgments if j.is_consistency_repeat]
    non_repeats = [j for j in m.judgments if not j.is_consistency_repeat]
    assert len(non_repeats) == 18
    # 10% of 18 → 2 repeats (max(1, round(1.8)) = 2)
    assert len(repeats) == 2
    # Consistency repeats live in the LAST session
    max_session = max(j.session_index for j in m.judgments)
    for r in repeats:
        assert r.session_index == max_session


def test_write_manifest_round_trips_json(tmp_path: Path) -> None:
    import json

    corpora = {"conversational": _fake_corpus("conversational")}
    m = build_manifest("njg", ["a", "b", "c"], ["conversational"], corpora,
                       audio_root=Path("rating/audio"))
    p = tmp_path / "manifest.json"
    write_manifest(m, p)
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["rater_id"] == "njg"
    assert data["total_judgments"] == len(m.judgments)
    assert len(data["judgments"]) == len(m.judgments)


def test_audio_relpaths_use_forward_slashes(tmp_path: Path) -> None:
    """The rating page reads paths in a browser context — Windows
    backslashes would break the fetch(). Paths must use `/`."""
    corpora = {"conversational": _fake_corpus("conversational")}
    m = build_manifest("njg", ["a", "b"], ["conversational"], corpora,
                       audio_root=Path("rating/audio"))
    for j in m.judgments:
        assert "\\" not in j.wav_left
        assert "\\" not in j.wav_right
