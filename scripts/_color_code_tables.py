"""Generate color-coded markdown tables for 04_RESULTS.md.

Color coding per column:
    top-2 within the column = green square (best)
    bottom-2 within the column = red square (worst)
    middle-4 within the column = yellow square

Higher-is-better columns: AB.PQ, AB.CE, DN.p808, DN.ovrl, DN.sig, DN.bak,
    noise floor (dBFS, more-negative-is-cleaner so LOWER is BETTER)
Lower-is-better columns: clip samples, WER %, TTFA ms, $/1K words

Special:
- clip samples: all 0 stay green (perfect); nonzero ranked worst-first
- TTFA: only conversational has values; narration skipped
"""

from __future__ import annotations

import json
from pathlib import Path

CAMPAIGN = "campaign-20260809T204608Z"
LATENCY = "latency-20260809T214106Z"

GREEN = "🟢"
YELLOW = "🟡"
RED = "🔴"

def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rank_cells(values: list[float], higher_is_better: bool = True) -> list[str]:
    """Return color emojis for a column of 8 values.
    Top 2 = green, bottom 2 = red, middle 4 = yellow.
    Ties by original insertion order (stable sort).
    """
    n = len(values)
    # Sort indices by value
    if higher_is_better:
        sorted_idx = sorted(range(n), key=lambda i: (-values[i], i))
    else:
        sorted_idx = sorted(range(n), key=lambda i: (values[i], i))
    colors = [YELLOW] * n
    # Top 2
    for i in sorted_idx[:2]:
        colors[i] = GREEN
    # Bottom 2
    for i in sorted_idx[-2:]:
        colors[i] = RED
    return colors


def rank_cells_special_clip(values: list[int]) -> list[str]:
    """Clip samples: all zeros = green; anything nonzero ranked worst-first."""
    colors = []
    nonzero_max = max(values) if any(v > 0 for v in values) else 0
    for v in values:
        if v == 0:
            colors.append(GREEN)
        elif v >= 100:
            colors.append(RED)
        elif v > 0:
            colors.append(YELLOW)
    return colors


