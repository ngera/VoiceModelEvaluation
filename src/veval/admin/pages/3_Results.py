"""Results page — browse Phase E analyzer outputs for one run.

Thin wrapper over the same functions `veval analyze` calls (CLAUDE.md
convention). Pick a run, pick stages, click run, browse results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from veval.analyze import (
    acceptance,
    cost,
    drift,
    hygiene,
    latency,
    quality,
    variance,
    wer,
)
from veval.analyze.common import AnalysisWriter
from veval.config import load_analyzers, load_corpus, load_gates
from veval.store.run_store import default_run_store

load_dotenv()

st.set_page_config(page_title="Results — veval", page_icon="📊", layout="wide")
st.title("📊 Results")
st.caption("Same analyzers as `veval analyze`. Reads from `runs/<run_id>/`, writes `analysis/<run_id>/`.")


# --- Run picker ------------------------------------------------------


runs = default_run_store().list_runs()
if not runs:
    st.warning("No runs under ./runs/. Generate audio first: `veval generate` or the Run page.")
    st.stop()

run_labels = [f"{p.name}" for p in runs]
selected_label = st.selectbox("Run", options=run_labels)
run_dir = next(p for p in runs if p.name == selected_label)

analysis_dir = Path("analysis") / run_dir.name

col_l, col_r = st.columns([2, 1])
with col_l:
    stages = st.multiselect(
        "Stages to run",
        options=["acceptance", "hygiene", "latency", "cost", "wer", "quality", "variance", "drift"],
        default=["acceptance", "hygiene", "latency", "cost"],
        help="wer + quality download models on first run (~4-8 GB).",
    )
with col_r:
    skip_ttsds = st.checkbox("Skip TTSDS2 inside quality", value=False)
    skip_audiobox = st.checkbox("Skip Audiobox inside quality", value=False)

run_clicked = st.button("Run analyzers", type="primary", disabled=not stages)

# --- Execution -------------------------------------------------------


def _load_json(name: str) -> dict[str, Any] | None:
    p = analysis_dir / name
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


if run_clicked:
    writer = AnalysisWriter(run_dir.name, base_dir=Path("analysis"))
    gates = load_gates(Path("configs/gates.yaml"))
    with st.status("Running analyzers...", expanded=True) as status:
        if "acceptance" in stages:
            st.write("acceptance…")
            acceptance.run(run_dir, writer=writer)
        if "hygiene" in stages:
            st.write("hygiene…")
            hygiene.run(run_dir, gates=gates, writer=writer)
        if "latency" in stages:
            st.write("latency…")
            latency.run(run_dir, writer=writer)
        if "cost" in stages:
            st.write("cost…")
            cost.run(run_dir, pricing_path=Path("configs/pricing.yaml"), writer=writer)
        if "wer" in stages:
            st.write("wer (downloads models on first run)…")
            analyzers = load_analyzers(Path("configs/analyzers.yaml"))
            corpus_by_uc = {}
            for uc in ("conversational", "narration"):
                p = Path("corpus") / f"{uc}.yaml"
                if p.exists():
                    corpus_by_uc[uc] = load_corpus(p)
            wer.run(run_dir, gates=gates, analyzers=analyzers,
                    corpus_by_use_case=corpus_by_uc, writer=writer)
        if "quality" in stages:
            st.write("quality (TTSDS2 + Audiobox)…")
            analyzers = load_analyzers(Path("configs/analyzers.yaml"))
            quality.run(run_dir, analyzers=analyzers,
                        compute_ttsds=not skip_ttsds,
                        compute_audiobox=not skip_audiobox, writer=writer)
        if "variance" in stages:
            st.write("variance…")
            wer_p = analysis_dir / "wer.json"
            q_p = analysis_dir / "quality.json"
            variance.run(run_dir, gates=gates,
                         wer_analysis_path=wer_p if wer_p.exists() else None,
                         quality_analysis_path=q_p if q_p.exists() else None, writer=writer)
        if "drift" in stages:
            st.write("drift…")
            drift.run(run_dir, gates=gates, writer=writer)
        status.update(label="Analyzers complete", state="complete", expanded=False)


# --- Result tabs -----------------------------------------------------

if not analysis_dir.exists():
    st.info("No analysis outputs yet — click **Run analyzers** above.")
    st.stop()

tab_names = ["Acceptance", "Hygiene", "Latency", "Cost", "WER", "Quality", "Variance", "Drift"]
tabs = st.tabs(tab_names)


def _render_by_provider(payload: dict[str, Any] | None, key: str = "by_provider") -> None:
    if not payload or key not in payload:
        st.info("Not run yet.")
        return
    df = pd.DataFrame(payload[key])
    st.dataframe(df, use_container_width=True, hide_index=True)


with tabs[0]:
    st.markdown("**WAV acceptance gate** — catches header/decode/LUFS/VAD/chars regressions before analysis")
    p = _load_json("acceptance.json")
    if p:
        st.metric(
            "Gate",
            "PASS" if p["gate_ok"] else "FAIL",
            f"{p['passed']} / {p['total_files']} files pass",
        )
        st.dataframe(pd.DataFrame(p["files"]), use_container_width=True, hide_index=True)
    else:
        st.info("Not run yet.")

with tabs[1]:
    st.markdown("**Hygiene** — clipping, LUFS, noise floor, pauses")
    p = _load_json("hygiene.json")
    _render_by_provider(p)
    if p:
        with st.expander("Per-file"):
            st.dataframe(pd.DataFrame(p["files"]), use_container_width=True, hide_index=True)

with tabs[2]:
    st.markdown("**Latency** — TTFA percentiles + RTF on long items")
    p = _load_json("latency.json")
    if p:
        ctx = p.get("context", {})
        st.caption(
            f"run kind: `{ctx.get('kind')}` · TTFA captured by mode: "
            f"`{ctx.get('ttfa_captured_by_mode')}` (latency-mode only)"
        )
    _render_by_provider(p)

with tabs[3]:
    st.markdown("**Cost** — pricing × observed chars, projected at 10K/100K/1M words/month")
    p = _load_json("cost_model.json")
    if p:
        st.metric("Total observed spend (USD)", f"${p['total_observed_cost_usd']:.4f}")
    _render_by_provider(p, key="providers")

with tabs[4]:
    st.markdown("**WER** — two-judge agreement, failure incidence, band, catastrophic events")
    p = _load_json("wer.json")
    _render_by_provider(p)
    if p:
        st.caption(f"normaliser: `{p['normaliser']}` · hash: `{p['normaliser_hash'][:16]}…`")
        with st.expander("Per-item transcripts"):
            st.dataframe(pd.DataFrame(p["items"]), use_container_width=True, hide_index=True)

with tabs[5]:
    st.markdown("**Quality** — TTSDS2 + Audiobox (PQ + CE)")
    p = _load_json("quality.json")
    if p:
        st.caption(f"axes reported: {p['audiobox_axes_reported']}")
        if p.get("ttsds_by_provider"):
            st.markdown("### TTSDS2")
            st.dataframe(pd.DataFrame(p["ttsds_by_provider"]),
                         use_container_width=True, hide_index=True)
        if p.get("audiobox_by_provider"):
            st.markdown("### Audiobox")
            st.dataframe(pd.DataFrame(p["audiobox_by_provider"]),
                         use_container_width=True, hide_index=True)
    else:
        st.info("Not run yet.")

with tabs[6]:
    st.markdown("**Variance** — noise floor + determinism (byte-identity across draws)")
    p = _load_json("variance.json")
    if p:
        st.caption(f"z_multiplier = {p['z_multiplier']} · scope = {p['measurement_noise_floor_scope']}")
    _render_by_provider(p)

with tabs[7]:
    st.markdown("**Drift** — per-third LUFS/dBFS on long narration items → monotonic-degradation flag")
    p = _load_json("drift.json")
    _render_by_provider(p)
    if p and p.get("items"):
        with st.expander("Per-item thirds"):
            st.dataframe(pd.DataFrame(p["items"]), use_container_width=True, hide_index=True)
