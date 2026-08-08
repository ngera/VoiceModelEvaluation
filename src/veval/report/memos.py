"""Memo templates with data slots.

Two memos per campaign:
    - `memo_conversational.md` -- support-agent recommendation
    - `memo_narration.md`      -- long-form narration recommendation

Each carries: the recommendation (single provider), rationale grounded in
the survivor set and frontier, a "not recommended" list with reasons,
and a robustness note (does the recommendation change if a threshold
moves within its pre-registered sweep points?).

Case study is a separate longer document that composes the two memos +
methodology + friction findings + Delta-vs-HI.
"""

from __future__ import annotations

from datetime import date

from veval.report.tables import (
    correlations_table,
    frontier_table,
    hi_table,
    robustness_table,
    survivors_table,
)


def _pick_recommendation(score_payload: dict, use_case: str) -> tuple[str | None, str]:
    """Return (provider, one-line rationale) or (None, reason).

    Heuristic (v1, spec §5): recommend the survivor that dominates on
    the COST frontier (best quality per dollar). If no survivor is on
    both cost and quality frontiers, recommend the highest-BT survivor.
    """
    fr_cost = score_payload.get("frontiers", {}).get(use_case, {}).get("cost")
    if not fr_cost:
        return None, "no frontier data yet - run `veval score` first"

    on_frontier = [
        p for p in fr_cost["points"]
        if p["on_frontier"] and p["provider"] != "anchor"
    ]
    if not on_frontier:
        return None, "no survivors on cost frontier"

    # Pick the one with the highest BT strength; tie-break on lowest cost.
    pick = sorted(
        on_frontier,
        key=lambda p: (-p["y_strength"], p["x_value"] or float("inf")),
    )[0]
    rationale = (
        f"BT strength {pick['y_strength']:+.2f} "
        f"(CI [{pick['y_ci_lower']:+.2f}, {pick['y_ci_upper']:+.2f}]) "
        f"at ${pick['x_value']:.3f}/1K words. "
        f"On the cost frontier; not dominated by any survivor."
    )
    return pick["provider"], rationale


def _not_recommended(score_payload: dict, use_case: str) -> list[str]:
    """One-line justifications for every non-recommended survivor."""
    fr = score_payload.get("frontiers", {}).get(use_case, {}).get("cost")
    if not fr:
        return []
    out: list[str] = []
    for p in fr["points"]:
        if p["on_frontier"] or p["provider"] == "anchor":
            continue
        dominators = p.get("dominated_by") or []
        if dominators:
            out.append(
                f"`{p['provider']}` - dominated by "
                + ", ".join(f"`{d}`" for d in dominators)
                + " (delta_y outside CI zero)"
            )
        else:
            out.append(f"`{p['provider']}` - off frontier")
    return out


def _robustness_note(score_payload: dict, use_case: str) -> str:
    unstable = [
        r for r in score_payload.get("robustness", [])
        if r["use_case"] == use_case and not r["is_stable"]
    ]
    if not unstable:
        return (
            "The recommendation is stable across the pre-registered "
            "robustness_points for every gate in this use case."
        )
    parts = ["The following gates flipped survivor set across their sweep:"]
    for r in unstable:
        parts.append(
            f"- `{r['gate_metric']}` - "
            f"{', '.join(str(p) for p in r['robustness_points'])}"
        )
    parts.append(
        "\nInterpretation: check the robustness table below. If your "
        "operating threshold sits at a boundary, revisit."
    )
    return "\n".join(parts)


def memo_markdown(score_payload: dict, use_case: str) -> str:
    """Render the memo for one use case as markdown."""
    provider, rationale = _pick_recommendation(score_payload, use_case)
    not_rec = _not_recommended(score_payload, use_case)

    heading = (
        "Support agent recommendation" if use_case == "conversational"
        else "Long-form narration recommendation"
    )

    parts: list[str] = [
        f"# {heading}",
        f"_Generated {date.today().isoformat()} "
        f"from `{score_payload.get('analysis_dir', 'unknown')}`_",
        "",
        "## Recommendation",
    ]
    if provider:
        parts.append(f"**`{provider}`** -- {rationale}")
    else:
        parts.append(f"_No recommendation available: {rationale}_")
    parts.append("")

    parts.append("## Not recommended")
    if not_rec:
        parts.extend(f"- {line}" for line in not_rec)
    else:
        parts.append("_(no dominated survivors)_")
    parts.append("")

    parts.append("## Robustness")
    parts.append(_robustness_note(score_payload, use_case))
    parts.append("")

    parts.append("## Frontier - cost axis")
    parts.append(frontier_table(score_payload, use_case, "cost"))
    parts.append("")

    parts.append("## Frontier - latency axis")
    parts.append(frontier_table(score_payload, use_case, "latency"))
    parts.append("")

    parts.append("## Survivor detail")
    parts.append(survivors_table_filtered(score_payload, use_case))
    parts.append("")

    return "\n".join(parts)


