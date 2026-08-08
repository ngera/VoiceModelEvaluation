"""Markdown table generators for the case study.

Every table is a pure function of `score.json`. Numbers are formatted
to sensible precision (2 sig figs for strengths, currency to 3 dp).
"""

from __future__ import annotations

from typing import Any


def _fmt(value: Any, spec: str = ".2f") -> str:
    if value is None:
        return "--"
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return str(value)


def survivors_table(score_payload: dict) -> str:
    """One row per (use_case, provider) with pass/fail + first failing gate."""
    lines = ["| Use case | Provider | Survives? | First blocker |",
             "|---|---|---|---|"]
    for s in score_payload.get("survivals", []):
        blocker = "--"
        if not s["survives"]:
            fails = [o for o in s["gate_outcomes"] if o["passed"] is False]
            if fails:
                blocker = f"`{fails[0]['gate_metric']}` ({fails[0]['reason']})"
        status = "yes" if s["survives"] else "**no**"
        lines.append(
            f"| {s['use_case']} | `{s['provider']}` | {status} | {blocker} |"
        )
    return "\n".join(lines)


def frontier_table(score_payload: dict, use_case: str, axis: str) -> str:
    """Ranked table of frontier points for one (use_case, axis) chart."""
    fr = score_payload.get("frontiers", {}).get(use_case, {}).get(axis)
    if not fr:
        return f"_(no frontier data for {use_case}.{axis})_"

    lines = [
        f"| Provider | On frontier | BT strength | 95% CI | "
        f"{'$/1K words' if axis == 'cost' else 'Latency (ms)'} | Notes |",
        "|---|---|---|---|---|---|",
    ]
    # Sort by strength descending (best on top)
    points = sorted(fr["points"], key=lambda p: -p["y_strength"])
    for p in points:
        on = "yes" if p["on_frontier"] else "--"
        ci = f"[{_fmt(p['y_ci_lower'])}, {_fmt(p['y_ci_upper'])}]"
        x = _fmt(p["x_value"], ".3f" if axis == "cost" else ".0f")
        notes = "; ".join(p.get("annotations", [])) or "--"
        lines.append(
            f"| `{p['provider']}` | {on} | {_fmt(p['y_strength'])} | {ci} | {x} | {notes} |"
        )
    return "\n".join(lines)


def robustness_table(score_payload: dict) -> str:
    """Which gates change their survivor set across their robustness_points."""
    lines = ["| Use case | Gate | Points | Stable? | Survivor deltas |",
             "|---|---|---|---|---|"]
    for r in score_payload.get("robustness", []):
        stable = "yes" if r["is_stable"] else "**NO**"
        deltas = "--"
        if not r["is_stable"]:
            surv = r["survivors_per_point"]
            deltas = " -> ".join(
                f"{pt}={','.join(surv[pt])}" for pt in sorted(surv, key=float)
            )
        lines.append(
            f"| {r['use_case']} | `{r['gate_metric']}` | "
            f"{r['robustness_points']} | {stable} | {deltas} |"
        )
    return "\n".join(lines)


def correlations_table(score_payload: dict) -> str:
    """Spearman rho table (D3 <-> D4, D3 <-> HI, D4 <-> HI)."""
    corr = score_payload.get("correlations", [])
    if not corr:
        return "_(no correlation data — needs D3 quality + BT fit + HI snapshot)_"
    lines = ["| Left axis | Right axis | rho | p | n | Interpretation |",
             "|---|---|---|---|---|---|"]
    for c in corr:
        rho = _fmt(c.get("rho"), ".2f")
        p = _fmt(c.get("p_value"), ".3f")
        lines.append(
            f"| {c['left_axis']} | {c['right_axis']} | {rho} | {p} | "
            f"{c['n_shared']} | {c['interpretation']} |"
        )
    return "\n".join(lines)


def hi_table(score_payload: dict) -> str:
    """Humanness Index comparison table."""
    hi = score_payload.get("hi")
    if not hi:
        return "_(no HI comparison — pass `--hi-snapshot` to score)_"
    snap = hi.get("snapshot", {})
    lines = [
        f"_HI snapshot captured {snap.get('captured_at')} from "
        f"{snap.get('source')}_\n",
        "| Provider | HI rank | Our rank | Delta | HI score | Our BT | Reproduces? |",
        "|---|---|---|---|---|---|---|",
    ]
    for provider, c in sorted(hi.get("comparisons", {}).items()):
        lines.append(
            f"| `{provider}` | "
            f"{_fmt(c.get('hi_rank'), 'd') if c.get('hi_rank') is not None else '--'} | "
            f"{_fmt(c.get('our_rank'), 'd') if c.get('our_rank') is not None else '--'} | "
            f"{_fmt(c.get('delta_rank'), '+d') if c.get('delta_rank') is not None else '--'} | "
            f"{_fmt(c.get('hi_score'))} | {_fmt(c.get('our_strength'))} | "
            f"{c.get('reproduces', 'unknown')} |"
        )
    return "\n".join(lines)
