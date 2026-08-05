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
    | Run    | D | ⏳ pending |
    | Results | E | ⏳ pending |
    | Frontier | G | ⏳ pending |

    ---

    **Reference docs:**
    - `documentation/voice_ai_eval_portfolio_edition.md` — current build scope
    - `documentation/voice_ai_eval_plan_v1_descoped.md` — full methodology
    - `CLAUDE.md` — locked decisions and conventions
    """
)

with st.sidebar:
    st.markdown("### veval")
    st.caption("Pick a page above.")
