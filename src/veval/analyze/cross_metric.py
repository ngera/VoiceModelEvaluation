"""Cross-metric agreement — Spearman ρ across the 6 quality signals.

Consumes `analysis/<run_id>/quality.json`. Pure function of the quality
aggregates; no audio or model calls.

Per use case, ranks the 8 providers on each of 6 signals (2 Audiobox axes
+ 4 DNSMOS axes) and computes the 6×6 Spearman ρ matrix. Purpose (spec
§4.3, RESEARCH_LOG F-8): quantify whether the two independent MOS
pipelines rank providers in the same order. High cross-pipeline ρ
strengthens the "6 signals, 2 independent pipelines" claim; low ρ is
itself the finding — the pipelines are measuring different things and
that becomes a threat to validity.

For DNSMOS on Cartesia, aggregates are computed over the *n_valid* files
(refusals excluded). Reported ranks are therefore over the subset that
the analyzer could score; the refusal rate itself is a separate signal
already reported in `quality.json` and F-4a.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

from scipy.stats import spearmanr

from .common import AnalysisWriter, RunReader

AUDIOBOX_AXES = ("production_quality", "content_enjoyment")
DNSMOS_AXES = ("p808_mos", "ovrl_mos", "sig_mos", "bak_mos")

# Signal id → (source, axis). Signal id is what appears in the output;
# stable and short so downstream tables stay readable.
SIGNALS: list[tuple[str, str, str]] = [
    ("audiobox.PQ", "audiobox", "production_quality"),
    ("audiobox.CE", "audiobox", "content_enjoyment"),
    ("dnsmos.p808", "dnsmos", "p808_mos"),
    ("dnsmos.ovrl", "dnsmos", "ovrl_mos"),
    ("dnsmos.sig",  "dnsmos", "sig_mos"),
    ("dnsmos.bak",  "dnsmos", "bak_mos"),
]


def _rows_by_provider(rows: list[dict[str, Any]], use_case: str, means_key: str,
                       ) -> dict[str, dict[str, float]]:
    """Return {provider: {axis: mean, ...}} for one use_case slice."""
    out: dict[str, dict[str, float]] = {}
    for r in rows:
        if r.get("use_case") != use_case:
            continue
        out[r["provider"]] = dict(r.get(means_key, {}))
    return out


def _rank_desc(values: dict[str, float]) -> dict[str, float]:
    """Rank providers high-to-low (rank 1 = best). Tied values get the
    average rank — matches Spearman's tie handling."""
    # Sort providers high-to-low
    items = sorted(values.items(), key=lambda kv: (-kv[1], kv[0]))
    n = len(items)
    ranks: dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        # Find span of ties
        while j + 1 < n and items[j + 1][1] == items[i][1]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-indexed average rank
        for k in range(i, j + 1):
            ranks[items[k][0]] = avg
        i = j + 1
    return ranks


def run(run_dir: Path, *, writer: AnalysisWriter,
        quality_analysis_path: Path | None = None) -> dict[str, Any]:
    """Compute per-use-case rank tables and Spearman ρ matrices.

    Reads quality.json (default: `writer.dir / quality.json`; override
    with `quality_analysis_path` for tests). Emits cross_metric.json.
    """
    import json

    reader = RunReader(run_dir)  # validate manifest exists
    manifest = reader.manifest()

    qpath = quality_analysis_path or (writer.dir / "quality.json")
    if not qpath.exists():
        raise FileNotFoundError(
            f"cross_metric requires quality.json first; not found at {qpath}"
        )
    q = json.loads(qpath.read_text(encoding="utf-8"))

    ab_rows = q.get("audiobox_by_provider", [])
    dn_rows = q.get("dnsmos_by_provider", [])
    use_cases = sorted({r["use_case"] for r in ab_rows} | {r["use_case"] for r in dn_rows})

    per_use_case: list[dict[str, Any]] = []
    for uc in use_cases:
        ab = _rows_by_provider(ab_rows, uc, "audiobox_means")
        dn = _rows_by_provider(dn_rows, uc, "dnsmos_means")
        providers = sorted(set(ab) | set(dn))

        # Build the value matrix: provider × signal, dropping providers
        # missing any signal (n_valid=0 case). Should be zero drops on a
        # clean campaign run.
        rows_kept: list[str] = []
        by_signal: dict[str, list[float]] = {sid: [] for sid, _, _ in SIGNALS}
        for prov in providers:
            values = []
            ok = True
            for _sid, source, axis in SIGNALS:
                src = ab if source == "audiobox" else dn
                v = src.get(prov, {}).get(axis)
                if v is None:
                    ok = False
                    break
                values.append(v)
            if not ok:
                continue
            rows_kept.append(prov)
            for (sid, _s, _a), v in zip(SIGNALS, values):
                by_signal[sid].append(v)

        # Ranks per signal (for the readable table)
        ranks_by_signal: dict[str, dict[str, float]] = {}
        for sid, source, axis in SIGNALS:
            src = ab if source == "audiobox" else dn
            values = {p: src[p][axis] for p in rows_kept}
            ranks_by_signal[sid] = _rank_desc(values)

        # 6 × 6 Spearman ρ matrix (over rows_kept)
        signal_ids = [sid for sid, _, _ in SIGNALS]
        rho_matrix: dict[str, dict[str, float]] = {sid: {} for sid in signal_ids}
        pairs_summary: list[dict[str, Any]] = []
        for a, b in combinations(signal_ids, 2):
            va = by_signal[a]
            vb = by_signal[b]
            if len(va) < 3:
                rho = float("nan")
                pval = float("nan")
            else:
                res = spearmanr(va, vb)
                rho = float(res.statistic)
                pval = float(res.pvalue)
            rho_matrix[a][b] = rho
            rho_matrix[b][a] = rho
            pairs_summary.append({"a": a, "b": b, "rho": rho, "p_value": pval})
        for sid in signal_ids:
            rho_matrix[sid][sid] = 1.0

        # Cross-pipeline pairs (Audiobox × DNSMOS) — the headline number
        ab_ids = [sid for sid, s, _ in SIGNALS if s == "audiobox"]
        dn_ids = [sid for sid, s, _ in SIGNALS if s == "dnsmos"]
        cross_pairs = [(a, b) for a in ab_ids for b in dn_ids]
        cross_rhos = [rho_matrix[a][b] for a, b in cross_pairs
                       if rho_matrix[a][b] == rho_matrix[a][b]]  # not nan
        cross_mean = sum(cross_rhos) / len(cross_rhos) if cross_rhos else float("nan")

        per_use_case.append({
            "use_case": uc,
            "providers_ranked": rows_kept,
            "n_providers": len(rows_kept),
            "ranks_by_signal": ranks_by_signal,
            "spearman_matrix": rho_matrix,
            "pairs": pairs_summary,
            "cross_pipeline_mean_rho": cross_mean,
        })

    payload: dict[str, Any] = {
        "run_id": manifest.get("run_id", run_dir.name),
        "signals": [{"id": sid, "source": s, "axis": a} for sid, s, a in SIGNALS],
        "by_use_case": per_use_case,
    }
    writer.write_json("cross_metric.json", payload)
    return payload
