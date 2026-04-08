"""Session state initialisation — runs once per browser session."""

import os

import streamlit as st

from src.agent.core import get_analyst_agent
from src.agent.runner import AgentRunner
from src.models.google import GoogleLLMModel
from src.tools import get_all_tools


def init_session_state() -> None:
    """Bootstrap AgentRunner, model, tools and message list in session state.

    Reads the API key from session state (user-provided) or the environment.
    Skips runner initialisation if no key is available and records any
    initialisation error in ``st.session_state.init_error``.
    """
    # Seed api_key from the environment on the very first run
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("GOOGLE_API_KEY", "")

    # Always ensure messages list exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Nothing to do without a key or when runner is already live
    if not st.session_state.api_key or "runner" in st.session_state:
        return

    # Make the key available to langchain_google_genai
    os.environ["GOOGLE_API_KEY"] = st.session_state.api_key

    try:
        tools = get_all_tools()
        default_model = GoogleLLMModel.GEMINI_3_1_FLASH_LITE
        agent = get_analyst_agent(tools, default_model)

        st.session_state.runner: AgentRunner = AgentRunner(agent)
        st.session_state.current_model: GoogleLLMModel = default_model
        st.session_state.tools = tools
        st.session_state.pop("init_error", None)
    except Exception as e:
        st.session_state.init_error = str(e)
