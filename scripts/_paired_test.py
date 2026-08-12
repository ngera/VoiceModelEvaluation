"""Paired-test recompute for Wave 1 item 8.

Our published SE(diff) = sqrt(SE_a^2 + SE_b^2) is the unpaired
formula. It assumes vendor-a's items and vendor-b's items are
independent samples. But every vendor speaks the SAME 75 corpus
items, so item-level effects (a hard-to-say item scoring low for
all vendors) are shared and should cancel in the paired difference.

The paired test is:
    delta_i = score_a(item_i) - score_b(item_i)   for i in 1..75
    SE_paired = SD(delta) / sqrt(75)
    z = |mean(delta)| / SE_paired

If item-level effects are strongly correlated across vendors (they
usually are), SE_paired < SE_unpaired and the paired z-score is
LARGER — the unpaired verdict is the conservative one.

This script recomputes the primary top-1-vs-top-2 comparisons under
both tests so 04_RESULTS.md can report both and state the direction
of the conservatism explicitly.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

CAMPAIGN = "campaign-20260809T204608Z"


def _load(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _per_item(doc: dict, signal: str) -> dict[tuple[str, str], dict[str, float]]:
    """Return {(vendor, use_case): {item_id: score}} for the given signal.

    Signal format: 'audiobox.production_quality' or 'dnsmos.ovrl_mos'.
    """
    source, axis = signal.split(".", 1)
    out: dict[tuple[str, str], dict[str, float]] = {}
    for f in doc.get("audiobox_files", []):
        v = f.get(source, {}).get(axis)
        if v is None:
            continue
        key = (f["provider"], f["use_case"])
        out.setdefault(key, {})[f["item_id"]] = v
    return out


def _paired(a_by_item: dict[str, float], b_by_item: dict[str, float]) -> dict:
    """Compute the paired test on the shared items."""
    shared = sorted(set(a_by_item) & set(b_by_item))
    if len(shared) < 3:
        return {"n_shared": len(shared), "verdict": "insufficient"}
    deltas = [a_by_item[i] - b_by_item[i] for i in shared]
    mean_delta = statistics.mean(deltas)
    sd_delta = statistics.stdev(deltas)
    n = len(deltas)
    se_paired = sd_delta / (n ** 0.5)
    z = abs(mean_delta) / se_paired if se_paired > 0 else float("inf")
    return {
        "n_shared": n,
        "mean_delta": mean_delta,
        "sd_delta": sd_delta,
        "se_paired": se_paired,
        "z_paired": z,
    }


def _unpaired(a_by_item: dict[str, float], b_by_item: dict[str, float]) -> dict:
    """Compute the unpaired test on each vendor's full sample."""
    a_vals = list(a_by_item.values())
    b_vals = list(b_by_item.values())
    if len(a_vals) < 2 or len(b_vals) < 2:
        return {"verdict": "insufficient"}
    mean_a = statistics.mean(a_vals)
    mean_b = statistics.mean(b_vals)
    sd_a = statistics.stdev(a_vals)
    sd_b = statistics.stdev(b_vals)
    se_a = sd_a / (len(a_vals) ** 0.5)
    se_b = sd_b / (len(b_vals) ** 0.5)
    se_unpaired = (se_a ** 2 + se_b ** 2) ** 0.5
    delta = mean_a - mean_b
    z = abs(delta) / se_unpaired if se_unpaired > 0 else float("inf")
    return {
        "n_a": len(a_vals),
        "n_b": len(b_vals),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "delta": delta,
        "se_unpaired": se_unpaired,
        "z_unpaired": z,
    }


def _compare(camp: dict, use_case: str, signal: str, a: str, b: str) -> None:
    per = _per_item(camp, signal)
    a_by = per.get((a, use_case), {})
    b_by = per.get((b, use_case), {})
    if not a_by or not b_by:
        print(f"  ({a}/{b} {use_case} {signal}: missing)")
        return
    up = _unpaired(a_by, b_by)
    pr = _paired(a_by, b_by)
    if "verdict" in up or "verdict" in pr:
        print(f"  ({a} vs {b} {use_case} {signal}: insufficient)")
        return
    ratio = pr["z_paired"] / up["z_unpaired"] if up["z_unpaired"] > 0 else float("inf")
    print(f"  {a:11s} vs {b:11s} ({use_case[:5]}, {signal.split('.')[1][:6]}):"
          f" delta={up['delta']:+.3f}"
          f"  unpaired z={up['z_unpaired']:.1f}sigma (SE={up['se_unpaired']:.4f})"
          f"  paired z={pr['z_paired']:.1f}sigma (SE={pr['se_paired']:.4f}, n={pr['n_shared']})"
          f"  paired/unpaired={ratio:.2f}x")


def main() -> None:
    camp = _load(f"analysis/{CAMPAIGN}/quality.json")

    print("=" * 100)
    print("PAIRED vs UNPAIRED TEST COMPARISON (Wave 1 item 8)")
    print("=" * 100)
    print("Unpaired: SE(diff) = sqrt(SE_a^2 + SE_b^2), independence assumption")
    print("Paired:   SE_paired = SD(delta) / sqrt(n_shared), leverages item-level correlation")
    print("If paired/unpaired > 1: paired test is tighter (more significant).")
    print()

    print("--- Audiobox PQ + CE, top-1 vs top-2 comparisons ---")
    _compare(camp, "conversational", "audiobox.production_quality", "speechify", "elevenlabs")
    _compare(camp, "conversational", "audiobox.content_enjoyment", "speechify", "fish")
    _compare(camp, "narration", "audiobox.production_quality", "speechify", "cartesia")
    _compare(camp, "narration", "audiobox.content_enjoyment", "speechify", "elevenlabs")

    print("\n--- DNSMOS OVRL + SIG, top-1 vs top-2 comparisons (tie calls) ---")
    _compare(camp, "conversational", "dnsmos.ovrl_mos", "openai", "elevenlabs")
    _compare(camp, "conversational", "dnsmos.sig_mos", "openai", "elevenlabs")
    _compare(camp, "narration", "dnsmos.ovrl_mos", "openai", "deepgram")
    _compare(camp, "narration", "dnsmos.sig_mos", "openai", "deepgram")


if __name__ == "__main__":
    main()
