"""Conversation memory management for Streamlit session state.

Bridges Streamlit's session_state with LangChain's message format.
Streamlit re-runs the entire script on each interaction, so session_state
is the canonical way to persist conversation history across reruns.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def _get_session_messages() -> list[dict[str, str]]:
    """Get the raw message list from Streamlit session state.

    Returns an empty list if session state is not initialized (e.g., during testing).
    """
    try:
        import streamlit as st

        if "messages" not in st.session_state:
            st.session_state.messages = []
        return st.session_state.messages
    except ImportError:
        # Outside Streamlit (e.g., test scripts) — use module-level storage
        if not hasattr(_get_session_messages, "_fallback"):
            _get_session_messages._fallback = []
        return _get_session_messages._fallback


def get_chat_history() -> list[BaseMessage]:
    """Convert session state messages to LangChain BaseMessage objects.

    Returns a list of HumanMessage and AIMessage objects suitable for
    passing to the agent.
    """
    raw = _get_session_messages()
    messages: list[BaseMessage] = []
    for msg in raw:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


def add_message(role: str, content: str) -> None:
    """Append a message to the session state history.

    Args:
        role: Either 'user' or 'assistant'.
        content: The message text.
    """
    messages = _get_session_messages()
    messages.append({"role": role, "content": content})


def clear_history() -> None:
    """Reset the conversation history."""
    messages = _get_session_messages()
    messages.clear()


def get_history_as_dicts() -> list[dict[str, str]]:
    """Return the raw message list (for display in Streamlit UI)."""
    return _get_session_messages()
