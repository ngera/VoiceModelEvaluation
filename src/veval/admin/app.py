"""Streamlit admin panel — landing page.

Launch:  streamlit run src/veval/admin/app.py

Design rule (CLAUDE.md): admin panel is a thin wrapper over the same
functions the CLI calls. Never duplicate logic.
"""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from veval import __version__

load_dotenv()

st.set_page_config(
    page_title="veval admin",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ veval — admin panel")
st.caption(f"v{__version__} · local-only · Voice AI evaluation harness")

st.markdown(
    """
    **Purpose:** interactive front-door to the same pipeline the CLI runs.
    Pages are added incrementally as each phase lands (see `CLAUDE.md`).

    | Page | Phase | Status |
    |---|---|---|
    | Doctor | A | ✅ live — click **Doctor** in sidebar |
    | Run    | D | ✅ live — click **Run** in sidebar |
    | Results | E | ✅ live — click **Results** in sidebar |
    | Rate   | F | ✅ live — click **Rate** in sidebar |
    | Frontier | G | ⏳ pending |

    ---

    **Reference docs:**
    - `documentation/voice_ai_eval_spec_v2.md` — WHAT + HOW
    - `documentation/IMPLEMENTATION_PLAN.md` — BUILD phases
    - `CLAUDE.md` — locked decisions and conventions
    - `RUNBOOK.md` — operational commands (build/dev)
    """
)

with st.sidebar:
    st.markdown("### veval")
    st.caption("Pick a page above.")
