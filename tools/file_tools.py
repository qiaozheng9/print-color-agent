"""File parsing tools for extracting color data from uploaded design files.

Supports PDF (via PyMuPDF), JPEG, and TIFF (via Pillow).
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ExtractColorInput(BaseModel):
    """Input schema for extract_color_from_file tool."""

    file_path: str = Field(description="Absolute path to the uploaded design file (PDF/JPEG/TIFF)")
    region: str = Field(
        default="auto",
        description="Extraction region: 'auto' for automatic dominant color detection",
    )


def _extract_from_image(img) -> list[tuple[float, float, float, float]]:
    """Extract dominant CMYK colors from a PIL Image.

    Converts RGB to CMYK using a simplified formula, then clusters by frequency.
    Returns top 5 dominant colors as (C, M, Y, K) tuples (0-100).
    """
    # Convert to RGB if needed
    if img.mode == "CMYK":
        # Already CMYK — sample pixels directly
        pixels = list(img.getdata())
    elif img.mode in ("RGB", "RGBA"):
        pixels = list(img.convert("RGB").getdata())
        # Convert RGB to CMYK
        cmyk_pixels = []
        for r, g, b in pixels:
            r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
            k = 1.0 - max(r_norm, g_norm, b_norm)
            if k >= 1.0:
                cmyk_pixels.append((0.0, 0.0, 0.0, 100.0))
            else:
                c = (1.0 - r_norm - k) / (1.0 - k) * 100.0
                m = (1.0 - g_norm - k) / (1.0 - k) * 100.0
                y = (1.0 - b_norm - k) / (1.0 - k) * 100.0
                cmyk_pixels.append((round(c, 1), round(m, 1), round(y, 1), round(k * 100.0, 1)))
        pixels = cmyk_pixels
    else:
        return []

    # Quantize to reduce color space (round to nearest 5%)
    def quantize(c: float, m: float, y: float, k: float) -> tuple[int, int, int, int]:
        return (round(c / 5) * 5, round(m / 5) * 5, round(y / 5) * 5, round(k / 5) * 5)

    # Count frequency of quantized colors
    from collections import Counter
    color_counts = Counter()
    for p in pixels:
        if isinstance(p, tuple) and len(p) >= 4:
            q = quantize(p[0], p[1], p[2], p[3])
            color_counts[q] += 1

    # Return top 5 most frequent colors
    top_colors = color_counts.most_common(5)
    return [(float(c), float(m), float(y), float(k)) for (c, m, y, k), _ in top_colors]


@tool(args_schema=ExtractColorInput)
def extract_color_from_file(file_path: str, region: str = "auto") -> str:
    """从上传的设计文件（PDF/TIFF/JPEG）中提取主要CMYK色值。

    自动检测文件类型并提取主要色彩。支持PDF（通过PyMuPDF）和图片（通过Pillow）。
    返回文件中出现频率最高的5种颜色的CMYK值。
    """
    path = Path(file_path)
    if not path.exists():
        return f"错误：文件不存在 - {file_path}"

    suffix = path.suffix.lower()
    colors: list[tuple[float, float, float, float]] = []

    try:
        if suffix == ".pdf":
            import fitz  # PyMuPDF

            doc = fitz.open(str(path))
            for page_num in range(min(len(doc), 3)):  # Process first 3 pages
                page = doc[page_num]
                # Extract images from the page
                image_list = page.get_images(full=True)
                for img_info in image_list:
                    xref = img_info[0]
                    try:
                        base_image = doc.extract_image(xref)
                        if base_image:
                            from io import BytesIO
                            from PIL import Image

                            img = Image.open(BytesIO(base_image["image"]))
                            page_colors = _extract_from_image(img)
                            colors.extend(page_colors)
                    except Exception:
                        continue
            doc.close()

        elif suffix in (".jpg", ".jpeg", ".tiff", ".tif", ".png", ".bmp"):
            from PIL import Image

            img = Image.open(str(path))
            colors = _extract_from_image(img)

        else:
            return f"错误：不支持的文件格式'{suffix}'。支持的格式：PDF, JPEG, TIFF, PNG, BMP"

    except ImportError as e:
        return f"错误：缺少必要的库 - {e}。请确保已安装PyMuPDF和Pillow。"
    except Exception as e:
        return f"错误：文件解析失败 - {e}"

    if not colors:
        return "未能从文件中提取到有效的色彩数据。可能原因：文件为空、图片模式不支持或文件损坏。"

    # Deduplicate and format
    seen = set()
    unique_colors = []
    for c, m, y, k in colors:
        key = (c, m, y, k)
        if key not in seen:
            seen.add(key)
            unique_colors.append((c, m, y, k))

    lines = [f"从文件 '{path.name}' 中提取到 {len(unique_colors)} 种主要颜色："]
    for i, (c, m, y, k) in enumerate(unique_colors[:5], 1):
        lines.append(f"  颜色{i}: C={c:.0f}%, M={m:.0f}%, Y={y:.0f}%, K={k:.0f}%")

    return "\n".join(lines)
