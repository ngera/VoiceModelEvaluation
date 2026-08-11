"""Frontier page - browse Phase G score outputs interactively.

Thin wrapper over the same functions `veval score` + `veval report` call.
Two panels:
    - Score: pick an analysis dir + BT fit, click Score -> writes score.json
    - Frontier: pick a use case + axis, view interactive Plotly chart
                with the survivor set, dominated set, and anchor
                distinguished. Robustness + correlations tables below.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from veval.report.charts import plotly_frontier
from veval.report.tables import (
    correlations_table, robustness_table, survivors_table,
)

load_dotenv()

st.set_page_config(page_title="Frontier - veval", page_icon="🏔️", layout="wide")
st.title("🏔️ Frontier")
st.caption(
    "Phase G scoring + interactive Pareto frontiers. Same functions as "
    "`veval score` + `veval report`."
)

# --- Load score.json ------------------------------------------------

score_path = Path(
    st.text_input("score.json path", value="analysis/score.json")
)
if not score_path.exists():
    st.warning(
        f"{score_path} not found. Generate it with `veval score` "
        "(or run the CLI from a terminal)."
    )
    st.stop()

score = json.loads(score_path.read_text(encoding="utf-8"))

st.divider()

# --- Frontier tabs --------------------------------------------------

tab_conv, tab_narr, tab_robust, tab_corr = st.tabs([
    "Conversational", "Narration", "Robustness", "Correlations",
])


def _render_frontier(use_case: str) -> None:
    frontiers = score.get("frontiers", {}).get(use_case, {})
    if not frontiers:
        st.info(f"No frontier data for {use_case} (needs BT fit + analyses).")
        return

    axis = st.radio(
        "Axis", options=["cost", "latency"], horizontal=True,
        key=f"axis_{use_case}",
    )
    fr = frontiers.get(axis)
    if not fr or not fr.get("points"):
        st.info(f"No {axis} frontier for {use_case}.")
        return

    fig = plotly_frontier(fr)
    st.plotly_chart(fig, use_container_width=True)

    # Point-level table
    df = pd.DataFrame(fr["points"])
    df["annotations"] = df["annotations"].apply(lambda a: "; ".join(a) if a else "")
    df = df[[
        "provider", "on_frontier", "y_strength", "y_ci_lower", "y_ci_upper",
        "x_value", "annotations",
    ]].sort_values("y_strength", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Dominations for this use case (from bt fit)
    if fr.get("dominations"):
        st.markdown("**Pairwise domination (CI-excludes-zero winners)**")
        dom_df = pd.DataFrame(fr["dominations"])
        st.dataframe(dom_df, use_container_width=True, hide_index=True)


with tab_conv:
    _render_frontier("conversational")

with tab_narr:
    _render_frontier("narration")

with tab_robust:
    st.markdown("**Robustness sweep** - do survivor sets flip when the "
                "gate threshold moves through its pre-registered sweep points?")
    st.markdown(robustness_table(score))
    st.caption(
        "`UNSTABLE` means the recommendation depends on your threshold "
        "choice; check whether the frontier composition survives "
        "movement inside its pre-registered range."
    )

with tab_corr:
    st.markdown("**Spearman rho** - rank agreement across quality axes.")
    st.markdown(correlations_table(score))

