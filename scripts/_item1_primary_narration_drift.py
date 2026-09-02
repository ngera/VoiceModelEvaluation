"""Item 1: run drift analyzer on primary-campaign narration L01..L08
for all 8 vendors' pinned voices. Uses R3 campaign audio (no new API calls)."""

from __future__ import annotations

import json
import wave
from collections import defaultdict
from pathlib import Path

import numpy as np

R3 = Path("runs/campaign-20260831T175358Z/audio")
OUT = Path("analysis/experiments-2026-09-01/item1_primary_narration_drift.json")

FADE_THRESHOLD_DB = 2.0


def _lufs(samples: np.ndarray, sr: int) -> float | None:
    try:
        import pyloudnorm as pyln
    except ImportError:
        return None
    if len(samples) < sr * 0.4:
        return None
    try:
        meter = pyln.Meter(sr)
        return float(meter.integrated_loudness(samples.astype(np.float64)))
    except Exception:
        return None


def _thirds(wav: Path) -> dict:
    with wave.open(str(wav), "rb") as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
        nch = w.getnchannels()
    s = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if nch > 1:
        s = s.reshape(-1, nch).mean(axis=1)
    third = len(s) // 3
    t1 = _lufs(s[:third], sr)
    t2 = _lufs(s[third:2 * third], sr)
    t3 = _lufs(s[2 * third:], sr)
    if None in (t1, t2, t3):
        return {"lufs_t1": t1, "lufs_t2": t2, "lufs_t3": t3, "monotonic_decreasing": None, "delta_t1_t3": None, "duration_s": len(s) / sr}
    delta = t1 - t3
    monotonic = (t1 > t2 > t3) or (t1 == t2 > t3) or (t1 > t2 == t3)
    return {
        "lufs_t1": round(t1, 3),
        "lufs_t2": round(t2, 3),
        "lufs_t3": round(t3, 3),
        "monotonic_decreasing": bool(monotonic),
        "delta_t1_t3": round(delta, 3),
        "duration_s": round(len(s) / sr, 2),
    }


def main():
    per_vendor: dict[str, list[dict]] = defaultdict(list)
    for vendor_dir in sorted(R3.iterdir()):
        if not vendor_dir.is_dir():
            continue
        vendor = vendor_dir.name
        narr = vendor_dir / "narration"
        if not narr.is_dir():
            continue
        for wav in sorted(narr.glob("L*.wav")):
            item = wav.stem
            stats = _thirds(wav)
            per_vendor[vendor].append({"item_id": item, **stats})

    # Also compute per-vendor fade summary
    summary = {}
    for vendor, items in per_vendor.items():
        faders = [i for i in items if i.get("delta_t1_t3") is not None and i["delta_t1_t3"] >= FADE_THRESHOLD_DB and i["monotonic_decreasing"]]
        monotonic = [i for i in items if i.get("monotonic_decreasing")]
        summary[vendor] = {
            "n_items": len(items),
            "n_fade": len(faders),
            "n_monotonic_decreasing_any_magnitude": len(monotonic),
            "fade_rate_pct": round(len(faders) / max(1, len(items)) * 100, 1),
            "fading_items": [{"item_id": i["item_id"], "delta_t1_t3": i["delta_t1_t3"]} for i in faders],
        }

    out = {"fade_threshold_db": FADE_THRESHOLD_DB, "per_vendor": summary, "per_file": per_vendor}
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Print summary table
    print(f"# Item 1 — pinned narration voice fade rate on L01..L08, R3 campaign audio\n")
    print(f"Fade threshold: Δ(t1−t3) ≥ {FADE_THRESHOLD_DB} dB AND monotonically decreasing across thirds.\n")
    print(f"| vendor | n_items | fade / total | rate | mono-decr (any mag) | fading items |")
    print(f"|---|---:|---:|---:|---:|---|")
    for vendor in sorted(summary.keys()):
        s = summary[vendor]
        fading = ", ".join(f"{f['item_id']} ({f['delta_t1_t3']:+.2f}dB)" for f in s["fading_items"]) or "-"
        print(f"| {vendor} | {s['n_items']} | {s['n_fade']} / {s['n_items']} | {s['fade_rate_pct']:.0f}% | {s['n_monotonic_decreasing_any_magnitude']} / {s['n_items']} | {fading} |")

    # Aggregate across all vendors' pinned voices
    total_items = sum(s["n_items"] for s in summary.values())
    total_fade = sum(s["n_fade"] for s in summary.values())
    total_mono = sum(s["n_monotonic_decreasing_any_magnitude"] for s in summary.values())
    print(f"\n**Cross-vendor aggregate**: {total_fade} / {total_items} = {total_fade/total_items*100:.1f}% items fade at threshold on their vendor's pinned narration voice.")
    print(f"**Cross-vendor mono-decr any magnitude**: {total_mono} / {total_items} = {total_mono/total_items*100:.1f}%.")
    print(f"\nDetail written to: {OUT}")


if __name__ == "__main__":
    main()
