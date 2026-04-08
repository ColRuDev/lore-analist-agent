"""Chat area component — message history, input and streaming response."""

import streamlit as st

from src.agent.exceptions import ModelUnavailableError


def render_chat() -> None:
    """Render the chat history and handle new user input with streaming."""
    st.title("Lore Analyst Agent")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Ask about game lore, characters, plot…"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            try:
                for chunk in st.session_state.runner.stream(user_input):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
            except ModelUnavailableError as e:
                placeholder.warning(str(e), icon="⏳")
                full_response = ""
            except Exception as e:
                error_text = str(e)
                if any(kw in error_text for kw in ("API key", "403", "PermissionDenied", "PERMISSION_DENIED")):
                    placeholder.error(
                        "❌ Invalid or unauthorised API key. "
                        "Please update your key in the sidebar.",
                        icon="🔑",
                    )
                else:
                    placeholder.error(f"❌ Unexpected error: {error_text}")
                full_response = ""

        if full_response:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
