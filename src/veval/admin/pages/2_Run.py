"""Admin panel — Run page.

Thin wrapper over `veval.runner.Runner` — same as `veval generate`.
CLAUDE.md convention: never duplicate the CLI logic here.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from veval.config import load_pricing, load_providers, load_voices
from veval.runner import RunMode, Runner, RunSummary, SpendTracker, SynthesisCache

load_dotenv()

st.set_page_config(page_title="Run — veval", page_icon="🎙️", layout="wide")
st.title("🎙️ Run")
st.caption("Same as `veval generate` from the CLI — pick mode, filters, run.")

# --- Sidebar: config paths (advanced) ---
with st.sidebar:
    st.header("Config paths")
    providers_file = st.text_input("providers.yaml", value="configs/providers.yaml")
    voices_file = st.text_input("voices.yaml", value="configs/voices.yaml")
    corpus_dir = st.text_input("corpus dir", value="corpus")
    pricing_file = st.text_input("pricing.yaml", value="configs/pricing.yaml")
    cache_dir = st.text_input("cache dir", value=".cache/synthesis")

# --- Load configs for the pickers ---
try:
    providers = load_providers(Path(providers_file))
    voices = load_voices(Path(voices_file))
    pricing = load_pricing(Path(pricing_file))
except Exception as e:  # noqa: BLE001
    st.error(f"Config load failed: {e}")
    st.stop()

# --- Mode selector ---
col_l, col_r = st.columns([1, 2])
with col_l:
    mode_str = st.radio(
        "Mode",
        options=["campaign", "variance", "latency"],
        index=0,
        help=(
            "campaign: one call per (provider, use_case, item). Cache enabled.\n"
            "variance: 10 items × N draws for noise floor. Cache OFF.\n"
            "latency:  50 serial trials per provider on one item. Cache OFF, Orpheus skipped."
        ),
    )
    parsed_mode = RunMode(mode_str)

with col_r:
    st.markdown("**Provider filter**")
    selected_providers = st.multiselect(
        "Providers (empty = all)",
        options=sorted(p.name for p in providers.providers),
        default=[],
        label_visibility="collapsed",
    )

# --- Mode-specific controls ---
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Use cases**")
    selected_use_cases = st.multiselect(
        "Use cases (empty = both)",
        options=["conversational", "narration"],
        default=[],
        label_visibility="collapsed",
    )

with c2:
    if parsed_mode == RunMode.campaign:
        st.markdown("**Items (pilot filter)**")
        items_raw = st.text_input(
            "Items (comma-separated, e.g. S01,M01,L01)",
            value="",
            label_visibility="collapsed",
        )
        items = [s.strip() for s in items_raw.split(",") if s.strip()] or None
    elif parsed_mode == RunMode.variance:
        st.markdown("**Variance draws**")
        n_draws = st.number_input(
            "n_draws", min_value=2, max_value=10, value=3,
            label_visibility="collapsed",
        )
        items = None
    else:  # latency
        st.markdown("**Latency item**")
        latency_item = st.text_input(
            "item_id", value="S01", label_visibility="collapsed",
        )
        items = None

with c3:
    if parsed_mode == RunMode.latency:
        st.markdown("**Trials per provider**")
        trials = st.number_input(
            "trials", min_value=1, max_value=200, value=50,
            label_visibility="collapsed",
        )

# --- Safety toggles ---
st.divider()
sa, sb, sc = st.columns(3)
with sa:
    no_cache = st.toggle(
        "Disable cache",
        value=False,
        help="Cache is off automatically for variance + latency modes.",
    )
with sb:
    no_spend_cap = st.toggle(
        "Disable spend cap", value=False,
        help="Recommended OFF — leave the cap on unless you know what you're doing.",
    )
with sc:
    spend_cap_str = st.text_input(
        "Spend cap USD (blank = default from env)",
        value="",
        help="Overrides VEVAL_SPEND_CAP_USD",
    )
    spend_cap_override: float | None = None
    if spend_cap_str.strip():
        try:
            spend_cap_override = float(spend_cap_str)
        except ValueError:
            st.warning("Spend cap must be a number; using env default")

st.divider()

# --- Run button ---
if st.button("▶  Run", type="primary"):
    cache = None if (no_cache or parsed_mode != RunMode.campaign) else SynthesisCache(Path(cache_dir))
    tracker = None if no_spend_cap else SpendTracker.from_env(pricing=pricing, cap_usd_override=spend_cap_override)

    runner = Runner(
        providers_file=Path(providers_file),
        voices_file=Path(voices_file),
        corpus_dir=Path(corpus_dir),
        pricing_file=Path(pricing_file),
        cache=cache,
        spend_tracker=tracker,
    )

    with st.status(f"Running {parsed_mode.value}...", expanded=True) as status:
        try:
            if parsed_mode == RunMode.campaign:
                summary = runner.run_campaign(
                    use_cases=selected_use_cases or None,  # type: ignore[arg-type]
                    provider_names=selected_providers or None,
                    item_ids=items,
                )
            elif parsed_mode == RunMode.variance:
                summary = runner.run_variance(
                    use_cases=selected_use_cases or None,  # type: ignore[arg-type]
                    provider_names=selected_providers or None,
                    n_draws=int(n_draws),
                )
            else:  # latency
                latency_uc = (selected_use_cases[0] if selected_use_cases else "conversational")
                summary = runner.run_latency(
                    provider_names=selected_providers or None,
                    use_case=latency_uc,  # type: ignore[arg-type]
                    item_id=latency_item,
                    trials=int(trials),
                )
            status.update(label=f"{parsed_mode.value} finished in {summary.elapsed_s:.1f}s", state="complete")
        except Exception as e:  # noqa: BLE001
            status.update(label=f"Runner error: {e}", state="error")
            st.exception(e)
            st.stop()

    # --- Summary ---
    st.divider()
    st.subheader("Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", summary.total)
    m2.metric("OK", summary.ok)
    m3.metric("Failed", summary.failed)
    m4.metric("Elapsed", f"{summary.elapsed_s:.1f}s")

    st.caption(f"Run dir: `{summary.run_dir}`")

    st.markdown("**Per provider**")
    provider_rows = sorted(set(summary.per_provider_ok) | set(summary.per_provider_failed))
    if provider_rows:
        st.dataframe(
            [
                {
                    "provider": p,
                    "ok": summary.per_provider_ok.get(p, 0),
                    "failed": summary.per_provider_failed.get(p, 0),
                }
                for p in provider_rows
            ],
            hide_index=True,
        )

    if tracker is not None:
        st.markdown("**Estimated spend (USD)**")
        spend_rows = [
            {"provider": p, "spend_usd": round(usd, 4)}
            for p, usd in sorted(tracker.per_provider_usd.items())
        ]
        spend_rows.append({"provider": "TOTAL", "spend_usd": round(tracker.total_usd, 4)})
        st.dataframe(spend_rows, hide_index=True)
        st.caption(f"Cap: ${tracker.cap_usd:.2f}")
