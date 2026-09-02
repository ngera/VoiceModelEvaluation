"""Render human-readable results from the experiment pack drift.json.

Emits Markdown to stdout suitable for the EXPERIMENTS_2026-09-01.md report.
"""

from __future__ import annotations

import json
from pathlib import Path

DRIFT = Path("analysis/experiments-2026-09-01/drift.json")


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _fade(row: dict, threshold_db: float = 2.0) -> bool:
    d = row.get("delta_t1_t3")
    m = row.get("monotonic_decreasing")
    return bool(d is not None and d >= threshold_db and m)


def _classify(row: dict) -> str:
    d = row.get("delta_t1_t3")
    m = row.get("monotonic_decreasing")
    if d is None:
        return "no-data"
    if _fade(row):
        return "FADE"
    if m:
        return f"mono-decr (small)"
    if d >= 2.0:
        return f"large delta (non-mono)"
    return "no fade"


def main():
    doc = json.loads(DRIFT.read_text(encoding="utf-8"))
    items = doc["items"]

    a = sorted([x for x in items if "A_new_items" in x["wav"]], key=lambda r: r["wav"])
    b = sorted([x for x in items if "B_voices" in x["wav"]], key=lambda r: r["wav"])
    c = sorted([x for x in items if "C_halves" in x["wav"]], key=lambda r: r["wav"])
    e = sorted([x for x in items if "E_altvoice" in x["wav"]], key=lambda r: r["wav"])

    # ================= A =================
    print("## Experiment A — 20 new items on ElevenLabs pinned narration voice\n")
    print("| item | topic | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ (t1−t3) | monotonic? | classification |")
    print("|---|---|---:|---:|---:|---:|---:|---|---|")
    a_fades = 0
    a_mono = 0
    per_topic_fade = {"TECH": 0, "WARM": 0, "FACT": 0, "EMOT": 0}
    per_topic_total = {"TECH": 0, "WARM": 0, "FACT": 0, "EMOT": 0}
    for x in a:
        label = _norm(x["wav"]).split("/")[-1].replace(".wav", "")
        topic = label[:4]  # TECH, WARM, FACT, EMOT
        per_topic_total[topic] = per_topic_total.get(topic, 0) + 1
        cls = _classify(x)
        fade = _fade(x)
        if fade:
            a_fades += 1
            per_topic_fade[topic] = per_topic_fade.get(topic, 0) + 1
        if x.get("monotonic_decreasing"):
            a_mono += 1
        print(f"| {label} | {topic} | {x['duration_s']:.1f}s | {x['lufs_t1']:+.2f} | {x['lufs_t2']:+.2f} | {x['lufs_t3']:+.2f} | {x.get('delta_t1_t3'):+.2f} | {x.get('monotonic_decreasing')} | {cls} |")
    print(f"\n**A totals**: {a_fades} / 20 items fade (Δ ≥ 2 dB AND monotonically decreasing across thirds). {a_mono} / 20 monotonic decreasing (any magnitude).")
    print(f"\n**Per topic (fade / total)**:")
    for topic in ["TECH", "WARM", "FACT", "EMOT"]:
        print(f"- {topic}: {per_topic_fade[topic]} / {per_topic_total[topic]}")
    print()

    # ================= B =================
    print("## Experiment B — L03 on 5 different ElevenLabs voices\n")
    print("| voice | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ (t1−t3) | monotonic? | classification |")
    print("|---|---:|---:|---:|---:|---:|---|---|")
    b_fades = 0
    for x in b:
        voice = _norm(x["wav"]).split("/")[-1].replace(".wav", "")
        cls = _classify(x)
        if _fade(x):
            b_fades += 1
        print(f"| {voice} | {x['duration_s']:.1f}s | {x['lufs_t1']:+.2f} | {x['lufs_t2']:+.2f} | {x['lufs_t3']:+.2f} | {x.get('delta_t1_t3'):+.2f} | {x.get('monotonic_decreasing')} | {cls} |")
    print(f"\n**B totals**: {b_fades} / 5 voices fade on L03.")
    print()

    # ================= C =================
    print("## Experiment C — L03 split into halves\n")
    print("| segment | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ (t1−t3) | monotonic? | classification |")
    print("|---|---:|---:|---:|---:|---:|---|---|")
    for x in c:
        label = _norm(x["wav"]).split("/")[-1].replace(".wav", "")
        cls = _classify(x)
        print(f"| {label} | {x['duration_s']:.1f}s | {x['lufs_t1']:+.2f} | {x['lufs_t2']:+.2f} | {x['lufs_t3']:+.2f} | {x.get('delta_t1_t3'):+.2f} | {x.get('monotonic_decreasing')} | {cls} |")
    print()

    # ================= E =================
    print("## Experiment E — alt-voice sweep (drift stats for reference; full T6-style needs quality/wer analyzers)\n")
    print("| vendor | item | duration | t1 LUFS | t2 LUFS | t3 LUFS | Δ | mono? |")
    print("|---|---|---:|---:|---:|---:|---:|---|")
    for x in e:
        parts = _norm(x["wav"]).split("/")
        vendor = parts[-2] if len(parts) >= 2 else "?"
        item = parts[-1].replace(".wav", "")
        print(f"| {vendor} | {item} | {x['duration_s']:.1f}s | {x['lufs_t1']:+.2f} | {x['lufs_t2']:+.2f} | {x['lufs_t3']:+.2f} | {x.get('delta_t1_t3'):+.2f} | {x.get('monotonic_decreasing')} |")


if __name__ == "__main__":
    main()
