"""Delta L/a/b to ink adjustment rule engine.

Maps color difference directions to specific, actionable ink adjustment recommendations.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

# Perceptibility threshold — adjustments are suggested only when delta exceeds this
THRESHOLD_DELTA_E = 3.0

# Smaller threshold for individual L/a/b components
THRESHOLD_COMPONENT = 2.0


class AdviceItem(BaseModel):
    """A single calibration recommendation."""

    channel: str = Field(description="Ink channel: C, M, Y, K, or '总墨量'")
    direction: Literal["increase", "decrease"] = Field(description="Adjustment direction")
    amount_min: float = Field(description="Minimum adjustment percentage")
    amount_max: float = Field(description="Maximum adjustment percentage")
    reason: str = Field(description="Human-readable explanation in Chinese")


def _calc_adjustment_range(delta: float) -> tuple[float, float]:
    """Map a delta magnitude to an adjustment percentage range.

    Larger deltas require larger adjustments. Returns (min%, max%).
    """
    abs_delta = abs(delta)
    if abs_delta < 3.0:
        return (1.0, 3.0)
    elif abs_delta < 6.0:
        return (3.0, 5.0)
    elif abs_delta < 10.0:
        return (5.0, 8.0)
    else:
        return (8.0, 12.0)


def generate_calibration_advice(
    predicted_lab: tuple[float, float, float],
    target_lab: tuple[float, float, float],
) -> list[AdviceItem]:
    """Generate ink adjustment advice based on predicted vs target Lab values.

    Rules:
    - delta_b > threshold: predicted yellower than target -> decrease Y
    - delta_b < -threshold: predicted bluer than target -> increase Y
    - delta_a > threshold: predicted redder than target -> decrease M
    - delta_a < -threshold: predicted greener than target -> increase M
    - delta_L > threshold: predicted lighter -> increase total ink / decrease K
    - delta_L < -threshold: predicted darker -> decrease total ink / increase K
    """
    L_pred, a_pred, b_pred = predicted_lab
    L_target, a_target, b_target = target_lab

    delta_L = L_pred - L_target
    delta_a = a_pred - a_target
    delta_b = b_pred - b_target

    advice: list[AdviceItem] = []

    # Delta b rules (yellow-blue axis)
    if delta_b > THRESHOLD_COMPONENT:
        adj = _calc_adjustment_range(delta_b)
        advice.append(AdviceItem(
            channel="Y",
            direction="decrease",
            amount_min=adj[0],
            amount_max=adj[1],
            reason=f"预测色比目标色偏黄(Δb=+{delta_b:.1f})，建议减少黄色油墨",
        ))
    elif delta_b < -THRESHOLD_COMPONENT:
        adj = _calc_adjustment_range(delta_b)
        advice.append(AdviceItem(
            channel="Y",
            direction="increase",
            amount_min=adj[0],
            amount_max=adj[1],
            reason=f"预测色比目标色偏蓝(Δb={delta_b:.1f})，建议增加黄色油墨",
        ))

    # Delta a rules (red-green axis)
    if delta_a > THRESHOLD_COMPONENT:
        adj = _calc_adjustment_range(delta_a)
        advice.append(AdviceItem(
            channel="M",
            direction="decrease",
            amount_min=adj[0],
            amount_max=adj[1],
            reason=f"预测色比目标色偏红(Δa=+{delta_a:.1f})，建议减少品红色油墨",
        ))
    elif delta_a < -THRESHOLD_COMPONENT:
        adj = _calc_adjustment_range(delta_a)
        advice.append(AdviceItem(
            channel="M",
            direction="increase",
            amount_min=adj[0],
            amount_max=adj[1],
            reason=f"预测色比目标色偏绿(Δa={delta_a:.1f})，建议增加品红色油墨",
        ))

    # Delta L rules (lightness)
    if abs(delta_L) > THRESHOLD_COMPONENT:
        adj = _calc_adjustment_range(delta_L)
        if delta_L > 0:
            # Predicted lighter than target — need more ink
            advice.append(AdviceItem(
                channel="总墨量",
                direction="increase",
                amount_min=adj[0],
                amount_max=adj[1],
                reason=f"预测色比目标色偏亮(ΔL=+{delta_L:.1f})，建议适当增加CMY墨量",
            ))
        else:
            # Predicted darker than target — reduce ink or adjust K
            advice.append(AdviceItem(
                channel="K",
                direction="decrease",
                amount_min=adj[0],
                amount_max=adj[1],
                reason=f"预测色比目标色偏暗(ΔL={delta_L:.1f})，建议适当减少黑色墨量或总墨量",
            ))

    # If no significant difference
    if not advice:
        total_delta_e = math.sqrt(delta_L**2 + delta_a**2 + delta_b**2)
        if total_delta_e < 1.0:
            advice.append(AdviceItem(
                channel="无",
                direction="increase",
                amount_min=0.0,
                amount_max=0.0,
                reason=f"色差ΔE={total_delta_e:.1f}，不可感知，无需调整",
            ))
        else:
            advice.append(AdviceItem(
                channel="无",
                direction="increase",
                amount_min=0.0,
                amount_max=0.0,
                reason=f"色差ΔE={total_delta_e:.1f}，在可接受范围内，可视情况微调",
            ))

    return advice


def advice_to_text(advice_list: list[AdviceItem]) -> str:
    """Format a list of AdviceItem into a human-readable Chinese string."""
    if not advice_list:
        return "无校准建议。"

    lines: list[str] = []
    for i, item in enumerate(advice_list, 1):
        if item.channel == "无":
            lines.append(f"{i}. {item.reason}")
        else:
            dir_text = "增加" if item.direction == "increase" else "减少"
            lines.append(
                f"{i}. {item.reason}：建议{dir_text}{item.channel}油墨 "
                f"{item.amount_min:.0f}%-{item.amount_max:.0f}%"
            )
    return "\n".join(lines)
