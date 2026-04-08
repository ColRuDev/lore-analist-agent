"""App assembler — wires page config, session, sidebar and chat together."""

import streamlit as st

from src.streamlit.chat import render_chat
from src.streamlit.session import init_session_state
from src.streamlit.sidebar import render_sidebar


def run() -> None:
    """Compose and launch the Streamlit app."""
    st.set_page_config(
        page_title="Lore Analyst Agent",
        page_icon="🎮",
        layout="wide",
    )
    init_session_state()
    render_sidebar()

    if "init_error" in st.session_state:
        st.error(
            f"❌ Failed to initialise agent: {st.session_state.init_error}",
            icon="🚨",
        )
        st.info(
            "The API key may be invalid or lack Gemini API access. "
            "Update it in the sidebar to try again.",
        )
        return

    if "runner" not in st.session_state:
        st.info("👈 Enter your Gemini API key in the sidebar to start chatting.")
        return

    render_chat()
