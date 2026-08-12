"""Recompute the noise floor properly (items 1-4 from review).

For each (vendor, use_case, signal) we compute:
    - within_draw_sd: SD across the 3 draws of each variance-subset
      item, pooled across items. Measures per-file inference noise.
    - between_item_sd: SD of the 75-item campaign column. Measures
      item-to-item variability at n=1 draw per item.
    - se_mean = sqrt(between_item_sd^2 / 75). Standard error of the
      75-item mean under the (mild) assumption that within-draw noise
      contributes negligibly at n_draws=1.
    - For a pair of vendors with means mu_a, mu_b on the same signal:
      SE(difference) = sqrt(se_mean_a^2 + se_mean_b^2). A pair is
      "significantly different" at alpha=0.05 iff |mu_a - mu_b| >
      1.96 * SE(diff).

We report the per-signal SE table, the top-2 vs #3 tie/not-tie for
each column of the 04_RESULTS.md tables, and per-signal absolute
scale so the review's item 3 (one number applied across two scales)
is directly addressed.

Also: item 4 asked for a pooled noise floor rather than one drawn
from the winner (Speechify T6). This recomputation uses ALL 8
vendors' variance-subset data, pooled — no circularity.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

CAMPAIGN = "campaign-20260809T204608Z"
VARIANCE = "variance-20260809T205319Z"


def _load(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _pooled_sd(sds: list[float], ns: list[int]) -> float | None:
    """Pooled SD across k groups with SD_i and n_i."""
    if not sds:
        return None
    num = sum((n - 1) * (s ** 2) for s, n in zip(sds, ns) if n > 1)
    den = sum((n - 1) for n in ns if n > 1)
    if den <= 0:
        return None
    return (num / den) ** 0.5


def compute_within_draw_sd(variance_doc: dict) -> dict[tuple[str, str, str], float]:
    """For each (vendor, use_case, signal), pool per-item SDs across
    the 3 draws. Returns dict keyed by (vendor, use_case, signal)."""

    files = variance_doc.get("audiobox_files", [])
    # Group by (vendor, use_case, item_id) → list of 3 draws
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for f in files:
        key = (f["provider"], f["use_case"], f["item_id"])
        groups.setdefault(key, []).append(f)

    # For each signal, collect per-item SDs (across the 3 draws), then
    # pool per (vendor, use_case)
    signals = [
        ("audiobox", "production_quality"),
        ("audiobox", "content_enjoyment"),
        ("dnsmos", "p808_mos"),
        ("dnsmos", "ovrl_mos"),
        ("dnsmos", "sig_mos"),
        ("dnsmos", "bak_mos"),
    ]

    per_item_sds: dict[tuple[str, str, str], list[tuple[float, int]]] = {}
    for (prov, uc, _item), draws in groups.items():
        for source, axis in signals:
            vals = [f.get(source, {}).get(axis) for f in draws]
            vals = [v for v in vals if v is not None]
            if len(vals) < 2:
                continue
            sd = statistics.stdev(vals)
            per_item_sds.setdefault((prov, uc, f"{source}.{axis}"), []).append((sd, len(vals)))

    within_sd: dict[tuple[str, str, str], float] = {}
    for key, sd_n_list in per_item_sds.items():
        sds = [s for s, _ in sd_n_list]
        ns = [n for _, n in sd_n_list]
        pooled = _pooled_sd(sds, ns)
        if pooled is not None:
            within_sd[key] = pooled
    return within_sd


def compute_between_item_sd(campaign_doc: dict) -> dict[tuple[str, str, str], tuple[float, int]]:
    """For each (vendor, use_case, signal), empirical SD of the 75
    per-item scores (single draw each). Returns dict → (sd, n)."""

    files = campaign_doc.get("audiobox_files", [])
    signals = [
        ("audiobox", "production_quality"),
        ("audiobox", "content_enjoyment"),
        ("dnsmos", "p808_mos"),
        ("dnsmos", "ovrl_mos"),
        ("dnsmos", "sig_mos"),
        ("dnsmos", "bak_mos"),
    ]

    vals_by_key: dict[tuple[str, str, str], list[float]] = {}
    for f in files:
        for source, axis in signals:
            v = f.get(source, {}).get(axis)
            if v is None:
                continue
            key = (f["provider"], f["use_case"], f"{source}.{axis}")
            vals_by_key.setdefault(key, []).append(v)

    result: dict[tuple[str, str, str], tuple[float, int]] = {}
    for key, vals in vals_by_key.items():
        if len(vals) < 2:
            continue
        result[key] = (statistics.stdev(vals), len(vals))
    return result


def se_mean(between_sd: float, n: int) -> float:
    """SE of an n-item mean, dominated by between-item SD at n>=10."""
    return between_sd / (n ** 0.5)


def se_diff(se_a: float, se_b: float) -> float:
    return (se_a ** 2 + se_b ** 2) ** 0.5


def per_signal_summary(sig: str, within: dict, between: dict, means: dict) -> None:
    """Print per-vendor SD, SE_mean, then the top-3 and their tie call."""

    conv_rows = []
    narr_rows = []
    for (prov, uc, s), (sd, n) in between.items():
        if s != sig:
            continue
        se = se_mean(sd, n)
        mean = means.get((prov, uc, s))
        w = within.get((prov, uc, s))
        row = (prov, mean, sd, se, w, n)
        if uc == "conversational":
            conv_rows.append(row)
        elif uc == "narration":
            narr_rows.append(row)

    for uc_name, rows in [("conversational", conv_rows), ("narration", narr_rows)]:
        if not rows:
            continue
        print(f"\n  --- {uc_name} ---")
        print(f"  {'vendor':11s} {'mean':>7s} {'SD_75':>7s} {'SE_mean':>8s} {'SD_within':>10s} {'n':>3s}")
        for prov, mean, sd, se, w, n in sorted(rows, key=lambda r: -(r[1] or 0)):
            w_str = f"{w:.4f}" if w is not None else "n/a"
            print(f"  {prov:11s} {mean:>7.3f} {sd:>7.3f} {se:>8.4f} {w_str:>10s} {n:>3}")

        # Compute top-3 pairwise tie tests
        rows_sorted = sorted(rows, key=lambda r: -(r[1] or 0))
        if len(rows_sorted) >= 3:
            top1, top2, top3 = rows_sorted[0], rows_sorted[1], rows_sorted[2]
            for (a, b) in [(top1, top2), (top2, top3), (top1, top3)]:
                if a[1] is None or b[1] is None:
                    continue
                delta = a[1] - b[1]
                se_d = se_diff(a[3], b[3])
                ratio = abs(delta) / se_d if se_d > 0 else float("inf")
                verdict = "SIG_DIFF" if abs(delta) > 1.96 * se_d else "TIE"
                print(f"  {a[0]} vs {b[0]}: delta={delta:+.3f}  SE_diff={se_d:.4f}  |delta|/SE_diff={ratio:.1f}  {verdict}")


def main() -> None:
    var_doc = _load(f"analysis/{VARIANCE}/quality.json")
    camp_doc = _load(f"analysis/{CAMPAIGN}/quality.json")

    within = compute_within_draw_sd(var_doc)
    between = compute_between_item_sd(camp_doc)

    # Means from the campaign per-vendor aggregates
    means: dict[tuple[str, str, str], float] = {}
    for r in camp_doc.get("audiobox_by_provider", []):
        for ax, val in r["audiobox_means"].items():
            means[(r["provider"], r["use_case"], f"audiobox.{ax}")] = val
    for r in camp_doc.get("dnsmos_by_provider", []):
        for ax, val in r["dnsmos_means"].items():
            means[(r["provider"], r["use_case"], f"dnsmos.{ax}")] = val

    print("=" * 88)
    print("NOISE FLOOR RECOMPUTE (per-vendor per-signal, no circularity)")
    print("=" * 88)
    print("SD_75      = empirical SD of the vendor's 75 per-item scores (single draw each)")
    print("SE_mean    = SD_75 / sqrt(75) = SE of the reported vendor mean")
    print("SD_within  = pooled per-item SD across the 3 variance-subset draws")
    print("             (measures inference-time reproducibility, per file)")
    print("SIG_DIFF   = |mean_a - mean_b| > 1.96 * SE(diff)  [alpha=0.05]")

    for sig in ["audiobox.production_quality", "audiobox.content_enjoyment",
                 "dnsmos.p808_mos", "dnsmos.ovrl_mos", "dnsmos.sig_mos", "dnsmos.bak_mos"]:
        print(f"\n============================================================")
        print(f"SIGNAL: {sig}")
        print(f"============================================================")
        per_signal_summary(sig, within, between, means)


if __name__ == "__main__":
    main()
