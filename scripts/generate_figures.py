"""Generate the 3 portfolio figures from analysis outputs.

Reads:
    analysis/campaign-20260809T204608Z/cross_metric.json  (Spearman + ranks)
    analysis/campaign-20260809T204608Z/quality.json       (per-provider means)
    analysis/campaign-20260809T204608Z/cost_model.json    (cost tiers)
    analysis/latency-20260809T214106Z/latency.json        (session 1 TTFA)
    analysis/latency-20260811T183028Z/latency.json        (session 2 OpenAI)
    analysis/latency-20260811T183202Z/latency.json        (session 2 ElevenLabs)

Writes:
    documentation/figures/f1_rank_inversion.png
    documentation/figures/f2_cost_vs_quality.png
    documentation/figures/f3_latency_stability.png

Run: `uv run python scripts/generate_figures.py`
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CAMPAIGN = "campaign-20260809T204608Z"
LAT_S1 = "latency-20260809T214106Z"
LAT_S2_OAI = "latency-20260811T183028Z"
LAT_S2_EL = "latency-20260811T183202Z"

FIG_DIR = Path("documentation/figures")

# Consistent per-provider colour so the same colour = same vendor across
# all figures. Speechify: purple; ElevenLabs: red; OpenAI: green; Cartesia:
# orange; Deepgram: teal; Google: yellow; Fish: pink; Orpheus: brown.
PROVIDER_COLOR = {
    "speechify": "#8e44ad",
    "elevenlabs": "#e74c3c",
    "openai": "#27ae60",
    "cartesia": "#e67e22",
    "deepgram": "#16a085",
    "google": "#f1c40f",
    "fish": "#e91e63",
    "orpheus": "#795548",
}
PROVIDER_ORDER = ["speechify", "openai", "elevenlabs", "orpheus",
                   "deepgram", "google", "cartesia", "fish"]


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- figure 1

def figure_1_rank_inversion() -> None:
    """Slope/dumbbell chart per use case. For each provider, plot two dots
    on a shared rank axis (1=best): one for Audiobox PQ rank, one for
    DNSMOS OVRL rank. Connect them with a coloured segment — red for a
    3+ rank swing (real inversion), grey for tight agreement. Provider
    order is by Audiobox rank (left panel) then DNSMOS rank (right)."""

    c = _load(f"analysis/{CAMPAIGN}/cross_metric.json")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)

    for ax, uc_row, title in zip(
        axes, c["by_use_case"],
        ["Conversational", "Narration"],
    ):
        ranks_ab = uc_row["ranks_by_signal"]["audiobox.PQ"]
        ranks_dn = uc_row["ranks_by_signal"]["dnsmos.ovrl"]
        provs = sorted(ranks_ab.keys(), key=lambda p: ranks_ab[p])

        x_ab = 0.0
        x_dn = 1.0

        for i, prov in enumerate(provs):
            r_ab = ranks_ab[prov]
            r_dn = ranks_dn[prov]
            gap = abs(r_ab - r_dn)

            # Segment colour signals inversion severity
            if gap >= 4:
                seg_color = "#c0392b"
                seg_lw = 3.0
                seg_alpha = 0.85
            elif gap >= 2:
                seg_color = "#e67e22"
                seg_lw = 2.0
                seg_alpha = 0.75
            else:
                seg_color = "#bdc3c7"
                seg_lw = 1.2
                seg_alpha = 0.55

            ax.plot([x_ab, x_dn], [r_ab, r_dn],
                     color=seg_color, lw=seg_lw, alpha=seg_alpha, zorder=2,
                     solid_capstyle="round")

            # Dots
            ax.scatter([x_ab], [r_ab], s=180, color="#3498db",
                        edgecolor="#2c3e50", linewidths=1.0, zorder=4)
            ax.scatter([x_dn], [r_dn], s=180, color="#f39c12",
                        edgecolor="#2c3e50", linewidths=1.0, zorder=4)

            # Provider name at the Audiobox end
            ax.annotate(prov, (x_ab, r_ab), xytext=(-10, 0),
                         textcoords="offset points", ha="right", va="center",
                         fontsize=10, weight="bold" if gap >= 4 else "normal",
                         color="#c0392b" if gap >= 4 else "#2c3e50")

            # Rank number at DNSMOS end if inverted (so reader can quickly
            # read "OpenAI: 8 → 1" for the perfect inversion)
            if gap >= 4:
                ax.annotate(f"{int(r_ab)}→{int(r_dn)}",
                             (x_dn, r_dn), xytext=(12, 0),
                             textcoords="offset points", ha="left",
                             va="center", fontsize=9, weight="bold",
                             color="#c0392b")

        # Axis labels at the top
        ax.text(x_ab, -0.5, "Audiobox PQ\n(warm rater)", ha="center", va="bottom",
                 fontsize=10, weight="bold", color="#3498db")
        ax.text(x_dn, -0.5, "DNSMOS OVRL\n(clean rater)", ha="center", va="bottom",
                 fontsize=10, weight="bold", color="#f39c12")

        ax.set_xlim(-0.55, 1.55)
        ax.invert_yaxis()  # rank 1 at top
        ax.set_ylim(9, 0)
        ax.set_yticks(range(1, 9))
        ax.set_ylabel("Rank of 8 (1 = best)" if ax is axes[0] else "")
        ax.set_title(title, fontsize=13, weight="bold", pad=32)
        ax.set_xticks([])
        for spine in ("top", "right", "bottom"):
            ax.spines[spine].set_visible(False)

        rho = uc_row["cross_pipeline_mean_rho"]
        ax.text(0.5, -0.14, f"cross-pipeline mean Spearman $\\rho$ = {rho:+.3f}",
                transform=ax.transAxes, ha="center", fontsize=10,
                style="italic", color="#7f8c8d")

    fig.suptitle(
        "Two independent MOS pipelines rank vendors differently\n"
        "Red slopes = 4+ rank swing between the pipelines. "
        "OpenAI on narration flips from #8 warm to #1 clean.",
        fontsize=12, y=1.00,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = FIG_DIR / "f1_rank_inversion.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- figure 2

def figure_2_cost_vs_quality() -> None:
    """2x2 grid — rows are rater (warm=Audiobox PQ, clean=DNSMOS OVRL),
    columns are use case. Each panel: cost per 1K words (log x) vs
    quality score (y), 8 dots labelled by vendor. Highlights the
    tied-on-quality outcomes where cost decides — especially the
    DNSMOS 'clean' row where OpenAI is tied for #1 at ~3x discount."""

    q = _load(f"analysis/{CAMPAIGN}/quality.json")
    c_mod = _load(f"analysis/{CAMPAIGN}/cost_model.json")

    cost_by_prov = {p["provider"]: p.get("dollars_per_1k_words_at", {}).get("100K_words_per_month")
                     for p in c_mod["providers"]}

    ab_by_key = {(r["provider"], r["use_case"]): r["audiobox_means"] for r in q["audiobox_by_provider"]}
    dn_by_key = {(r["provider"], r["use_case"]): r["dnsmos_means"] for r in q["dnsmos_by_provider"]}

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    panels = [
        (axes[0][0], "production_quality", "conversational", ab_by_key,
         "Warm rater — Conversational", "Audiobox PQ (0-10)"),
        (axes[0][1], "production_quality", "narration",      ab_by_key,
         "Warm rater — Narration",      "Audiobox PQ (0-10)"),
        (axes[1][0], "ovrl_mos",           "conversational", dn_by_key,
         "Clean rater — Conversational", "DNSMOS OVRL (MOS 1-5)"),
        (axes[1][1], "ovrl_mos",           "narration",      dn_by_key,
         "Clean rater — Narration",      "DNSMOS OVRL (MOS 1-5)"),
    ]

    for ax, axis_id, uc, source, title, y_label in panels:
        points = []
        for prov in PROVIDER_ORDER:
            cost = cost_by_prov.get(prov)
            v = source.get((prov, uc), {}).get(axis_id)
            if cost is None or v is None:
                continue
            points.append((prov, cost, v))
            ax.scatter(cost, v, s=260, color=PROVIDER_COLOR[prov],
                        edgecolor="#2c3e50", linewidths=1.0,
                        alpha=0.95, zorder=3)

        # Label placement: manual anti-collision — sort by cost, alternate
        # up/down offsets when neighbours are within 20% of each other on x
        # and within 5% of the y-range on y.
        y_vals = [p[2] for p in points]
        y_min, y_max = min(y_vals), max(y_vals)
        y_range = y_max - y_min if y_max > y_min else 1
        sorted_pts = sorted(points, key=lambda p: p[1])
        last_placed_y = None
        alt = 1
        for prov, cost, v in sorted_pts:
            dy = 14
            if last_placed_y is not None and abs(v - last_placed_y) < 0.15 * y_range:
                dy = 14 if alt == 1 else -18
                alt = -alt
            ax.annotate(prov, (cost, v), xytext=(8, dy),
                         textcoords="offset points", fontsize=10,
                         color=PROVIDER_COLOR[prov], weight="bold")
            last_placed_y = v

        ax.set_xscale("log")
        ax.set_xlabel("Cost per 1K words ($) — 100K wpm tier · log scale", fontsize=9)
        ax.set_ylabel(y_label, fontsize=10)
        ax.set_title(title, fontsize=12, weight="bold")
        ax.grid(True, which="both", alpha=0.25, lw=0.5)
        # Give room for labels
        pad = y_range * 0.15
        ax.set_ylim(y_min - pad, y_max + pad)
        ax.set_xlim(cost_by_prov["orpheus"] * 0.5,
                     max(v for v in cost_by_prov.values() if v) * 1.5)

    fig.suptitle(
        "Cost vs quality — which #1 is actually worth the money?\n"
        "TOP row (warm): Speechify is #1 AND cheapest on the paid tier — rare win-win.\n"
        "BOTTOM row (clean): the top 2 are essentially tied on quality; OpenAI at $0.075 beats ElevenLabs at $0.22 (3x saving).",
        fontsize=12, y=1.00,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = FIG_DIR / "f2_cost_vs_quality.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- figure 3

LAT_S3_OAI = "latency-20260812T191143Z"
LAT_S3_EL = "latency-20260812T191323Z"


def figure_3_latency_stability() -> None:
    """3-session TTFA per vendor. S3 added 2026-08-12 with concurrent
    ping baseline (see F-11) — refuted the original 2-session
    stability finding. Figure shows all three sessions per vendor
    with the range annotation."""

    s1 = _load(f"analysis/{LAT_S1}/latency.json")
    s2_oai = _load(f"analysis/{LAT_S2_OAI}/latency.json")
    s2_el = _load(f"analysis/{LAT_S2_EL}/latency.json")
    s3_oai = _load(f"analysis/{LAT_S3_OAI}/latency.json")
    s3_el = _load(f"analysis/{LAT_S3_EL}/latency.json")

    def _extract(doc: dict, provider: str) -> dict:
        for r in doc["by_provider"]:
            if r["provider"] == provider and r.get("n_with_ttfa"):
                return {
                    "p50": r["ttfa_p50_ms"], "p90": r["ttfa_p90_ms"],
                    "min": r["ttfa_min_ms"], "max": r["ttfa_max_ms"],
                    "n": r["n_with_ttfa"],
                }
        return {}

    oai = [_extract(s1, "openai"), _extract(s2_oai, "openai"), _extract(s3_oai, "openai")]
    el = [_extract(s1, "elevenlabs"), _extract(s2_el, "elevenlabs"), _extract(s3_el, "elevenlabs")]

    fig, ax = plt.subplots(figsize=(12, 6))

    y_openai = 1.0
    y_eleven = 0.4

    session_colors = ["#27ae60", "#f39c12", "#c0392b"]  # green / amber / red
    session_labels = ["S1 · 2026-08-09", "S2 · 2026-08-11", "S3 · 2026-08-12 (+ ping baseline)"]
    session_offsets = [0.12, 0.0, -0.12]

    def _plot_session(y: float, data: dict, color: str, label: str | None,
                       label_dy: int = 14) -> None:
        ax.plot([data["min"], data["max"]], [y, y],
                 color=color, lw=1.2, alpha=0.4, solid_capstyle="round")
        ax.plot([data["p50"], data["p90"]], [y, y],
                 color=color, lw=6, alpha=0.55, solid_capstyle="round")
        ax.scatter([data["p50"]], [y], s=140, marker="o",
                    color=color, edgecolor="#2c3e50", linewidths=0.8,
                    zorder=5, label=label)
        ax.annotate(f"p50 {data['p50']:.0f} · p90 {data['p90']:.0f}",
                     (data["p50"], y), xytext=(-6, label_dy),
                     textcoords="offset points",
                     ha="right", fontsize=8.5, color=color, weight="bold")

    for i, (data, color, label, dy) in enumerate(zip(
        oai, session_colors, session_labels, [14, 14, -18],
    )):
        _plot_session(y_openai + session_offsets[i], data, color, label if i < 3 else None, label_dy=dy)
    for i, (data, color, dy) in enumerate(zip(
        el, session_colors, [14, 14, -18],
    )):
        _plot_session(y_eleven + session_offsets[i], data, color, None, label_dy=dy)

    # Range annotations
    oai_p50_range = max(d["p50"] for d in oai) - min(d["p50"] for d in oai)
    el_p50_range = max(d["p50"] for d in el) - min(d["p50"] for d in el)
    ax.text(2200, y_openai,
             f"p50 range: {min(d['p50'] for d in oai):.0f}–{max(d['p50'] for d in oai):.0f} ms\n"
             f"(+{100*oai_p50_range/min(d['p50'] for d in oai):.0f}% max shift)",
             ha="left", va="center", fontsize=9, weight="bold", color="#c0392b")
    ax.text(1200, y_eleven,
             f"p50 range: {min(d['p50'] for d in el):.0f}–{max(d['p50'] for d in el):.0f} ms\n"
             f"(+{100*el_p50_range/min(d['p50'] for d in el):.0f}% max shift)",
             ha="left", va="center", fontsize=9, weight="bold", color="#c0392b")

    # Sub-500 ms line
    ax.axvline(500, color="#3498db", lw=1.2, ls="--", alpha=0.5, zorder=1)
    ax.text(500, 1.55, " sub-500ms\n (real-time voice threshold)",
             color="#3498db", fontsize=9, va="top")

    # Ping baseline annotation
    ax.text(2100, 1.55,
             "S3 concurrent ping (1.1.1.1):\np50=8ms · p90=12ms · max=29ms\n(ISP was clean during S3)",
             ha="left", va="top", fontsize=8.5, color="#7f8c8d", style="italic")

    ax.set_yticks([y_openai, y_eleven])
    ax.set_yticklabels(["OpenAI\n(tts-1-hd)", "ElevenLabs\n(Flash v2.5)"],
                        fontsize=11, weight="bold")
    ax.set_xlabel("Time-to-first-audio-frame (ms) — 50 trials per session, S01 corpus item")
    ax.set_title("Three-session TTFA per vendor — S3 refuted the 'ElevenLabs is stable' finding (F-11)\n"
                  "Bold band = p50→p90. Thin line = min→max. Ranking preserved; absolute values shift 50-90% session-to-session.",
                  fontsize=11)
    ax.grid(True, axis="x", alpha=0.25, lw=0.5)
    ax.set_xlim(300, 3800)
    ax.set_ylim(0.15, 1.65)
    ax.legend(loc="upper right", frameon=True, fontsize=9, bbox_to_anchor=(0.98, 0.98))

    fig.tight_layout()
    out = FIG_DIR / "f3_latency_stability.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure_1_rank_inversion()
    figure_2_cost_vs_quality()
    figure_3_latency_stability()
    print(f"\nall figures in {FIG_DIR}/")


if __name__ == "__main__":
    main()
