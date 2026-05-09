"""Knowledge base and calibration history query tools.

Uses FTS5 full-text search for knowledge articles and parameterized queries
for calibration history records.
"""

from __future__ import annotations

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class QueryKnowledgeInput(BaseModel):
    """Input schema for query_knowledge_base tool."""

    query: str = Field(description="Search query in Chinese, e.g. '色差', '灰平衡', '网点扩大'")


@tool(args_schema=QueryKnowledgeInput)
def query_knowledge_base(query: str) -> str:
    """在色彩管理知识库中搜索相关信息。

    用于回答印刷色彩专业术语、工艺参数、故障排除方法等问题。
    使用FTS5全文搜索，支持中文关键词匹配。
    """
    from database.dao import KnowledgeDAO

    results = KnowledgeDAO.search(query, limit=5)

    if not results:
        return f"知识库中未找到与'{query}'相关的内容。请尝试其他关键词，如：CMYK、色差、网点扩大、灰平衡、校准。"

    lines = [f"找到 {len(results)} 条与'{query}'相关的知识：\n"]
    for i, r in enumerate(results, 1):
        # Truncate content for preview
        content_preview = r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
        lines.append(
            f"{i}. 【{r['category']}】{r['title']}\n"
            f"   {content_preview}\n"
        )

    return "\n".join(lines)


class QueryHistoryInput(BaseModel):
    """Input schema for query_calibration_history tool."""

    paper_type: str = Field(
        default="",
        description="Filter by paper type name, e.g. '157g铜版纸'. Empty string for all types.",
    )
    max_delta_e: float = Field(
        default=10.0,
        description="Maximum delta-E filter. Only return records with delta-E <= this value.",
    )


@tool(args_schema=QueryHistoryInput)
def query_calibration_history(paper_type: str = "", max_delta_e: float = 10.0) -> str:
    """查询历史校准记录。可按纸张类型和色差范围筛选。

    返回过往的校准案例，包括输入参数、预测结果、色差和校准建议。
    用于参考类似场景的历史校准方案。
    """
    from database.dao import CalibrationDAO

    paper_filter = paper_type if paper_type else None
    records = CalibrationDAO.search(
        paper_type=paper_filter,
        max_delta_e=max_delta_e,
        limit=10,
    )

    if not records:
        filter_desc = f"纸张'{paper_type}'" if paper_type else "所有纸张"
        return f"未找到符合条件的校准记录（{filter_desc}，ΔE≤{max_delta_e}）。"

    lines = [f"找到 {len(records)} 条校准记录：\n"]
    for i, r in enumerate(records, 1):
        target_lab = f"L*={r['target_l']:.1f}, a*={r['target_a']:.1f}, b*={r['target_b']:.1f}" if r['target_l'] is not None else "未记录"
        predicted_lab = f"L*={r['predicted_l']:.1f}, a*={r['predicted_a']:.1f}, b*={r['predicted_b']:.1f}" if r['predicted_l'] is not None else "未记录"

        lines.append(
            f"{i}. [{r['paper_type']}] ΔE={r['delta_e']:.1f}\n"
            f"   目标色: CMYK({r['target_c']:.0f},{r['target_m']:.0f},{r['target_y']:.0f},{r['target_k']:.0f})\n"
            f"   目标Lab: {target_lab}\n"
            f"   预测Lab: {predicted_lab}\n"
            f"   建议: {r['advice_summary']}\n"
            f"   备注: {r['operator_notes']}\n"
        )

    return "\n".join(lines)
