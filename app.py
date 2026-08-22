"""Streamlit app for the Hee local-first companion bot."""

from __future__ import annotations

import streamlit as st

from hee_bot.bot import LocalCompanionBot
from hee_bot.config import SETTINGS


st.set_page_config(page_title="Hee", page_icon=":speech_balloon:", layout="wide")


@st.cache_resource
def get_bot(provider: str) -> LocalCompanionBot:
    return LocalCompanionBot(provider=provider)


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "provider" not in st.session_state:
        st.session_state.provider = "ollama"


def render_sidebar() -> str:
    st.sidebar.title("Hee")
    st.sidebar.caption("Privacy-first companion bot")

    provider = st.sidebar.radio(
        "Connectivity Mode",
        options=["ollama", "openai"],
        format_func=lambda x: "Offline (Ollama)" if x == "ollama" else "Online (OpenAI)",
        index=0 if st.session_state.provider == "ollama" else 1,
    )

    if provider != st.session_state.provider:
        st.session_state.provider = provider
        st.cache_resource.clear()
        st.rerun()

    model_info = []
    if provider == "ollama":
        model_info = [
            f"- Chat model: `{SETTINGS.chat_model}`",
            f"- Embeddings: `{SETTINGS.embedding_model}`",
        ]
    else:
        if not SETTINGS.openai_api_key:
            st.sidebar.warning("OpenAI API key is missing. Check your environment variables.")
        model_info = [
            f"- Chat model: `{SETTINGS.openai_chat_model}`",
            f"- Embeddings: `{SETTINGS.openai_embedding_model}`",
        ]

    st.sidebar.markdown(
        "\n".join(
            model_info
            + [
                f"- SQLite: `{SETTINGS.sqlite_path}`",
                "- Commands: `/remember`, `/forget`, `/memory`, `/help`",
            ]
        )
    )
    st.sidebar.info(
        "Memory policy: store preferences, important events, recurring goals, "
        "and only sensitive details you explicitly choose to remember."
    )
    return provider


def render_chat_history() -> None:
    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("caption"):
                st.caption(item["caption"])


def main() -> None:
    init_session_state()
    provider = render_sidebar()
    bot = get_bot(provider)

    st.title("Hee")
    st.write(
        "A private, supportive companion powered by Ollama, OpenAI, SQLite, and Streamlit."
    )
    render_chat_history()

    prompt = st.chat_input("Talk to Hee or use /remember, /forget, /memory")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thinking_text = "Thinking locally..." if provider == "ollama" else "Thinking online..."
        with st.spinner(thinking_text):
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
