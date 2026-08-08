"""Rate page — Phase F pairwise rating workflow.

Same functions as `veval rate` (CLAUDE.md convention). Two panels:
    - Build   — pick rater id, corpora, providers, click build → writes rating/manifest.json
    - Normalize — pick source campaign run, click normalize → -18 LUFS into rating/audio/
    - Fit — drop a judgments CSV, click fit → Bradley-Terry + bootstrap CIs

Serving the rating page itself is a CLI-only concern (blocking server);
this page prints the command to run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from veval.analyze.common import RunReader
from veval.config import load_corpus, load_providers
from veval.human.bt import RawJudgment, consistency_rate, fit_per_use_case
from veval.human.loudness import normalize_file
from veval.human.pair_builder import ANCHOR_SYSTEM, build_manifest, write_manifest
from veval.store.run_store import default_run_store

load_dotenv()

st.set_page_config(page_title="Rate — veval", page_icon="🎧", layout="wide")
st.title("🎧 Rate")
st.caption("Phase F — pairwise A/B rating with Bradley-Terry + bootstrap CIs.")

tabs = st.tabs(["Build manifest", "Normalize audio", "Fit Bradley-Terry"])

# --- Build ------------------------------------------------------------

with tabs[0]:
    st.markdown("**Build the per-rater rating manifest.** Writes `rating/manifest.json`.")

    col_l, col_r = st.columns([2, 1])
    with col_l:
        rater_id = st.text_input("Rater id", value="njg")
        use_cases = st.multiselect(
            "Use cases",
            options=["conversational", "narration"],
            default=["conversational", "narration"],
        )
        reps = st.number_input(
            "Reps per pair", min_value=1, max_value=10, value=3,
            help="D-009: 3 reps default for the 8-provider roster (was 5 in spec).",
        )
        consistency = st.slider(
            "Consistency-repeat fraction", 0.0, 0.25, 0.10, 0.01,
        )
    with col_r:
        providers_path = st.text_input("providers.yaml", value="configs/providers.yaml")
        corpus_dir = st.text_input("corpus dir", value="corpus")
        audio_root = st.text_input("audio root", value="rating/audio")

    if st.button("Build manifest", type="primary", disabled=not (rater_id and use_cases)):
        providers = load_providers(Path(providers_path))
        systems = [p.name for p in providers.providers] + [ANCHOR_SYSTEM]
        corpora = {uc: load_corpus(Path(corpus_dir) / f"{uc}.yaml") for uc in use_cases}
        manifest = build_manifest(
            rater_id=rater_id, systems=systems, use_cases=use_cases,
            corpora=corpora, audio_root=Path(audio_root),
            reps_per_pair=int(reps),
            consistency_repeat_fraction=float(consistency),
        )
        out = Path("rating/manifest.json")
        write_manifest(manifest, out)
        st.success(f"Wrote {out} — {manifest.total_judgments} judgments in {manifest.total_sessions} sessions.")
        st.dataframe(
            pd.DataFrame([{
                "system": s, "n_pairs": sum(
                    1 for j in manifest.judgments
                    if s in (j.system_left, j.system_right)
                ),
            } for s in manifest.systems]),
            hide_index=True, use_container_width=True,
        )

# --- Normalize --------------------------------------------------------

with tabs[1]:
    st.markdown("**Normalize campaign WAVs to -18 LUFS** and copy into `rating/audio/`.")

    runs = default_run_store().list_runs("campaign")
    if not runs:
        st.warning("No campaign runs under ./runs/. Generate audio first.")
    else:
        run_pick = st.selectbox("Source run", options=[p.name for p in runs])
        source = next(p for p in runs if p.name == run_pick)

        if st.button("Normalize", type="primary"):
            reader = RunReader(source)
            ok = 0
            failed = 0
            errors = []
            audio_root = Path("rating/audio")
            with st.status("Normalizing...", expanded=True) as status:
                for rec in reader.records():
                    dst = audio_root / rec.use_case / rec.provider / f"{rec.item_id}.wav"
                    r = normalize_file(rec.wav_path, dst)
                    if r.error:
                        failed += 1
                        errors.append(f"{rec.provider}/{rec.use_case}/{rec.item_id}: {r.error}")
                    else:
                        ok += 1
                status.update(
                    label=f"Done — {ok} normalized, {failed} failed",
                    state="complete", expanded=False,
                )
            if errors:
                st.warning("Errors:")
                for e in errors:
                    st.text(e)
            st.success(f"{ok} files normalized to {audio_root}")

    st.divider()
    st.markdown("**Then serve the rating page:**")
    st.code("uv run veval rate serve", language="powershell")

# --- Fit --------------------------------------------------------------

with tabs[2]:
    st.markdown("**Fit Bradley-Terry** from a judgments CSV downloaded from the rating page.")

    uploaded = st.file_uploader("judgments CSV", type=["csv"])
    n_resamples = st.slider("Bootstrap resamples", 100, 5000, 2000, 100)
    alpha = st.slider("L2 penalty (alpha)", 0.0, 2.0, 0.5, 0.1)

    if uploaded and st.button("Fit", type="primary"):
        import csv as csvmod
        import io

        text = uploaded.getvalue().decode("utf-8")
        rows = list(csvmod.DictReader(io.StringIO(text)))
        judgments = [
            RawJudgment(
                use_case=r["use_case"], item_id=r["item_id"],
                system_left=r["system_left"], system_right=r["system_right"],
                winner=r["winner"],  # type: ignore[arg-type]
                is_consistency_repeat=r["is_consistency_repeat"].lower() == "true",
            )
            for r in rows
        ]
        consistency, n_rep = consistency_rate(judgments)
        st.metric("Loaded judgments", len(judgments))
        st.metric("Consistency", f"{consistency:.1%}", f"n={n_rep} repeats")

        with st.spinner(f"Bootstrapping {n_resamples} resamples per use case..."):
            fits = fit_per_use_case(judgments, n_resamples=n_resamples, alpha=alpha)

        for uc, f in fits.items():
            st.subheader(uc)
            df = pd.DataFrame([
                {
                    "system": s,
                    "strength": strength,
                    "ci_lower": f.strength_ci_lower[s],
                    "ci_upper": f.strength_ci_upper[s],
                }
                for s, strength in sorted(
                    zip(f.systems, f.strengths), key=lambda x: -x[1]
                )
            ])
            st.dataframe(df, hide_index=True, use_container_width=True)

            st.markdown("**Pairwise differences (domination test)**")
            pd_rows = []
            for (a, b), d in f.pairwise_diff.items():
                pd_rows.append({
                    "pair": f"{a} vs {b}",
                    "point_diff": d["point_diff"],
                    "ci_lower": d["ci_lower"],
                    "ci_upper": d["ci_upper"],
                    "dominates": d["dominates"],
                })
            st.dataframe(
                pd.DataFrame(pd_rows).sort_values("point_diff", ascending=False),
                hide_index=True, use_container_width=True,
            )

        out = Path("analysis/bt_fit.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "n_judgments": len(judgments),
            "consistency_rate": consistency,
            "fits": {
                uc: {
                    "systems": f.systems,
                    "strengths": f.strengths,
                    "strength_ci_lower": f.strength_ci_lower,
                    "strength_ci_upper": f.strength_ci_upper,
                    "pairwise_diff": {
                        f"{a}__{b}": v for (a, b), v in f.pairwise_diff.items()
                    },
                }
                for uc, f in fits.items()
            },
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        st.success(f"Saved fit to {out}")