def survivors_table_filtered(score_payload: dict, use_case: str) -> str:
    """Same as survivors_table but scoped to one use case."""
    lines = ["| Provider | Survives? | Blocker |",
             "|---|---|---|"]
    for s in score_payload.get("survivals", []):
        if s["use_case"] != use_case:
            continue
        blocker = "--"
        if not s["survives"]:
            fails = [o for o in s["gate_outcomes"] if o["passed"] is False]
            if fails:
                blocker = f"`{fails[0]['gate_metric']}`"
        status = "yes" if s["survives"] else "**no**"
        lines.append(f"| `{s['provider']}` | {status} | {blocker} |")
    return "\n".join(lines)


def case_study_markdown(score_payload: dict) -> str:
    """Composite: methodology summary + both memos + cross-cutting tables."""
    parts = [
        "# Voice AI evaluation - case study",
        f"_Generated {date.today().isoformat()} "
        f"from `{score_payload.get('analysis_dir', 'unknown')}`_",
        "",
        "## Method (one paragraph)",
        (
            "Eight providers evaluated across two use cases (conversational "
            "support agent + long-form narration). Quality measured three "
            "ways: distributional (TTSDS2 + Audiobox PQ, D3), two-judge WER "
            "with a Parakeet + faster-whisper agreement rule (D2), and "
            "n=1 blind pairwise A/B with a human anchor fitted via Bradley-"
            "Terry with clustered-bootstrap CIs (D4). Latency measured as "
            "TTFA p50/p90 from 50 serial trials + RTF on long items (D1). "
            "Cost from published pricing (D6). Configs frozen in `prereg-v1` "
            "before any results existed; amendments logged in DEVIATIONS.md "
            "and re-tagged. Domination is asserted only when the bootstrap "
            "95% CI on the pairwise BT difference excludes zero -- otherwise "
            "the pair is reported as 'no difference detected at this n'."
        ),
        "",
        "## Recommendations",
        "",
    ]

    for uc in ("conversational", "narration"):
        provider, rationale = _pick_recommendation(score_payload, uc)
        parts.append(f"### {uc}")
        if provider:
            parts.append(f"**`{provider}`** -- {rationale}")
        else:
            parts.append(f"_No recommendation available: {rationale}_")
        parts.append("")

    parts.append("## Gates & survivors")
    parts.append(survivors_table(score_payload))
    parts.append("")

    parts.append("## Frontier - conversational")
    parts.append("### Cost axis")
    parts.append(frontier_table(score_payload, "conversational", "cost"))
    parts.append("### Latency axis")
    parts.append(frontier_table(score_payload, "conversational", "latency"))
    parts.append("")

    parts.append("## Frontier - narration")
    parts.append("### Cost axis")
    parts.append(frontier_table(score_payload, "narration", "cost"))
    parts.append("### Latency axis")
    parts.append(frontier_table(score_payload, "narration", "latency"))
    parts.append("")

    parts.append("## Robustness sweep")
    parts.append(robustness_table(score_payload))
    parts.append("")

    parts.append("## Cross-metric agreement (Spearman rho)")
    parts.append(correlations_table(score_payload))
    parts.append("")

    parts.append("## Humanness Index cross-check")
    parts.append(hi_table(score_payload))
    parts.append("")

    parts.append("## Charts")
    parts.append("- `conversational_cost.png` -- conversational quality vs cost")
    parts.append("- `conversational_latency.png` -- conversational quality vs TTFA")
    parts.append("- `narration_cost.png` -- narration quality vs cost")
    parts.append("- `narration_latency.png` -- narration quality vs RTF")
    parts.append("")
    parts.append(
        "Interactive versions (`*.html`) are in `site/interactive/`. "
        "See also the friction-log summary in the case study appendix."
    )

    return "\n".join(parts)
