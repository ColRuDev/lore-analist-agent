"""Sidebar component — API key input, model selector and conversation controls."""

import os

import streamlit as st

from src.agent.core import get_analyst_agent
from src.models.google import GoogleLLMModel


def _render_api_key_section() -> None:
    """Render the API key password input and status indicator."""
    st.subheader("🔑 Gemini API Key")

    stored_key: str = st.session_state.get("api_key", "")

    api_key_input = st.text_input(
        "API Key",
        value=stored_key,
        type="password",
        placeholder="AIza…",
        help="Your Google Gemini API key. Get one at https://aistudio.google.com/apikey",
        label_visibility="collapsed",
    )

    if api_key_input != stored_key:
        st.session_state.api_key = api_key_input
        # Reset runner so session.py re-initialises with the new key
        st.session_state.pop("runner", None)
        st.session_state.pop("init_error", None)
        st.session_state.messages = []
        st.rerun()

    if api_key_input:
        st.success("API key set", icon="✅")
    else:
        st.warning("Enter your API key to start", icon="⚠️")


def render_sidebar() -> None:
    """Render the sidebar: API key input, model radio selector and clear button."""
    with st.sidebar:
        st.title("🎮 Lore Analyst Agent")
        st.markdown("---")

        _render_api_key_section()

        # Model controls are only meaningful once the runner is ready
        if "runner" not in st.session_state:
            return

        st.markdown("---")

        model_names = [m.value for m in GoogleLLMModel]
        current_index = model_names.index(st.session_state.current_model.value)

        selected_model_name = st.radio(
            "Model",
            options=model_names,
            index=current_index,
            help="Switch the underlying LLM. Conversation history is preserved.",
        )

        if selected_model_name != st.session_state.current_model.value:
            new_model = GoogleLLMModel(selected_model_name)
            new_agent = get_analyst_agent(st.session_state.tools, new_model)
            st.session_state.runner.swap_agent(new_agent)
            st.session_state.current_model = new_model
            st.success(f"Switched to **{new_model.value}**")

        st.markdown("---")

        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.runner.clear_history()
            st.session_state.messages = []
            st.rerun()

        st.caption(f"Active model: `{st.session_state.current_model.value}`")
