"""Chart layer: Plotly (interactive) + Altair (static PNG).

Convention (chosen 2026-08-08):
    - Plotly figures for the Streamlit admin page. Hover tooltips reveal
      per-provider CI details; click-to-select filters the annotations.
    - Altair PNG for the case study markdown. Frozen-in-time, embeds
      cleanly in memo templates, no runtime dependency on a browser.

Both back-ends consume the SAME normalized payload from a UseCaseFrontier
so the two views can't diverge.

Chart contract:
    - Y axis: BT strength with vertical error bars (CI lo, hi).
    - X axis: $/1K words (cost frontier) OR TTFA p90 ms (latency frontier).
    - Marker style: filled for on-frontier, hollow for dominated.
    - Anchor point: distinct color/shape ("human anchor (reference)").
    - Text labels on every point (avoid legend-only interpretation).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import plotly.graph_objects as go


def _points_to_dataframe(frontier_payload: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for p in frontier_payload.get("points", []):
        rows.append({
            "provider": p["provider"],
            "y_strength": p["y_strength"],
            "y_ci_lower": p["y_ci_lower"],
            "y_ci_upper": p["y_ci_upper"],
            "x_value": p["x_value"],
            "on_frontier": p["on_frontier"],
            "annotations": "; ".join(p.get("annotations", [])),
            "is_anchor": p["provider"] == "anchor",
        })
    return pd.DataFrame(rows)


# --- Plotly (interactive) ------------------------------------------------


def plotly_frontier(frontier_payload: dict[str, Any]) -> go.Figure:
    """Interactive scatter with error bars + frontier hull. For Streamlit."""
    df = _points_to_dataframe(frontier_payload)
    # Drop points with no x (they're rendered separately)
    plottable = df[df["x_value"].notna()].copy()
    missing = df[df["x_value"].isna()]

    axis = frontier_payload.get("axis", "cost")
    x_label = (
        "$ per 1K words" if axis == "cost"
        else "TTFA p90 (ms) — or buffered total (D-008)"
    )

    fig = go.Figure()

    # Dominated points
    dominated = plottable[~plottable["on_frontier"] & ~plottable["is_anchor"]]
    if not dominated.empty:
        fig.add_trace(go.Scatter(
            x=dominated["x_value"], y=dominated["y_strength"],
            error_y=dict(
                type="data",
                array=dominated["y_ci_upper"] - dominated["y_strength"],
                arrayminus=dominated["y_strength"] - dominated["y_ci_lower"],
            ),
            mode="markers+text",
            name="dominated",
            text=dominated["provider"],
            textposition="top center",
            marker=dict(color="#888", size=10, symbol="circle-open"),
            hovertemplate=(
                "<b>%{text}</b><br>x=%{x:.3f}<br>y=%{y:.2f} "
                "[%{customdata[0]:.2f}, %{customdata[1]:.2f}]<br>"
                "%{customdata[2]}<extra></extra>"
            ),
            customdata=dominated[[
                "y_ci_lower", "y_ci_upper", "annotations",
            ]].values,
        ))

    # On-frontier providers (non-anchor)
    survivors = plottable[plottable["on_frontier"] & ~plottable["is_anchor"]]
    if not survivors.empty:
        fig.add_trace(go.Scatter(
            x=survivors["x_value"], y=survivors["y_strength"],
            error_y=dict(
                type="data",
                array=survivors["y_ci_upper"] - survivors["y_strength"],
                arrayminus=survivors["y_strength"] - survivors["y_ci_lower"],
            ),
            mode="markers+text",
            name="on frontier",
            text=survivors["provider"],
            textposition="top center",
            marker=dict(color="#2266cc", size=13, symbol="circle"),
            hovertemplate=(
                "<b>%{text}</b><br>x=%{x:.3f}<br>y=%{y:.2f} "
                "[%{customdata[0]:.2f}, %{customdata[1]:.2f}]<br>"
                "%{customdata[2]}<extra></extra>"
            ),
            customdata=survivors[[
                "y_ci_lower", "y_ci_upper", "annotations",
            ]].values,
        ))

    # Anchor
    anchor = plottable[plottable["is_anchor"]]
    if not anchor.empty:
        fig.add_trace(go.Scatter(
            x=anchor["x_value"], y=anchor["y_strength"],
            error_y=dict(
                type="data",
                array=anchor["y_ci_upper"] - anchor["y_strength"],
                arrayminus=anchor["y_strength"] - anchor["y_ci_lower"],
            ),
            mode="markers+text",
            name="human anchor",
            text=anchor["provider"],
            textposition="top center",
            marker=dict(color="#cc4422", size=15, symbol="star"),
            hovertemplate="<b>anchor</b><br>y=%{y:.2f}<extra></extra>",
        ))

    fig.update_layout(
        title=(
            f"{frontier_payload.get('use_case', '?').capitalize()} - "
            f"{axis} frontier"
        ),
        xaxis_title=x_label,
        yaxis_title="BT strength (bootstrap 95% CI)",
        template="plotly_white",
        hovermode="closest",
        height=500,
    )

    # Annotate providers with missing x below the plot
    if not missing.empty:
        note = ", ".join(missing["provider"])
        fig.add_annotation(
            xref="paper", yref="paper", x=0, y=-0.15,
            showarrow=False,
            text=f"<i>not on chart (no x-axis data): {note}</i>",
            font=dict(size=10, color="#666"),
        )
    return fig


# --- Altair (static) -----------------------------------------------------


def altair_frontier(frontier_payload: dict[str, Any]) -> alt.LayerChart:
    """Static case-study version of the same chart.

    Altair grammar makes the error-bar + hull composition cleaner than
    matplotlib; vl-convert-python renders to PNG for embedding in memos.
    """
    df = _points_to_dataframe(frontier_payload)
    plottable = df[df["x_value"].notna()].copy()

    axis = frontier_payload.get("axis", "cost")
    x_label = "$ per 1K words" if axis == "cost" else "TTFA p90 (ms)"

    # Color scale: on-frontier providers pop; dominated fade to gray;
    # anchor gets a warm callout color.
    plottable["role"] = plottable.apply(
        lambda r: "anchor" if r["is_anchor"]
        else ("on frontier" if r["on_frontier"] else "dominated"),
        axis=1,
    )

    color_scale = alt.Scale(
        domain=["on frontier", "dominated", "anchor"],
        range=["#2266cc", "#aaaaaa", "#cc4422"],
    )

    base = alt.Chart(plottable).encode(
        x=alt.X("x_value:Q", title=x_label,
                scale=alt.Scale(zero=False, padding=20)),
        y=alt.Y("y_strength:Q", title="BT strength (95% CI)",
                scale=alt.Scale(zero=False, padding=20)),
    )

    error_bars = base.mark_errorbar(color="#666", opacity=0.7).encode(
        y=alt.Y("y_ci_lower:Q"),
        y2=alt.Y2("y_ci_upper:Q"),
    )

    points = base.mark_point(size=180, filled=True, opacity=0.85).encode(
        color=alt.Color("role:N", scale=color_scale, legend=alt.Legend(title=None)),
        shape=alt.Shape("role:N", scale=alt.Scale(
            domain=["on frontier", "dominated", "anchor"],
            range=["circle", "circle", "diamond"],
        )),
        tooltip=[
            "provider:N",
            alt.Tooltip("y_strength:Q", format=".2f"),
            alt.Tooltip("x_value:Q", format=".3f"),
            "annotations:N",
        ],
    )

    labels = base.mark_text(align="left", dx=8, dy=-8, fontSize=11).encode(
        text="provider:N",
    )

    chart = (error_bars + points + labels).properties(
        width=520, height=380,
        title=alt.TitleParams(
            text=(
                f"{frontier_payload.get('use_case', '?').capitalize()} - "
                f"{axis} frontier"
            ),
            fontSize=14, anchor="start",
        ),
    ).configure_view(stroke=None).configure_axis(
        gridColor="#eee", labelFontSize=11, titleFontSize=12,
    )
    return chart


def altair_to_png(chart: alt.Chart | alt.LayerChart, out_path: Path, scale: float = 2.0) -> None:
    """Render an Altair chart to a PNG file via vl-convert-python."""
    import vl_convert as vlc
    out_path.parent.mkdir(parents=True, exist_ok=True)
    png = vlc.vegalite_to_png(chart.to_json(), scale=scale)
    out_path.write_bytes(png)


def plotly_to_html(fig: go.Figure, out_path: Path, include_plotlyjs: str = "cdn") -> None:
    """Write an interactive standalone HTML for the case study appendix."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs=include_plotlyjs, full_html=True)