def build_table(uc: str) -> str:
    q = _load(f"analysis/{CAMPAIGN}/quality.json")
    h = _load(f"analysis/{CAMPAIGN}/hygiene.json")
    w = _load(f"analysis/{CAMPAIGN}/wer.json")
    c = _load(f"analysis/{CAMPAIGN}/cost_model.json")
    lat = _load(f"analysis/{LATENCY}/latency.json") if uc == "conversational" else None

    cost_by_p = {p["provider"]: p.get("dollars_per_1k_words_at", {}).get("100K_words_per_month") for p in c["providers"]}

    # Get provider rows
    providers = sorted({r["provider"] for r in q["audiobox_by_provider"] if r["use_case"] == uc})
    rows = []
    for p in providers:
        ab = next(r["audiobox_means"] for r in q["audiobox_by_provider"] if r["provider"] == p and r["use_case"] == uc)
        dn = next(r["dnsmos_means"] for r in q["dnsmos_by_provider"] if r["provider"] == p and r["use_case"] == uc)
        hg = next(r for r in h["by_provider"] if r["provider"] == p and r["use_case"] == uc)
        wer_items = [i for i in w["items"] if i.get("provider") == p and i.get("use_case") == uc and i.get("agreement_wer") is not None]
        wer_mean = 100 * sum(i["agreement_wer"] for i in wer_items) / len(wer_items) if wer_items else 0
        ttfa = None
        if lat:
            lat_r = next((r for r in lat["by_provider"] if r["provider"] == p and r.get("use_case") == uc and r.get("ttfa_p50_ms")), None)
            if lat_r:
                ttfa = lat_r["ttfa_p50_ms"]
        rows.append({
            "provider": p,
            "ab_pq": ab["production_quality"],
            "ab_ce": ab["content_enjoyment"],
            "dn_p808": dn["p808_mos"],
            "dn_ovrl": dn["ovrl_mos"],
            "dn_sig": dn["sig_mos"],
            "dn_bak": dn["bak_mos"],
            "clip": hg["total_clipped_samples"],
            "nf": hg["mean_noise_floor_dbfs"],
            "wer": wer_mean,
            "ttfa": ttfa,
            "cost": cost_by_p.get(p),
        })

    # Sort rows by ab_pq desc (matches the existing table order)
    rows.sort(key=lambda r: -r["ab_pq"])

    # Extract column values in row order
    def col(k): return [r[k] for r in rows]

    # Compute per-column colors
    colors = {
        "ab_pq":   rank_cells(col("ab_pq"), higher_is_better=True),
        "ab_ce":   rank_cells(col("ab_ce"), higher_is_better=True),
        "dn_p808": rank_cells(col("dn_p808"), higher_is_better=True),
        "dn_ovrl": rank_cells(col("dn_ovrl"), higher_is_better=True),
        "dn_sig":  rank_cells(col("dn_sig"), higher_is_better=True),
        "dn_bak":  rank_cells(col("dn_bak"), higher_is_better=True),
        # clip samples: 0 is best (special handling)
        "clip":    rank_cells_special_clip(col("clip")),
        # noise floor: more-negative (lower) is better
        "nf":      rank_cells(col("nf"), higher_is_better=False),
        # WER: lower is better
        "wer":     rank_cells(col("wer"), higher_is_better=False),
        # cost: lower is better
        "cost":    rank_cells(col("cost"), higher_is_better=False),
    }
    # TTFA only for conversational; skip in narration
    if lat:
        ttfa_vals = col("ttfa")
        # Some vendors don't report TTFA (Speechify, Fish, Google, Orpheus per D-008 and adapter-shape).
        # For those, mark with "—" (no color); for measured, rank the measured subset.
        measured_ix = [i for i, v in enumerate(ttfa_vals) if v is not None]
        colors["ttfa"] = ["—"] * len(rows)
        if measured_ix:
            measured_vals = [ttfa_vals[i] for i in measured_ix]
            sub_colors = rank_cells(measured_vals, higher_is_better=False)
            for i, c in zip(measured_ix, sub_colors):
                colors["ttfa"][i] = c

    # Build markdown
    if uc == "conversational":
        header = "| Vendor | AB.PQ | AB.CE | DN.p808 | DN.ovrl | DN.sig | DN.bak | clip samples | noise floor (dBFS) | WER % | TTFA p50 (ms) | $/1K words |"
        sep = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    else:
        header = "| Vendor | AB.PQ | AB.CE | DN.p808 | DN.ovrl | DN.sig | DN.bak | clip samples | noise floor (dBFS) | WER % | $/1K words |"
        sep = "|---|---|---|---|---|---|---|---|---|---|---|"

    lines = [header, sep]
    for i, r in enumerate(rows):
        cells = [
            r["provider"],
            f"{colors['ab_pq'][i]} {r['ab_pq']:.2f}",
            f"{colors['ab_ce'][i]} {r['ab_ce']:.2f}",
            f"{colors['dn_p808'][i]} {r['dn_p808']:.2f}",
            f"{colors['dn_ovrl'][i]} {r['dn_ovrl']:.2f}",
            f"{colors['dn_sig'][i]} {r['dn_sig']:.2f}",
            f"{colors['dn_bak'][i]} {r['dn_bak']:.2f}",
            f"{colors['clip'][i]} {r['clip']}",
            f"{colors['nf'][i]} {r['nf']:.1f}",
            f"{colors['wer'][i]} {r['wer']:.1f}",
        ]
        if uc == "conversational":
            ttfa = r["ttfa"]
            ttfa_str = f"{colors['ttfa'][i]} {ttfa:.0f}" if ttfa is not None else "—"
            cells.append(ttfa_str)
        cells.append(f"{colors['cost'][i]} {r['cost']:.3f}")
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def main() -> None:
    out = Path("scripts/_color_coded_tables.md")
    content = "### Conversational\n\n" + build_table("conversational") + "\n\n### Narration\n\n" + build_table("narration") + "\n"
    out.write_text(content, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
