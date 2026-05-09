"""Display helpers — Lab swatches, delta-E badges, report formatters."""

from __future__ import annotations

import re

import streamlit as st


def _lab_to_rgb(L: float, a: float, b: float) -> tuple[int, int, int]:
    """Convert CIE L*a*b* to sRGB (0-255) via XYZ, D65 illuminant."""
    # Lab -> XYZ
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    delta = 6.0 / 29.0
    xn, yn, zn = 95.047, 100.000, 108.883

    def f_inv(t: float) -> float:
        return t**3 if t > delta else 3.0 * delta**2 * (t - 4.0 / 29.0)

    x = f_inv(fx) * xn / 100.0
    y = f_inv(fy) * yn / 100.0
    z = f_inv(fz) * zn / 100.0

    # XYZ -> linear sRGB
    r_lin = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g_lin = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b_lin = 0.0557 * x - 0.2040 * y + 1.0570 * z

    # Gamma correction + clamp
    def gamma(v: float) -> int:
        v = max(0.0, min(1.0, v))
        return int(round((1.055 * (v ** (1.0 / 2.4)) - 0.055) if v > 0.0031308 else v * 12.92, 0) * 255)

    return (gamma(r_lin), gamma(g_lin), gamma(b_lin))


def render_lab_swatch(L: float, a: float, b: float, label: str = "") -> None:
    """Render a colored block representing the given L*a*b* color."""
    r, g, bl = _lab_to_rgb(L, a, b)
    hex_color = f"#{r:02x}{g:02x}{bl:02x}"
    label_html = f'<span style="margin-left:12px;font-size:14px;color:#555;">{label}</span>' if label else ""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;margin:8px 0;">
            <div style="
                width:64px;height:64px;border-radius:8px;
                background:{hex_color};
                border:2px solid #e0e0e0;
                box-shadow:0 2px 8px rgba(0,0,0,0.10);
                flex-shrink:0;
            "></div>
            {label_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_lab_swatch_inline(L: float, a: float, b: float, size: int = 48) -> str:
    """Return an inline HTML string for a Lab color swatch (for use in columns)."""
    r, g, bl = _lab_to_rgb(L, a, b)
    hex_color = f"#{r:02x}{g:02x}{bl:02x}"
    return (
        f'<div style="'
        f"width:{size}px;height:{size}px;border-radius:6px;"
        f"background:{hex_color};"
        f"border:2px solid #e0e0e0;"
        f"box-shadow:0 1px 4px rgba(0,0,0,0.08);"
        f'display:inline-block;"></div>'
    )


def format_delta_e_badge(delta_e: float) -> str:
    """Return a colored badge string based on delta-E threshold."""
    if delta_e < 1.0:
        color, bg, text = "#2e7d32", "#e8f5e9", "不可感知"
    elif delta_e < 3.0:
        color, bg, text = "#f57f17", "#fffde7", "可感知"
    elif delta_e < 6.0:
        color, bg, text = "#e65100", "#fff3e0", "明显差异"
    else:
        color, bg, text = "#c62828", "#ffebee", "显著差异"
    return (
        f'<span style="'
        f"background:{bg};color:{color};"
        f"padding:4px 12px;border-radius:12px;"
        f"font-weight:600;font-size:13px;"
        f'display:inline-block;">'
        f"ΔE={delta_e:.1f}  {text}"
        f"</span>"
    )


def parse_lab_from_result(result_text: str) -> tuple[float, float, float] | None:
    """Extract L*, a*, b* values from a tool result string using regex."""
    match = re.search(r"L\*=\s*([-\d.]+).*?a\*=\s*([-\d.]+).*?b\*=\s*([-\d.]+)", result_text)
    if match:
        return (float(match.group(1)), float(match.group(2)), float(match.group(3)))
    return None


def parse_delta_e_from_result(result_text: str) -> float | None:
    """Extract delta-E value from a tool result string."""
    match = re.search(r"ΔE=\s*([-\d.]+)", result_text)
    if match:
        return float(match.group(1))
    return None


# ──────────────────────────────────────────────────────
#  Global CSS — injected once via st.markdown
# ──────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
/* ── CMYK color tokens ── */
:root {
    --cmyk-cyan:    #00aeef;
    --cmyk-magenta: #ec008c;
    --cmyk-yellow:  #fff200;
    --cmyk-black:   #1a1a1a;
    --accent-red:   #E74C3C;
    --surface:      #fafafa;
    --surface-alt:  #f0f2f5;
    --text-primary: #1a1a1a;
    --text-muted:   #6b7280;
    --radius:       10px;
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%);
}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] div {
    color: #f0f0f0 !important;
}
/* Active/selected nav link highlight */
[data-testid="stSidebar"] a[aria-current="page"] {
    color: #ffffff !important;
    font-weight: 700 !important;
    background: rgba(231,76,60,0.25) !important;
    border-radius: 6px !important;
}
/* Nav group headers */
[data-testid="stSidebar"] [data-testid="stMarkdown"] strong,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {
    color: #ffffff !important;
}
/* Sidebar selectbox styling */
[data-testid="stSidebar"] [data-testid="stSelectbox"] label {
    color: #e0e0e0 !important;
}
/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    color: #ffffff !important;
    background: rgba(231,76,60,0.15) !important;
    border: 1px solid rgba(231,76,60,0.5) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(231,76,60,0.35) !important;
    border-color: #E74C3C !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
}

/* ── Metric cards ── */
.metric-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-card .metric-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 4px 0;
}
.metric-card .metric-label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Result panel ── */
.result-panel {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── Section headers ── */
.section-header {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent-red);
    display: inline-block;
}

/* ── Knowledge result cards ── */
.kb-card {
    background: white;
    border-left: 4px solid var(--accent-red);
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin: 8px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.kb-card .kb-title {
    font-weight: 600;
    font-size: 15px;
    color: var(--text-primary);
}
.kb-card .kb-category {
    display: inline-block;
    background: #fef2f2;
    color: var(--accent-red);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    margin-left: 8px;
}
.kb-card .kb-content {
    margin-top: 8px;
    font-size: 14px;
    color: #374151;
    line-height: 1.6;
}

/* ── History record cards ── */
.history-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.history-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

/* ── CMYK dots ── */
.cmyk-dots {
    display: flex;
    gap: 6px;
    margin: 4px 0;
}
.cmyk-dot {
    width: 20px; height: 20px;
    border-radius: 50%;
    border: 2px solid #e0e0e0;
    display: inline-block;
}

/* ── Form styling ── */
[data-testid="stForm"] {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 8px;
}

/* ── Button override ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(231,76,60,0.25);
}
</style>
"""


def inject_global_css() -> None:
    """Inject the global CSS into the Streamlit page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
