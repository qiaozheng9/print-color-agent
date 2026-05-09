"""Print Color Prediction & Calibration Agent — Streamlit entry point.

Uses st.navigation + st.Page for modern multipage routing.
"""

from __future__ import annotations

import warnings

# Suppress LangChain/LangGraph deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="langgraph")

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from database.db_manager import init_db
from database.seed_data import run_all_seeding

# ── Database initialization ──
init_db()
run_all_seeding()

# ── Agent initialization is deferred to the chat page ──
# The agent requires a valid API key; tool-only pages work without it.

# ── Page definitions using st.Page ──
from frontend.pages import (
    render_chat_page,
    render_compare_page,
    render_history_page,
    render_knowledge_page,
    render_predict_page,
)

page_chat = st.Page(render_chat_page, title="智能对话", icon="💬", default=True, url_path="chat")
page_predict = st.Page(render_predict_page, title="色彩预测", icon="🎨", url_path="predict")
page_compare = st.Page(render_compare_page, title="工艺对比", icon="⚖️", url_path="compare")
page_knowledge = st.Page(render_knowledge_page, title="知识库", icon="📚", url_path="knowledge")
page_history = st.Page(render_history_page, title="校准历史", icon="📊", url_path="history")

# ── Navigation ──
nav = st.navigation(
    {
        "主功能": [page_chat],
        "色彩工具": [page_predict, page_compare],
        "数据查询": [page_knowledge, page_history],
    },
    position="sidebar",
)

# ── Run selected page ──
nav.run()
