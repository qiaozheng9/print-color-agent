"""Paper type definitions and conversion matrix profiles."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field


class PaperProfile(BaseModel):
    """Defines a paper type's physical properties and color conversion parameters."""

    name: str = Field(description="Paper type name, e.g. '157g铜版纸'")
    weight_gsm: int = Field(description="Paper weight in grams per square meter")
    surface: Literal["glossy", "matte", "uncoated"] = Field(description="Paper surface finish")
    dot_gain_pct: float = Field(default=15.0, description="Dot gain percentage")
    max_ink_pct: float = Field(default=340.0, description="Total ink coverage limit")
    white_point: tuple[float, float, float] = Field(
        default=(95.0, 0.0, 0.0),
        description="Paper white point in CIE L*a*b* (L*, a*, b*)",
    )
    conversion_matrix: list[list[float]] = Field(
        description="4x3 matrix for CMYK-to-XYZ conversion. Each row is [C, M, Y, K] coefficients for X, Y, Z.",
    )

    def dot_gain_factor(self) -> float:
        """Return dot gain as a fractional factor for correction calculations."""
        return self.dot_gain_pct / 100.0


# Default profiles — used as fallback when DB is unavailable
# Matrix format: 3x4 (rows=X,Y,Z; cols=C,M,Y,K absorption coefficients)
# Subtractive model: reflectance = 1 - matrix @ cmyk; XYZ = paper_white_XYZ * reflectance
# Row sums must be <= 0.95 to leave 5% minimum reflectance at full ink coverage.
# Realistic values based on typical CMYK ink absorption characteristics.
_DEFAULT_PROFILES: dict[str, PaperProfile] = {
    "157g铜版纸": PaperProfile(
        name="157g铜版纸",
        weight_gsm=157,
        surface="glossy",
        dot_gain_pct=14.0,
        max_ink_pct=340.0,
        white_point=(95.0, 0.5, -1.5),
        conversion_matrix=[
            [0.20, 0.04, 0.01, 0.70],  # X: absorbs red; row sum=0.95
            [0.04, 0.55, 0.04, 0.32],  # Y: absorbs green; row sum=0.95
            [0.01, 0.05, 0.75, 0.14],  # Z: absorbs blue; row sum=0.95
        ],
    ),
    "128g铜版纸": PaperProfile(
        name="128g铜版纸",
        weight_gsm=128,
        surface="glossy",
        dot_gain_pct=15.0,
        max_ink_pct=330.0,
        white_point=(93.0, 0.5, -1.0),
        conversion_matrix=[
            [0.19, 0.04, 0.01, 0.68],
            [0.04, 0.53, 0.04, 0.31],
            [0.01, 0.05, 0.73, 0.13],
        ],
    ),
    "80g双胶纸": PaperProfile(
        name="80g双胶纸",
        weight_gsm=80,
        surface="uncoated",
        dot_gain_pct=20.0,
        max_ink_pct=300.0,
        white_point=(90.0, 1.0, -3.0),
        conversion_matrix=[
            [0.18, 0.04, 0.01, 0.65],
            [0.04, 0.50, 0.04, 0.29],
            [0.01, 0.05, 0.70, 0.12],
        ],
    ),
    "105g哑粉纸": PaperProfile(
        name="105g哑粉纸",
        weight_gsm=105,
        surface="matte",
        dot_gain_pct=16.0,
        max_ink_pct=320.0,
        white_point=(92.0, 0.8, -2.0),
        conversion_matrix=[
            [0.19, 0.04, 0.01, 0.67],
            [0.04, 0.52, 0.04, 0.30],
            [0.01, 0.05, 0.72, 0.13],
        ],
    ),
}


def get_profile(name: str) -> PaperProfile | None:
    """Get a paper profile by name. Tries DB first, falls back to defaults."""
    try:
        from database.dao import PaperTypeDAO

        row = PaperTypeDAO.get_by_name(name)
        if row:
            matrix = json.loads(row["conversion_matrix"])
            return PaperProfile(
                name=row["name"],
                weight_gsm=row["weight_gsm"],
                surface=row["surface"],
                dot_gain_pct=row["dot_gain_pct"],
                max_ink_pct=row["max_ink_pct"],
                white_point=(row["white_point_l"], row["white_point_a"], row["white_point_b"]),
                conversion_matrix=matrix,
            )
    except Exception:
        pass
    return _DEFAULT_PROFILES.get(name)


def list_profiles() -> list[str]:
    """Return all available paper type names."""
    try:
        from database.dao import PaperTypeDAO

        rows = PaperTypeDAO.get_all()
        if rows:
            return [r["name"] for r in rows]
    except Exception:
        pass
    return list(_DEFAULT_PROFILES.keys())
