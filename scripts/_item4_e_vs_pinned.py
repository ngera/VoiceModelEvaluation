"""Item 4: alt-voice E audio vs R3 primary-campaign pinned-voice audio.

For each of 4 vendors (openai, fish, deepgram, google), compare:
- Audiobox PQ + CE means on L01..L08 with alt voice (E) vs pinned voice (R3)
- DNSMOS OVRL means (where DNSMOS returned scores)
- WER agreement means

Answer the T6-style question: does the alt voice preserve
approximately the same quality-axis scores as the pinned voice on
the same 8 items?
"""

from __future__ import annotations

import json
from pathlib import Path


R3 = Path("analysis/campaign-20260831T175358Z")
E = Path("analysis/experiments-2026-09-01-E")

VENDORS_TO_COMPARE = ["openai", "fish", "deepgram", "google"]


def _load_quality(analysis_dir: Path) -> dict:
    return json.loads((analysis_dir / "quality.json").read_text(encoding="utf-8"))


def _load_wer(analysis_dir: Path) -> dict:
    return json.loads((analysis_dir / "wer.json").read_text(encoding="utf-8"))


def _l_items_ab_means(quality_doc: dict, provider: str) -> dict:
    """Return per-axis mean over L01..L08 items from a quality.json.

    Uses audiobox_files (per-file scores) filtered to provider/narration
    and item_id starting with 'L' (long stratum).
    """
    files = [
        f for f in quality_doc.get("audiobox_files", [])
        if f.get("provider") == provider
        and f.get("use_case") == "narration"
        and f.get("item_id", "").startswith("L")
    ]
    pq = [f.get("audiobox", {}).get("production_quality") for f in files if f.get("audiobox", {}).get("production_quality") is not None]
    ce = [f.get("audiobox", {}).get("content_enjoyment") for f in files if f.get("audiobox", {}).get("content_enjoyment") is not None]
    dovrl = [f.get("dnsmos", {}).get("ovrl_mos") for f in files if f.get("dnsmos", {}).get("ovrl_mos") is not None]
    return {
        "n_ab": len(pq),
        "pq_mean": sum(pq) / len(pq) if pq else None,
        "ce_mean": sum(ce) / len(ce) if ce else None,
        "n_dnsmos": len(dovrl),
        "dnsmos_ovrl_mean": sum(dovrl) / len(dovrl) if dovrl else None,
    }


def _l_items_wer_mean(wer_doc: dict, provider: str) -> dict:
    items = [
        i for i in wer_doc.get("items", [])
        if i.get("provider") == provider
        and i.get("use_case") == "narration"
        and i.get("item_id", "").startswith("L")
    ]
    wers = [i.get("agreement_wer") for i in items if i.get("agreement_wer") is not None]
    return {
        "n_wer": len(wers),
        "wer_mean": sum(wers) / len(wers) if wers else None,
    }


def main():
    r3_q = _load_quality(R3)
    e_q = _load_quality(E)
    r3_w = _load_wer(R3)
    e_w = _load_wer(E)

    print("# Follow-up 4 — Alt-voice quality/WER vs pinned-voice, L01..L08 narration\n")
    print("Compares each vendor's **alt voice** (Experiment E) against their")
    print("**pinned voice** (R3 primary campaign) on the SAME 8 long narration items.")
    print("This is the T6-style test: does the ranking hold under voice change?\n")

    print("| vendor | axis | pinned (R3) mean | alt (E) mean | Δ (alt − pinned) | % change | n |")
    print("|---|---|---:|---:|---:|---:|---:|")
    for v in VENDORS_TO_COMPARE:
        p = _l_items_ab_means(r3_q, v)
        a = _l_items_ab_means(e_q, v)
        pw = _l_items_wer_mean(r3_w, v)
        aw = _l_items_wer_mean(e_w, v)
        for axis, pinned, alt, n, fmt in [
            ("AB.PQ", p["pq_mean"], a["pq_mean"], min(p["n_ab"], a["n_ab"]), "{:.3f}"),
            ("AB.CE", p["ce_mean"], a["ce_mean"], min(p["n_ab"], a["n_ab"]), "{:.3f}"),
            ("DN.ovrl", p["dnsmos_ovrl_mean"], a["dnsmos_ovrl_mean"], min(p["n_dnsmos"], a["n_dnsmos"]), "{:.3f}"),
            ("WER", pw["wer_mean"], aw["wer_mean"], min(pw["n_wer"], aw["n_wer"]), "{:.4f}"),
        ]:
            if pinned is None or alt is None:
                print(f"| {v} | {axis} | {'n/a' if pinned is None else fmt.format(pinned)} | {'n/a' if alt is None else fmt.format(alt)} | – | – | {n} |")
                continue
            d = alt - pinned
            pct = d / pinned * 100 if pinned else 0
            print(f"| {v} | {axis} | {fmt.format(pinned)} | {fmt.format(alt)} | {d:+.4f} | {pct:+.2f}% | {n} |")

    # Vendor summary: do rankings hold?
    print("\n## T6-style interpretation\n")
    print("**Question**: for each vendor, is the alt voice's score close to (within ~5% or ~0.15 on Audiobox / 0.15 on DNSMOS) the pinned voice's score on the same items?\n")
    for v in VENDORS_TO_COMPARE:
        p = _l_items_ab_means(r3_q, v)
        a = _l_items_ab_means(e_q, v)
        pw = _l_items_wer_mean(r3_w, v)
        aw = _l_items_wer_mean(e_w, v)
        deltas = []
        if p["pq_mean"] and a["pq_mean"]:
            deltas.append(("AB.PQ", a["pq_mean"] - p["pq_mean"]))
        if p["ce_mean"] and a["ce_mean"]:
            deltas.append(("AB.CE", a["ce_mean"] - p["ce_mean"]))
        if p["dnsmos_ovrl_mean"] and a["dnsmos_ovrl_mean"]:
            deltas.append(("DN.ovrl", a["dnsmos_ovrl_mean"] - p["dnsmos_ovrl_mean"]))
        if pw["wer_mean"] is not None and aw["wer_mean"] is not None:
            deltas.append(("WER", aw["wer_mean"] - pw["wer_mean"]))
        max_ab_delta = max((abs(d) for axis, d in deltas if axis.startswith("AB")), default=0)
        max_dn_delta = max((abs(d) for axis, d in deltas if axis.startswith("DN")), default=0)
        wer_delta = next((d for axis, d in deltas if axis == "WER"), None)
        # A "hold" if AB deltas < 0.15 and DN < 0.15 and |WER| < 0.03
        hold = max_ab_delta < 0.15 and max_dn_delta < 0.15 and (wer_delta is None or abs(wer_delta) < 0.03)
        d_str = ", ".join(f"{axis}={d:+.3f}" for axis, d in deltas)
        verdict = "✓ HOLDS (deltas within noise)" if hold else "⚠ SHIFTS (alt voice diverges materially)"
        print(f"- **{v}**: {d_str}  →  {verdict}")


if __name__ == "__main__":
    main()
