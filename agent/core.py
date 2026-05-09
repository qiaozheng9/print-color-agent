"""LangGraph agent creation, LLM configuration, and query execution.

Uses create_react_agent from langgraph.prebuilt with ChatOpenAI pointed at
the MiMo API (OpenAI-compatible endpoint).
"""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.prompts import SYSTEM_PROMPT


def create_llm() -> ChatOpenAI:
    """Create a ChatOpenAI instance configured for the MiMo API.

    Reads configuration from environment variables:
    - MIMO_API_KEY: API authentication key
    - MIMO_BASE_URL: API endpoint URL
    - MIMO_MODEL: Model identifier
    """
    api_key = os.getenv("MIMO_API_KEY", "")
    base_url = os.getenv("MIMO_BASE_URL", "https://api.mimo.example.com/v1")
    model = os.getenv("MIMO_MODEL", "MiMo-V2.5-Pro")

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0.1,
    )


def create_agent(tools: list, llm: ChatOpenAI | None = None):
    """Create a LangGraph ReAct agent with the given tools.

    Args:
        tools: List of LangChain tools to bind to the agent.
        llm: Optional pre-configured LLM. If None, creates one from env vars.

    Returns:
        A compiled LangGraph agent graph ready for invocation.
    """
    if llm is None:
        llm = create_llm()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )
    return agent


def run_agent_query(agent, user_input: str, chat_history: list[BaseMessage] | None = None) -> str:
    """Run a single query through the agent and return the response text.

    Args:
        agent: The compiled LangGraph agent.
        user_input: The user's message text.
        chat_history: Optional list of previous messages for context.

    Returns:
        The agent's response as a string.
    """
    messages: list[BaseMessage] = []
    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=user_input))

    result = agent.invoke({"messages": messages})

    # Extract the last AI message from the result
    response_messages = result.get("messages", [])
    for msg in reversed(response_messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content

    return "抱歉，未能生成有效回复。请重试。"
