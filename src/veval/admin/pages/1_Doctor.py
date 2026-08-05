"""Doctor page — same checks as `veval doctor`, in a browser tab."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from veval.adapters import ADAPTERS
from veval.config import load_providers
from veval.doctor import run_doctor

load_dotenv()

st.set_page_config(page_title="Doctor — veval", page_icon="🩺", layout="wide")
st.title("🩺 Doctor")
st.caption("Health-check the pipeline end-to-end. Same as `veval doctor` from the CLI.")

# --- Controls ---
col_l, col_r = st.columns([2, 1])
with col_l:
    providers_file = st.text_input(
        "providers.yaml path",
        value="configs/providers.yaml",
        help="Loaded on every run. Missing file falls back to registered adapters.",
    )
    probe_text = st.text_area(
        "Probe text",
        value="The quick brown fox jumps over the lazy dog.",
        help="Sent to each provider. Keep short — this is a smoke test, not a benchmark.",
    )
    only_provider = st.selectbox(
        "Restrict to one provider",
        options=["(all)"] + sorted(ADAPTERS.keys()),
        index=0,
    )

with col_r:
    st.markdown("**Registered adapters**")
    for name in sorted(ADAPTERS.keys()):
        st.markdown(f"- `{name}`")
    st.caption("Key presence is reported per provider after a run — see Environment below.")

    st.markdown("**Configs**")
    p = Path(providers_file)
    if p.exists():
        try:
            providers = load_providers(p)
            st.success(f"{len(providers.providers)} providers loaded")
        except Exception as e:  # noqa: BLE001
            st.error(f"parse error: {e}")
    else:
        st.warning("providers.yaml not found — will use fallback probe")

st.divider()

# --- Run ---
run_clicked = st.button("Run doctor", type="primary")

if run_clicked:
    with st.spinner("Running smoke tests..."):
        report = run_doctor(
            providers_file=Path(providers_file),
            only_provider=None if only_provider == "(all)" else only_provider,
            probe_text=probe_text,
        )

    # Env keys
    st.subheader("Environment")
    if report.envs_present:
        cols = st.columns(min(len(report.envs_present), 4))
        for i, (key, present) in enumerate(report.envs_present.items()):
            with cols[i % len(cols)]:
                if present:
                    st.success(f"✓ {key}")
                else:
                    st.error(f"✗ {key} not set")
    else:
        st.info("No env checks (providers.yaml not loaded)")

    # Per-adapter results
    st.subheader("Adapters")
    for r in report.adapter_results:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 3])
            with c1:
                if r.ok:
                    st.markdown(f"### ✅ {r.provider}")
                else:
                    st.markdown(f"### ❌ {r.provider}")
            with c2:
                if r.ok and r.result:
                    ttfa = f"{r.result.ttfa_ms:.0f} ms" if r.result.ttfa_ms else "—"
                    st.metric("TTFA", ttfa)
            with c3:
                if r.ok and r.result:
                    st.metric("Total", f"{r.result.total_ms:.0f} ms")
            with c4:
                if r.ok and r.result:
                    st.caption(f"{len(r.result.audio_bytes):,} bytes · {r.result.audio_format}")
                    st.audio(r.result.audio_bytes, format=f"audio/{r.result.audio_format}")
                else:
                    st.error(r.notes)

    # Summary
    ok = sum(1 for r in report.adapter_results if r.ok)
    total = len(report.adapter_results)
    if total > 0 and ok == total:
        st.success(f"All {total} adapter(s) passed.")
    elif total > 0:
        st.error(f"{total - ok} failure(s) of {total}. Fix before campaign.")

    if report.run_dir:
        st.caption(f"Run written to: `{report.run_dir}`")
