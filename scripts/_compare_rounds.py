"""Compare round-2 baseline (2026-08-09) vs round-3 replication (2026-08-31).

Reads the analysis JSONs for both campaigns and produces:
- Per-vendor per-use-case mean deltas on AB.PQ, AB.CE, DNSMOS (4 axes), WER
- Failure-incidence delta on WER
- Hygiene deltas (clipped samples, noise floor, speech ratio)
- Cost totals and per-vendor observed_cost_usd deltas
- Ranking flips per axis
- Cross-pipeline mean rho change (F-8 stability)
- Rank correlation (Spearman) between R2 and R3 per-vendor rankings per axis

Emits a Markdown-friendly table on stdout.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

R2 = "campaign-20260809T204608Z"
R3 = "campaign-20260831T175358Z"


def _load(run: str, stage: str) -> dict:
    return json.loads(
        Path(f"analysis/{run}/{stage}.json").read_text(encoding="utf-8")
    )


def _by_provider_uc(rows: list[dict], key: str) -> dict:
    """Return {(provider, use_case): value_at_key} for a list of by_provider rows."""
    out = {}
    for r in rows:
        v = r.get(key)
        out[(r["provider"], r["use_case"])] = v
    return out


def _nested_by_provider_uc(rows: list[dict], outer: str, inner: str) -> dict:
    """Return {(provider, use_case): value_at_outer[inner]}."""
    out = {}
    for r in rows:
        d = r.get(outer, {}) or {}
        v = d.get(inner)
        out[(r["provider"], r["use_case"])] = v
    return out


def compare_signal(name: str, r2_map: dict, r3_map: dict, fmt: str = "{:.3f}") -> None:
    """Print a per-vendor comparison table for one signal."""
    print(f"\n### {name}\n")
    print("| Vendor | Use case | R2 (baseline) | R3 (replication) | Δ (R3−R2) | % change |")
    print("|---|---|---:|---:|---:|---:|")
    all_keys = sorted(set(r2_map.keys()) | set(r3_map.keys()))
    for (prov, uc) in all_keys:
        v2 = r2_map.get((prov, uc))
        v3 = r3_map.get((prov, uc))
        if v2 is None or v3 is None:
            row = f"| {prov} | {uc} | {'-' if v2 is None else fmt.format(v2)} | {'-' if v3 is None else fmt.format(v3)} | - | - |"
            print(row)
            continue
        d = v3 - v2
        pct = (d / v2 * 100) if v2 else 0
        print(f"| {prov} | {uc} | {fmt.format(v2)} | {fmt.format(v3)} | {d:+.3f} | {pct:+.1f}% |")


def top1_per_signal(r2_map: dict, r3_map: dict, higher_is_better: bool = True) -> None:
    """For each use case, print top-1 vendor in R2 vs R3."""
    by_uc: dict[str, list] = {}
    for (prov, uc), v in r2_map.items():
        by_uc.setdefault(uc, []).append((prov, v, "R2"))
    for (prov, uc), v in r3_map.items():
        by_uc.setdefault(uc, []).append((prov, v, "R3"))

    for uc in sorted(by_uc.keys()):
        r2_rows = [(p, v) for p, v, r in by_uc[uc] if r == "R2" and v is not None]
        r3_rows = [(p, v) for p, v, r in by_uc[uc] if r == "R3" and v is not None]
        r2_sorted = sorted(r2_rows, key=lambda t: -t[1] if higher_is_better else t[1])
        r3_sorted = sorted(r3_rows, key=lambda t: -t[1] if higher_is_better else t[1])
        r2_top = r2_sorted[0][0] if r2_sorted else "?"
        r3_top = r3_sorted[0][0] if r3_sorted else "?"
        flip = "" if r2_top == r3_top else "  ⚠ FLIP"
        print(f"  {uc:14s}: R2 #1 = {r2_top:12s}  R3 #1 = {r3_top:12s}{flip}")


def spearman_rank(r2_map: dict, r3_map: dict) -> dict:
    """Per use case, Spearman rank correlation between R2 and R3 vendor orderings."""
    by_uc: dict[str, dict] = {}
    for (prov, uc), v in r2_map.items():
        by_uc.setdefault(uc, {}).setdefault("r2", {})[prov] = v
    for (prov, uc), v in r3_map.items():
        by_uc.setdefault(uc, {}).setdefault("r3", {})[prov] = v

    result = {}
    for uc, dicts in by_uc.items():
        r2 = dicts.get("r2", {})
        r3 = dicts.get("r3", {})
        common = sorted(p for p in r2 if p in r3 and r2[p] is not None and r3[p] is not None)
        if len(common) < 3:
            result[uc] = None
            continue
        v2 = [r2[p] for p in common]
        v3 = [r3[p] for p in common]
        # Ranks (higher = rank 1)
        def _ranks(vals):
            sorted_idx = sorted(range(len(vals)), key=lambda i: -vals[i])
            ranks = [0] * len(vals)
            for rank, idx in enumerate(sorted_idx, start=1):
                ranks[idx] = rank
            return ranks
        rk2, rk3 = _ranks(v2), _ranks(v3)
        n = len(common)
        d2 = sum((a - b) ** 2 for a, b in zip(rk2, rk3))
        rho = 1 - (6 * d2) / (n * (n * n - 1))
        result[uc] = (rho, n, common)
    return result


def main() -> None:
    q2 = _load(R2, "quality")
    q3 = _load(R3, "quality")
    w2 = _load(R2, "wer")
    w3 = _load(R3, "wer")
    h2 = _load(R2, "hygiene")
    h3 = _load(R3, "hygiene")
    c2 = _load(R2, "cost_model")
    c3 = _load(R3, "cost_model")
    x2 = _load(R2, "cross_metric")
    x3 = _load(R3, "cross_metric")

    print("# Round-2 (2026-08-09) vs Round-3 (2026-08-31) — replication comparison")
    print("")
    print(f"- R2 run: `{R2}` — {q2.get('run_id')}")
    print(f"- R3 run: `{R3}` — {q3.get('run_id')}")

    # === Cost totals ===
    print(f"\n## Cost totals")
    print(f"- R2 total_observed_cost_usd: **${c2['total_observed_cost_usd']:.4f}**")
    print(f"- R3 total_observed_cost_usd: **${c3['total_observed_cost_usd']:.4f}**")
    delta = c3['total_observed_cost_usd'] - c2['total_observed_cost_usd']
    pct = delta / c2['total_observed_cost_usd'] * 100
    print(f"- Δ: **{delta:+.4f}** ({pct:+.2f}%)")

    print(f"\n### Per-vendor observed cost (delta)")
    c2_by = {r["provider"]: r["observed_cost_usd"] for r in c2["providers"]}
    c3_by = {r["provider"]: r["observed_cost_usd"] for r in c3["providers"]}
    print("| Vendor | R2 $ | R3 $ | Δ$ | % change |")
    print("|---|---:|---:|---:|---:|")
    for p in sorted(c2_by.keys()):
        v2, v3 = c2_by.get(p, 0), c3_by.get(p, 0)
        d = v3 - v2
        pc = (d / v2 * 100) if v2 else 0
        print(f"| {p} | {v2:.4f} | {v3:.4f} | {d:+.4f} | {pc:+.1f}% |")

    # === Audiobox ===
    for axis in ["production_quality", "content_enjoyment"]:
        r2_map = _nested_by_provider_uc(q2["audiobox_by_provider"], "audiobox_means", axis)
        r3_map = _nested_by_provider_uc(q3["audiobox_by_provider"], "audiobox_means", axis)
        compare_signal(f"AB.{'PQ' if 'production' in axis else 'CE'}", r2_map, r3_map)
        print(f"\n**Top-1 flip check ({'AB.PQ' if 'production' in axis else 'AB.CE'}):**")
        top1_per_signal(r2_map, r3_map, higher_is_better=True)
        print(f"\n**Rank stability (Spearman ρ R2 vs R3):**")
        for uc, sp in spearman_rank(r2_map, r3_map).items():
            if sp is None:
                print(f"  {uc}: (insufficient overlap)")
            else:
                rho, n, common = sp
                print(f"  {uc}: ρ = {rho:+.3f}  (n={n} vendors)")

    # === DNSMOS ===
    for axis in ["p808_mos", "ovrl_mos", "sig_mos", "bak_mos"]:
        r2_map = _nested_by_provider_uc(q2["dnsmos_by_provider"], "dnsmos_means", axis)
        r3_map = _nested_by_provider_uc(q3["dnsmos_by_provider"], "dnsmos_means", axis)
        compare_signal(f"DN.{axis.replace('_mos','')}", r2_map, r3_map)
        print(f"\n**Top-1 flip check (DN.{axis.replace('_mos','')}):**")
        top1_per_signal(r2_map, r3_map, higher_is_better=True)

    # === WER ===
    r2_wer = _by_provider_uc(w2["by_provider"], "agreement_wer_mean")
    r3_wer = _by_provider_uc(w3["by_provider"], "agreement_wer_mean")
    compare_signal("WER (agreement mean)", r2_wer, r3_wer, fmt="{:.4f}")
    print(f"\n**Top-1 flip check (WER, lower is better):**")
    top1_per_signal(r2_wer, r3_wer, higher_is_better=False)

    r2_fail = _by_provider_uc(w2["by_provider"], "failure_incidence_pct")
    r3_fail = _by_provider_uc(w3["by_provider"], "failure_incidence_pct")
    compare_signal("WER failure_incidence_pct", r2_fail, r3_fail, fmt="{:.1f}")

    # === Hygiene ===
    r2_clip = _by_provider_uc(h2["by_provider"], "total_clipped_samples")
    r3_clip = _by_provider_uc(h3["by_provider"], "total_clipped_samples")
    compare_signal("Hygiene: total clipped samples", r2_clip, r3_clip, fmt="{:.0f}")

    r2_nf = _by_provider_uc(h2["by_provider"], "mean_noise_floor_dbfs")
    r3_nf = _by_provider_uc(h3["by_provider"], "mean_noise_floor_dbfs")
    compare_signal("Hygiene: mean noise floor (dBFS)", r2_nf, r3_nf, fmt="{:.1f}")

    r2_sr = _by_provider_uc(h2["by_provider"], "mean_speech_ratio")
    r3_sr = _by_provider_uc(h3["by_provider"], "mean_speech_ratio")
    compare_signal("Hygiene: mean speech ratio", r2_sr, r3_sr, fmt="{:.3f}")

    # === F-8 cross-pipeline aggregate mean rho ===
    print(f"\n## F-8 (cross-pipeline mean Spearman ρ)")
    print("| Use case | R2 mean ρ | R3 mean ρ | Δ |")
    print("|---|---:|---:|---:|")
    r2_ucs = {b["use_case"]: b["cross_pipeline_mean_rho"] for b in x2["by_use_case"]}
    r3_ucs = {b["use_case"]: b["cross_pipeline_mean_rho"] for b in x3["by_use_case"]}
    for uc in sorted(r2_ucs.keys()):
        v2, v3 = r2_ucs.get(uc), r3_ucs.get(uc)
        d = (v3 - v2) if (v2 is not None and v3 is not None) else None
        print(f"| {uc} | {v2:+.3f} | {v3:+.3f} | {d:+.3f} |")

    # F-8 PQ vs DNSMOS mean and CE vs DNSMOS mean per use case
    print(f"\n### F-8 decomposition (PQ vs DNSMOS mean ρ, CE vs DNSMOS mean ρ per use case)")
    print("| Use case | Axis | R2 mean ρ | R3 mean ρ | Δ |")
    print("|---|---|---:|---:|---:|")
    for run_label, run in [("R2", x2), ("R3", x3)]:
        pass  # print below
    per = {}
    for run_label, run in [("R2", x2), ("R3", x3)]:
        for block in run["by_use_case"]:
            uc = block["use_case"]
            pq_dns = [row["rho"] for row in block["pairs"]
                      if "production_quality" in row.get("a","") + row.get("b","")
                      and "dnsmos" in row.get("a","") + row.get("b","")]
            ce_dns = [row["rho"] for row in block["pairs"]
                      if "content_enjoyment" in row.get("a","") + row.get("b","")
                      and "dnsmos" in row.get("a","") + row.get("b","")]
            per.setdefault(uc, {})[f"{run_label}_PQ"] = statistics.mean(pq_dns) if pq_dns else None
            per.setdefault(uc, {})[f"{run_label}_CE"] = statistics.mean(ce_dns) if ce_dns else None
    for uc in sorted(per.keys()):
        d = per[uc]
        for axis, key in [("PQ↔DNSMOS mean", "PQ"), ("CE↔DNSMOS mean", "CE")]:
            v2 = d.get(f"R2_{key}")
            v3 = d.get(f"R3_{key}")
            if v2 is not None and v3 is not None:
                delta = v3 - v2
                print(f"| {uc} | {axis} | {v2:+.3f} | {v3:+.3f} | {delta:+.3f} |")


if __name__ == "__main__":
    main()
