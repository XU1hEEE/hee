"""Streamlit app for the Hee local-first companion bot."""

from __future__ import annotations

import json

import streamlit as st

from hee_bot.bot import LocalCompanionBot
from hee_bot.config import DATABASE_PATH
from hee_bot.database import Database


st.set_page_config(page_title="Hee", page_icon=":speech_balloon:", layout="wide")


@st.cache_resource
def get_bot() -> LocalCompanionBot:
    """Get a cached instance of the bot."""
    provider = st.session_state.get("llm_provider", "ollama")
    if provider == "openai":
        return LocalCompanionBot(llm_provider="openai", openai_api_key=st.session_state.get("openai_api_key"))
    return LocalCompanionBot()


@st.cache_resource
def get_db() -> Database:
    """Get a cached instance of the database."""
    db = Database(DATABASE_PATH)
    db.initialize()
    return db

def init_session_state() -> None:
    """Initialize session state variables."""
    if "messages_by_space" not in st.session_state:
        st.session_state.messages_by_space = {}
    if "selected_space_id" not in st.session_state:
        st.session_state.selected_space_id = 1  # Default space


def render_sidebar() -> None:
    """Render the sidebar with memory spaces and controls."""
    st.sidebar.title("Hee")
    st.sidebar.caption("Your local-first AI companion")

    st.sidebar.header("LLM Provider")
    provider = st.sidebar.radio("Provider", ["Ollama", "OpenAI"], key="llm_provider")
    if provider == "OpenAI":
        api_key = st.sidebar.text_input("OpenAI API Key", type="password", key="openai_api_key")

    db = get_db()
    spaces = db.get_memory_spaces()
    space_names = {space.id: space.name for space in spaces}

    selected_space_id = st.sidebar.selectbox(
        "Memory Space",
        options=list(space_names.keys()),
        format_func=lambda x: space_names[x],
        key="selected_space_id",
    )

    with st.sidebar.form("new_space"):
        new_space_name = st.text_input("Space Name")
        if st.form_submit_button("＋ New Space") and new_space_name.strip():
            name = new_space_name.strip()
            if name in space_names.values():
                st.warning("A space with that name already exists.")
            else:
                db.add_memory_space(name, f"A space for {name}")
                st.rerun()


def render_memory_dashboard() -> None:
    """Render the memory dashboard for browsing and exporting memories."""
    st.header("Memory Dashboard")
    db = get_db()
    space_id = st.session_state.selected_space_id
    memories = db.get_enriched_memories(space_id)

    if not memories:
        st.info("No memories in this space yet.")
        return

    for mem in memories:
        with st.expander(f"{mem.memory_type.upper()}: {mem.content[:50]}..."):
            st.markdown(f"**Content:** {mem.content}")
            st.markdown(f"**Source:** {mem.source_message or 'N/A'}")
            st.markdown(f"**History:**")
            st.code(mem.history or "No changes tracked.", language="diff")

            if st.button("Delete", key=f"delete_{mem.id}"):
                db.delete_memory(mem.id)
                st.rerun()

    # Export functionality
    st.subheader("Export Space")
    export_format = st.radio("Format", ["JSON", "Markdown"], horizontal=True)
    if st.button("Generate Export"):
        if export_format == "JSON":
            json_export = json.dumps([mem.__dict__ for mem in memories], indent=2)
            st.download_button(
                "Download JSON",
                json_export,
                f"hee_memories_{space_id}.json",
                "application/json",
            )
        else:
            md_export = "\n".join([f"- **{m.memory_type}:** {m.content}" for m in memories])
            st.download_button(
                "Download Markdown",
                md_export,
                f"hee_memories_{space_id}.md",
                "text/markdown",
            )


def render_chat() -> None:
    """Render the main chat interface."""
    bot = get_bot()
    st.header(f"Chat")
    messages = st.session_state.messages_by_space.setdefault(st.session_state.selected_space_id, [])

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to Hee..."):
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = bot.handle_input(
                    prompt, st.session_state.selected_space_id
                )
                st.markdown(result["reply"])

        messages.append({"role": "assistant", "content": result["reply"]})
        st.rerun()


def main() -> None:
    """Main app execution."""
    init_session_state()
    render_sidebar()

    tab1, tab2 = st.tabs(["Chat", "Memory Dashboard"])

    with tab1:
        render_chat()

    with tab2:
        render_memory_dashboard()


if __name__ == "__main__":
    main()
