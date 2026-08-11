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

# GitHub's markdown sanitizer strips both `style="..."` inline CSS AND
# the legacy `bgcolor` attribute on <td>. The reliable workaround is
# an inline color-chip <img> from placehold.co placed at the start of
# each numeric cell — reads as a colored bar next to the value.
GREEN = "c8e6c9"    # light green (hex without #)
YELLOW = "fff9c4"   # light yellow
RED = "ffcdd2"      # light red
NONE = None

def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rank_cells(values: list[float], higher_is_better: bool = True) -> list[str]:
    """Return bgcolor hex strings for a column of 8 values.
    Top 2 = light green, bottom 2 = light red, middle 4 = light yellow.
    Ties by original insertion order (stable sort).
    """
    n = len(values)
    if higher_is_better:
        sorted_idx = sorted(range(n), key=lambda i: (-values[i], i))
    else:
        sorted_idx = sorted(range(n), key=lambda i: (values[i], i))
    colors = [YELLOW] * n
    for i in sorted_idx[:2]:
        colors[i] = GREEN
    for i in sorted_idx[-2:]:
        colors[i] = RED
    return colors


def rank_cells_special_clip(values: list[int]) -> list[str]:
    """Clip samples: 0 = green; >=100 = red; 1-99 = yellow."""
    colors = []
    for v in values:
        if v == 0:
            colors.append(GREEN)
        elif v >= 100:
            colors.append(RED)
        else:
            colors.append(YELLOW)
    return colors


def td(text: str, bg: str | None) -> str:
    """Render one <td> with an inline color chip if bg is set.
    Chip is a small placehold.co image; label = color name for
    screen readers. Right-aligned for numeric.
    """
    if not bg:
        return f'<td align="right">{text}</td>'
    label = {"c8e6c9": "best", "fff9c4": "mid", "ffcdd2": "worst"}.get(bg, "")
    chip = f'<img src="https://placehold.co/40x18/{bg}/{bg}.png" alt="{label}">'
    return f'<td align="right">{chip} {text}</td>'


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
        measured_ix = [i for i, v in enumerate(ttfa_vals) if v is not None]
        colors["ttfa"] = [None] * len(rows)
        if measured_ix:
            measured_vals = [ttfa_vals[i] for i in measured_ix]
            sub_colors = rank_cells(measured_vals, higher_is_better=False)
            for i, c in zip(measured_ix, sub_colors):
                colors["ttfa"][i] = c

    # Build HTML table (GitHub markdown supports raw HTML + <td bgcolor>)
    if uc == "conversational":
        headers = ["Vendor", "AB.PQ", "AB.CE", "DN.p808", "DN.ovrl", "DN.sig", "DN.bak",
                    "clip samples", "noise floor (dBFS)", "WER %", "TTFA p50 (ms)", "$/1K words"]
    else:
        headers = ["Vendor", "AB.PQ", "AB.CE", "DN.p808", "DN.ovrl", "DN.sig", "DN.bak",
                    "clip samples", "noise floor (dBFS)", "WER %", "$/1K words"]

    lines = ["<table>", "<thead>", "<tr>"]
    for h in headers:
        lines.append(f'<th>{h}</th>')
    lines.extend(["</tr>", "</thead>", "<tbody>"])

    for i, r in enumerate(rows):
        lines.append("<tr>")
        lines.append(f'<td><b>{r["provider"]}</b></td>')
        lines.append(td(f'{r["ab_pq"]:.2f}',   colors["ab_pq"][i]))
        lines.append(td(f'{r["ab_ce"]:.2f}',   colors["ab_ce"][i]))
        lines.append(td(f'{r["dn_p808"]:.2f}', colors["dn_p808"][i]))
        lines.append(td(f'{r["dn_ovrl"]:.2f}', colors["dn_ovrl"][i]))
        lines.append(td(f'{r["dn_sig"]:.2f}',  colors["dn_sig"][i]))
        lines.append(td(f'{r["dn_bak"]:.2f}',  colors["dn_bak"][i]))
        lines.append(td(f'{r["clip"]}',        colors["clip"][i]))
        lines.append(td(f'{r["nf"]:.1f}',      colors["nf"][i]))
        lines.append(td(f'{r["wer"]:.1f}',     colors["wer"][i]))
        if uc == "conversational":
            ttfa = r["ttfa"]
            if ttfa is None:
                lines.append('<td align="right">—</td>')
            else:
                lines.append(td(f'{ttfa:.0f}', colors["ttfa"][i]))
        lines.append(td(f'{r["cost"]:.3f}', colors["cost"][i]))
        lines.append("</tr>")

    lines.extend(["</tbody>", "</table>"])
    return "\n".join(lines)


def main() -> None:
    out = Path("scripts/_color_coded_tables.md")
    content = "### Conversational\n\n" + build_table("conversational") + "\n\n### Narration\n\n" + build_table("narration") + "\n"
    out.write_text(content, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
