"""Write the full anchor-recording script to `rating/anchor_script.md`.

150 items (75 conversational + 75 narration) with word counts and
estimated read-time-at-150-wpm. Print or view alongside the mic.
"""

from __future__ import annotations

import sys
from pathlib import Path

from veval.config import load_corpus


WPM = 150  # target read pace


def _est_seconds(word_count: int) -> str:
    seconds = word_count / (WPM / 60.0)
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds // 60
    remainder = seconds - minutes * 60
    return f"{int(minutes)}m {int(remainder):02d}s"


def main() -> int:
    out = Path("rating/anchor_script.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Anchor recording script",
        "",
        f"150 items across two use cases. Target pace **~{WPM} words/minute**.",
        "",
        "Save each recording as `rating/anchor/<use_case>_<item_id>.wav`. "
        "Any format soundfile can decode is fine (WAV, FLAC, MP3) — the "
        "`veval rate normalize` step will convert to −18 LUFS mono WAV.",
        "",
        "Suggested session structure:",
        "- Session 1 (~30 min): all conversational shorts (S**) + jargon (J**) + edge (E**)",
        "- Session 2 (~30 min): all conversational mediums (M**) + longs (L**) + probes (P**)",
        "- Session 3 (~30 min): same for narration shorts / jargon / edge",
        "- Session 4 (~30 min): narration mediums / longs / probes",
        "",
        "Break the recording sequence any way you like — the pair-builder "
        "doesn't care about recording order, only per-file naming.",
        "",
    ]

    total_words = 0
    total_items = 0
    for use_case in ("conversational", "narration"):
        corpus_path = Path(f"corpus/{use_case}.yaml")
        if not corpus_path.exists():
            print(f"skipping missing corpus: {corpus_path}", file=sys.stderr)
            continue
        corpus = load_corpus(corpus_path)
        uc_words = sum(i.word_count for i in corpus.items)
        uc_time = _est_seconds(uc_words)
        lines.append(f"## {use_case} — {len(corpus.items)} items · {uc_words} words · ~{uc_time} of speech")
        lines.append("")
        for item in corpus.items:
            est = _est_seconds(item.word_count)
            lines.append(
                f"### `{item.id}` — {item.word_count} words · ~{est} · "
                f"save as `rating/anchor/{use_case}_{item.id}.wav`"
            )
            lines.append("")
            lines.append(f"> {item.text}")
            lines.append("")
        total_words += uc_words
        total_items += len(corpus.items)

    lines.insert(3, f"**Total: {total_items} items · {total_words} words · "
                    f"~{_est_seconds(total_words)} of pure speech**")
    lines.insert(4, "")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} — {total_items} items, {total_words} words, "
          f"~{_est_seconds(total_words)} of speech")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
