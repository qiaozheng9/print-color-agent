"""All page render functions for the Streamlit app.

Each function is registered via st.Page in main.py.
"""

from __future__ import annotations

import re

import streamlit as st

from frontend.display import (
    format_delta_e_badge,
    inject_global_css,
    parse_delta_e_from_result,
    parse_lab_from_result,
    render_lab_swatch,
    render_lab_swatch_inline,
)


# ═══════════════════════════════════════════════════════
#  1. Chat Page — Main conversational interface
# ═══════════════════════════════════════════════════════

def render_chat_page() -> None:
    """Main chat interface powered by the LangGraph agent."""
    inject_global_css()

    st.markdown(
        '<div style="margin-bottom:4px;">'
        '<span style="font-size:13px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:1.5px;color:#E74C3C;">PRINT COLOR AGENT</span></div>',
        unsafe_allow_html=True,
    )
    st.title("印刷色彩预测与校准智能体")
    st.caption("输入您的色彩管理问题，智能体将调用专业工具为您分析。")

    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if user_input := st.chat_input("例如：帮我预测 C50 M30 Y80 K10 在 157g铜版纸 上的颜色"):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("正在分析中..."):
                try:
                    # Lazy agent initialization
                    if "agent" not in st.session_state:
                        from agent.core import create_agent
                        from tools import ALL_TOOLS
                        st.session_state.agent = create_agent(ALL_TOOLS)

                    from agent.core import run_agent_query
                    from agent.memory import get_chat_history

                    chat_history = get_chat_history()
                    response = run_agent_query(st.session_state.agent, user_input, chat_history)
                except Exception as e:
                    response = f"处理请求时出错：{e}"
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Sidebar controls
    with st.sidebar:
        st.markdown("### 会话控制")
        if st.button("清空对话历史", use_container_width=True):
            st.session_state.messages = []
            from agent.memory import clear_history
            clear_history()
            st.rerun()

        st.divider()
        st.markdown(
            '<div style="font-size:12px;color:#888;">'
            "智能体将自动调用色彩计算、知识库查询等工具。\n\n"
            "**支持的功能：**\n"
            "- 色彩预测\n"
            "- 色差计算\n"
            "- 校准建议\n"
            "- 知识查询\n"
            "- 历史记录\n"
            "- 文件解析"
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════
#  2. Color Prediction Page — Direct tool invocation
# ═══════════════════════════════════════════════════════

def render_predict_page() -> None:
    """Color prediction form — calls predict_print_color directly."""
    inject_global_css()

    st.markdown(
        '<span style="font-size:13px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:1.5px;color:#E74C3C;">COLOR PREDICTION</span>',
        unsafe_allow_html=True,
    )
    st.title("色彩预测")
    st.caption("输入CMYK色值和纸张类型，直接获取预测的CIE L*a*b*色彩值。")

    from models.paper_profiles import list_profiles
    profiles = list_profiles()

    # ── Prediction form ──
    with st.form("predict_form"):
        st.markdown('<div class="section-header">CMYK 输入</div>', unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            c = st.slider("C — 青色 (Cyan)", 0, 100, 50, key="pred_c")
            m = st.slider("M — 品红 (Magenta)", 0, 100, 30, key="pred_m")
        with col_c2:
            y = st.slider("Y — 黄色 (Yellow)", 0, 100, 80, key="pred_y")
            k = st.slider("K — 黑色 (Black)", 0, 100, 10, key="pred_k")

        paper = st.selectbox("纸张类型", profiles, key="pred_paper")
        submitted = st.form_submit_button("预测色彩", use_container_width=True)

    if submitted:
        with st.spinner("正在计算..."):
            from tools.color_tools import predict_print_color
            result = predict_print_color.invoke({"c": c, "m": m, "y": y, "k": k, "paper_type": paper})

        # Parse and display
        lab = parse_lab_from_result(result)
        if lab:
            st.markdown('<div class="section-header">预测结果</div>', unsafe_allow_html=True)

            col_swatch, col_values = st.columns([1, 2])
            with col_swatch:
                render_lab_swatch(lab[0], lab[1], lab[2], "预测色")
            with col_values:
                st.markdown(
                    f'<div class="result-panel">'
                    f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
                    f'<div class="metric-card"><div class="metric-label">L* 明度</div>'
                    f'<div class="metric-value">{lab[0]:.1f}</div></div>'
                    f'<div class="metric-card"><div class="metric-label">a* 红绿</div>'
                    f'<div class="metric-value">{lab[1]:.1f}</div></div>'
                    f'<div class="metric-card"><div class="metric-label">b* 黄蓝</div>'
                    f'<div class="metric-value">{lab[2]:.1f}</div></div>'
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.code(result, language=None)

    # ── Delta-E section ──
    st.divider()
    with st.expander("色差计算（可选） — 输入目标 Lab 值计算 ΔE"):
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            tL = st.number_input("目标 L*", -128.0, 128.0, 50.0, step=0.1, key="target_l")
        with col_t2:
            ta = st.number_input("目标 a*", -128.0, 128.0, 0.0, step=0.1, key="target_a")
        with col_t3:
            tb = st.number_input("目标 b*", -128.0, 128.0, 0.0, step=0.1, key="target_b")

        if st.button("计算色差"):
            if submitted and lab:
                from tools.color_tools import calculate_delta_e76
                de_result = calculate_delta_e76.invoke({
                    "lab1_l": lab[0], "lab1_a": lab[1], "lab1_b": lab[2],
                    "lab2_l": tL, "lab2_a": ta, "lab2_b": tb,
                })
                de_val = parse_delta_e_from_result(de_result)
                if de_val is not None:
                    st.markdown(format_delta_e_badge(de_val), unsafe_allow_html=True)
                st.code(de_result, language=None)
            else:
                st.warning("请先在上方进行色彩预测。")

    # Sidebar info
    with st.sidebar:
        st.markdown("### 色彩预测")
        st.markdown(
            '<div style="font-size:12px;color:#888;">'
            "直接调用色彩转换引擎，\n无需经过大语言模型。\n\n"
            "**输出说明：**\n"
            "- L*: 明度 (0=黑, 100=白)\n"
            "- a*: 红绿轴\n"
            "- b*: 黄蓝轴\n"
            "- ΔE: 色差值"
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════
#  3. Compare Page — Side-by-side paper comparison
# ═══════════════════════════════════════════════════════

def render_compare_page() -> None:
    """Compare the same CMYK color across two different paper types."""
    inject_global_css()

    st.markdown(
        '<span style="font-size:13px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:1.5px;color:#E74C3C;">PAPER COMPARISON</span>',
        unsafe_allow_html=True,
    )
    st.title("工艺参数对比")
    st.caption("同一色值在不同纸张上的色彩表现对比。")

    from models.paper_profiles import list_profiles
    profiles = list_profiles()

    # ── Shared CMYK input ──
    with st.form("compare_form"):
        st.markdown('<div class="section-header">CMYK 色值</div>', unsafe_allow_html=True)
        col_cm1, col_cm2 = st.columns(2)
        with col_cm1:
            c = st.slider("C", 0, 100, 50, key="cmp_c")
            m = st.slider("M", 0, 100, 30, key="cmp_m")
        with col_cm2:
            y = st.slider("Y", 0, 100, 80, key="cmp_y")
            k = st.slider("K", 0, 100, 10, key="cmp_k")

        st.markdown('<div class="section-header">纸张选择</div>', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            paper_a = st.selectbox("纸张 A", profiles, index=0, key="cmp_paper_a")
        with col_p2:
            default_b = 2 if len(profiles) > 2 else 1
            paper_b = st.selectbox("纸张 B", profiles, index=default_b, key="cmp_paper_b")

        submitted = st.form_submit_button("开始对比", use_container_width=True)

    if submitted:
        with st.spinner("正在计算两组预测..."):
            from tools.color_tools import predict_print_color, calculate_delta_e76

            result_a = predict_print_color.invoke({"c": c, "m": m, "y": y, "k": k, "paper_type": paper_a})
            result_b = predict_print_color.invoke({"c": c, "m": m, "y": y, "k": k, "paper_type": paper_b})

        lab_a = parse_lab_from_result(result_a)
        lab_b = parse_lab_from_result(result_b)

        if lab_a and lab_b:
            st.markdown('<div class="section-header">对比结果</div>', unsafe_allow_html=True)

            # Side by side
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**{paper_a}**")
                render_lab_swatch(lab_a[0], lab_a[1], lab_a[2])
                st.markdown(
                    f'<div class="result-panel">'
                    f"L*={lab_a[0]:.1f}  a*={lab_a[1]:.1f}  b*={lab_a[2]:.1f}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_b:
                st.markdown(f"**{paper_b}**")
                render_lab_swatch(lab_b[0], lab_b[1], lab_b[2])
                st.markdown(
                    f'<div class="result-panel">'
                    f"L*={lab_b[0]:.1f}  a*={lab_b[1]:.1f}  b*={lab_b[2]:.1f}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Delta-E between the two
            de_result = calculate_delta_e76.invoke({
                "lab1_l": lab_a[0], "lab1_a": lab_a[1], "lab1_b": lab_a[2],
                "lab2_l": lab_b[0], "lab2_a": lab_b[1], "lab2_b": lab_b[2],
            })
            de_val = parse_delta_e_from_result(de_result)

            st.divider()
            st.markdown(
                '<div class="section-header">两纸张间色差</div>',
                unsafe_allow_html=True,
            )
            if de_val is not None:
                st.markdown(format_delta_e_badge(de_val), unsafe_allow_html=True)
            st.code(de_result, language=None)

    # Sidebar
    with st.sidebar:
        st.markdown("### 对比分析")
        st.markdown(
            '<div style="font-size:12px;color:#888;">'
            "选择两种纸张，系统将分别\n"
            "计算同一CMYK色值的预测\n"
            "Lab值，并对比两者的色差。"
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════
#  4. Knowledge Base Page — FTS5 search
# ═══════════════════════════════════════════════════════

def render_knowledge_page() -> None:
    """Knowledge base search with FTS5 full-text search."""
    inject_global_css()

    st.markdown(
        '<span style="font-size:13px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:1.5px;color:#E74C3C;">KNOWLEDGE BASE</span>',
        unsafe_allow_html=True,
    )
    st.title("色彩知识库")
    st.caption("搜索印刷色彩管理专业术语、工艺参数、故障排除方法。")

    # Quick search tags
    st.markdown(
        '<div style="margin-bottom:16px;">'
        '<span style="font-size:12px;color:#888;margin-right:8px;">热门关键词：</span>'
        '<span style="background:#fef2f2;color:#E74C3C;padding:3px 10px;border-radius:12px;'
        'font-size:12px;margin-right:6px;cursor:pointer;">色差</span>'
        '<span style="background:#fef2f2;color:#E74C3C;padding:3px 10px;border-radius:12px;'
        'font-size:12px;margin-right:6px;cursor:pointer;">灰平衡</span>'
        '<span style="background:#fef2f2;color:#E74C3C;padding:3px 10px;border-radius:12px;'
        'font-size:12px;margin-right:6px;cursor:pointer;">网点扩大</span>'
        '<span style="background:#fef2f2;color:#E74C3C;padding:3px 10px;border-radius:12px;'
        'font-size:12px;margin-right:6px;cursor:pointer;">校准</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    query = st.text_input("搜索关键词", placeholder="输入关键词，如：色差、灰平衡、网点扩大...", label_visibility="collapsed")

    if query:
        with st.spinner("搜索中..."):
            from tools.knowledge_tools import query_knowledge_base
            result = query_knowledge_base.invoke({"query": query})

        if "未找到" in result:
            st.info(result)
        else:
            # Parse the result into individual articles and display as cards
            articles = re.split(r"\n(?=\d+\.)", result.strip())
            for article in articles:
                article = article.strip()
                if not article:
                    continue
                # Extract title and content
                title_match = re.search(r"【(.+?)】(.+)", article)
                if title_match:
                    category = title_match.group(1)
                    title = title_match.group(2).strip()
                    # Content is everything after the title line
                    content_lines = article.split("\n", 2)
                    content = content_lines[-1].strip() if len(content_lines) > 1 else ""
                    content = re.sub(r"^\s*\d+\.\s*", "", content).strip()

                    st.markdown(
                        f'<div class="kb-card">'
                        f'<span class="kb-title">{title}</span>'
                        f'<span class="kb-category">{category}</span>'
                        f'<div class="kb-content">{content}</div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(article)

    # Sidebar
    with st.sidebar:
        st.markdown("### 知识库")
        st.markdown(
            '<div style="font-size:12px;color:#888;">'
            "基于SQLite FTS5全文搜索，\n"
            "支持中文关键词匹配。\n\n"
            "**内容分类：**\n"
            "- 术语解释\n"
            "- 工艺参数\n"
            "- 故障排除\n"
            "- 校准方法"
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════
#  5. Calibration History Page
# ═══════════════════════════════════════════════════════

def render_history_page() -> None:
    """Calibration history browser with filters."""
    inject_global_css()

    st.markdown(
        '<span style="font-size:13px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:1.5px;color:#E74C3C;">CALIBRATION HISTORY</span>',
        unsafe_allow_html=True,
    )
    st.title("校准历史")
    st.caption("浏览过往校准记录，参考类似场景的历史方案。")

    from models.paper_profiles import list_profiles
    profiles = list_profiles()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        paper_filter = st.selectbox("纸张类型", ["全部"] + profiles, key="hist_paper")
    with col_f2:
        max_de = st.slider("最大色差 ΔE", 0.0, 20.0, 10.0, step=0.5, key="hist_de")

    paper_param = "" if paper_filter == "全部" else paper_filter

    with st.spinner("查询中..."):
        from tools.knowledge_tools import query_calibration_history
        result = query_calibration_history.invoke({
            "paper_type": paper_param,
            "max_delta_e": max_de,
        })

    if "未找到" in result:
        st.info(result)
    else:
        # Parse individual records
        records = re.split(r"\n(?=\d+\.)", result.strip())
        for record in records:
            record = record.strip()
            if not record:
                continue

            # Extract key info
            paper_match = re.search(r"\[(.+?)\]", record)
            de_match = re.search(r"ΔE=([\d.]+)", record)
            cmyk_match = re.search(r"CMYK\((\d+),(\d+),(\d+),(\d+)\)", record)
            advice_match = re.search(r"建议:\s*(.+)", record)
            notes_match = re.search(r"备注:\s*(.+)", record)

            paper_name = paper_match.group(1) if paper_match else "未知"
            de_val = float(de_match.group(1)) if de_match else 0.0
            advice = advice_match.group(1).strip() if advice_match else ""
            notes = notes_match.group(1).strip() if notes_match else ""

            badge = format_delta_e_badge(de_val)

            st.markdown(
                f'<div class="history-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                f'<span style="font-weight:600;font-size:15px;">{paper_name}</span>'
                f"{badge}"
                f"</div>"
                f'<div style="font-size:13px;color:#555;margin-bottom:4px;">'
                f"<strong>建议：</strong>{advice}</div>"
                f'<div style="font-size:12px;color:#888;">'
                f"<strong>备注：</strong>{notes}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Sidebar
    with st.sidebar:
        st.markdown("### 校准历史")
        st.markdown(
            '<div style="font-size:12px;color:#888;">'
            "浏览历史校准记录，\n"
            "按纸张类型和色差范围筛选。\n\n"
            "每条记录包含：\n"
            "- 目标色与预测色\n"
            "- 色差ΔE值\n"
            "- 校准建议\n"
            "- 操作员备注"
            "</div>",
            unsafe_allow_html=True,
        )
