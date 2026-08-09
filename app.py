"""Streamlit app for the Hee local-first companion bot."""

from __future__ import annotations

import streamlit as st

from hee_bot.bot import LocalCompanionBot
from hee_bot.config import SETTINGS


st.set_page_config(page_title="Hee", page_icon=":speech_balloon:", layout="wide")


@st.cache_resource
def get_bot() -> LocalCompanionBot:
    return LocalCompanionBot()


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sidebar() -> None:
    st.sidebar.title("Hee")
    st.sidebar.caption("Local-first companion bot")
    st.sidebar.markdown(
        "\n".join(
            [
                f"- Chat model: `{SETTINGS.chat_model}`",
                f"- Embeddings: `{SETTINGS.embedding_model}`",
                f"- SQLite: `{SETTINGS.sqlite_path}`",
                "- Commands: `/remember`, `/forget`, `/memory`, `/help`",
            ]
        )
    )
    st.sidebar.info(
        "Memory policy: store preferences, important events, recurring goals, "
        "and only sensitive details you explicitly choose to remember."
    )


def render_chat_history() -> None:
    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("caption"):
                st.caption(item["caption"])


def main() -> None:
    init_session_state()
    bot = get_bot()

    st.title("Hee")
    st.write(
        "A private, local-first support bot powered by Ollama, Qwen, SQLite, and Streamlit."
    )
    render_sidebar()
    render_chat_history()

    prompt = st.chat_input("Talk to Hee or use /remember, /forget, /memory")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking locally..."):
            result = bot.handle_input(prompt)
        st.markdown(result["reply"])
        caption_parts: list[str] = []
        memory_update = result.get("memory_update")
        if memory_update:
            caption_parts.append(memory_update)
        analysis = result.get("analysis")
        if analysis:
            caption_parts.append(
                f"emotion={analysis.emotion}, intent={analysis.intent}, store={analysis.should_store}"
            )
        caption = " | ".join(caption_parts)
        if caption:
            st.caption(caption)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["reply"],
            "caption": caption if caption else None,
        }
    )


if __name__ == "__main__":
    main()
