"""Color calculation tools for LangChain agent binding.

Each tool uses @tool decorator with Pydantic args_schema for strict input validation.
"""

from __future__ import annotations

import math

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class PredictColorInput(BaseModel):
    """Input schema for predict_print_color tool."""

    c: float = Field(description="Cyan ink percentage (0-100)")
    m: float = Field(description="Magenta ink percentage (0-100)")
    y: float = Field(description="Yellow ink percentage (0-100)")
    k: float = Field(description="Black ink percentage (0-100)")
    paper_type: str = Field(description="Paper type name, e.g. '157g铜版纸'")


@tool(args_schema=PredictColorInput)
def predict_print_color(c: float, m: float, y: float, k: float, paper_type: str) -> str:
    """预测给定CMYK色值在指定纸张上的印刷色彩（CIE L*a*b*值）。

    输入CMYK四色墨量百分比和纸张类型，返回预测的CIE L*a*b*色彩值。
    适用于印前色彩预测、色彩对比分析等场景。
    """
    # Validate CMYK range
    for name, val in [("C", c), ("M", m), ("Y", y), ("K", k)]:
        if not (0 <= val <= 100):
            return f"错误：{name}值必须在0-100之间，当前值为{val}"

    from models.paper_profiles import get_profile
    from models.converter import ColorConverter

    profile = get_profile(paper_type)
    if profile is None:
        from models.paper_profiles import list_profiles
        available = ", ".join(list_profiles())
        return f"错误：未找到纸张类型'{paper_type}'。可用的纸张类型：{available}"

    converter = ColorConverter(profile)
    lab = converter.cmyk_to_lab(c, m, y, k)

    return (
        f"预测结果（{paper_type}）：\n"
        f"  输入CMYK: C={c:.0f}%, M={m:.0f}%, Y={y:.0f}%, K={k:.0f}%\n"
        f"  预测Lab: L*={lab[0]:.1f}, a*={lab[1]:.1f}, b*={lab[2]:.1f}\n"
        f"  纸张白点: L*={profile.white_point[0]:.1f}, a*={profile.white_point[1]:.1f}, b*={profile.white_point[2]:.1f}"
    )


class DeltaEInput(BaseModel):
    """Input schema for calculate_delta_e76 tool."""

    lab1_l: float = Field(description="First color's L* value")
    lab1_a: float = Field(description="First color's a* value")
    lab1_b: float = Field(description="First color's b* value")
    lab2_l: float = Field(description="Second color's L* value")
    lab2_a: float = Field(description="Second color's a* value")
    lab2_b: float = Field(description="Second color's b* value")


@tool(args_schema=DeltaEInput)
def calculate_delta_e76(
    lab1_l: float, lab1_a: float, lab1_b: float,
    lab2_l: float, lab2_a: float, lab2_b: float,
) -> str:
    """计算两个CIE L*a*b*颜色之间的ΔE76色差。

    返回色差值和可感知性判断。色差标准：ΔE<1 不可感知，1-3 可感知，3-6 明显，>6 显著。
    """
    delta_l = lab1_l - lab2_l
    delta_a = lab1_a - lab2_a
    delta_b = lab1_b - lab2_b
    delta_e = math.sqrt(delta_l**2 + delta_a**2 + delta_b**2)

    # Interpret the delta-E value
    if delta_e < 1.0:
        interpretation = "不可感知差异"
    elif delta_e < 3.0:
        interpretation = "可感知但不明显"
    elif delta_e < 6.0:
        interpretation = "明显差异"
    else:
        interpretation = "显著差异"

    return (
        f"ΔE76色差计算结果：\n"
        f"  颜色1: L*={lab1_l:.1f}, a*={lab1_a:.1f}, b*={lab1_b:.1f}\n"
        f"  颜色2: L*={lab2_l:.1f}, a*={lab2_a:.1f}, b*={lab2_b:.1f}\n"
        f"  ΔL*={delta_l:+.1f}, Δa*={delta_a:+.1f}, Δb*={delta_b:+.1f}\n"
        f"  ΔE={delta_e:.1f}（{interpretation}）"
    )


class CalibrationInput(BaseModel):
    """Input schema for generate_calibration_advice tool."""

    predicted_l: float = Field(description="Predicted color L* value")
    predicted_a: float = Field(description="Predicted color a* value")
    predicted_b: float = Field(description="Predicted color b* value")
    target_l: float = Field(description="Target color L* value")
    target_a: float = Field(description="Target color a* value")
    target_b: float = Field(description="Target color b* value")


@tool(args_schema=CalibrationInput)
def generate_calibration_advice(
    predicted_l: float, predicted_a: float, predicted_b: float,
    target_l: float, target_a: float, target_b: float,
) -> str:
    """基于预测色与目标色的差异，生成具体的墨量调整校准建议。

    比较预测色和目标色的L*a*b*值，分析色差方向，给出CMYK墨量调整建议。
    """
    from models.calibration_rules import generate_calibration_advice as _gen_advice, advice_to_text

    predicted = (predicted_l, predicted_a, predicted_b)
    target = (target_l, target_a, target_b)

    # Calculate delta-E first
    delta_e = math.sqrt(
        (predicted_l - target_l)**2 +
        (predicted_a - target_a)**2 +
        (predicted_b - target_b)**2
    )

    advice_list = _gen_advice(predicted, target)
    advice_text = advice_to_text(advice_list)

    return (
        f"校准建议报告：\n"
        f"  预测色: L*={predicted_l:.1f}, a*={predicted_a:.1f}, b*={predicted_b:.1f}\n"
        f"  目标色: L*={target_l:.1f}, a*={target_a:.1f}, b*={target_b:.1f}\n"
        f"  色差ΔE: {delta_e:.1f}\n\n"
        f"调整建议：\n{advice_text}"
    )
