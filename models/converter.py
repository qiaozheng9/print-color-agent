"""CMYK-to-Lab color conversion engine.

Uses a subtractive model: ink reduces the paper's reflectance.
XYZ = paper_white_XYZ * (1 - absorption), where absorption is computed
from a per-paper matrix applied to the dot-gain-corrected CMYK values.

Falls back to simplified empirical formulas when no conversion matrix is available.
"""

from __future__ import annotations

import math

import numpy as np

from models.paper_profiles import PaperProfile


def _apply_dot_gain(value: float, factor: float) -> float:
    """Apply dot gain correction to a single channel value (0.0-1.0).

    Uses the Murray-Davies model: adjusted = value + factor * value * (1 - value)
    """
    return value + factor * value * (1.0 - value)


def _lab_to_xyz(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Convert CIE L*a*b* to CIE XYZ (D65 illuminant, 0-100 scale)."""
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    delta = 6.0 / 29.0
    xn, yn, zn = 95.047, 100.000, 108.883

    def f_inv(t: float) -> float:
        if t > delta:
            return t**3
        return 3.0 * delta**2 * (t - 4.0 / 29.0)

    return (f_inv(fx) * xn, f_inv(fy) * yn, f_inv(fz) * zn)


def _xyz_to_lab(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Convert CIE XYZ to CIE L*a*b* (D65 illuminant, 0-100 scale)."""
    xn, yn, zn = 95.047, 100.000, 108.883

    def f(t: float) -> float:
        delta = 6.0 / 29.0
        if t > delta**3:
            return t ** (1.0 / 3.0)
        return t / (3.0 * delta**2) + 4.0 / 29.0

    fx = f(x / xn)
    fy = f(y / yn)
    fz = f(z / zn)

    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return (L, a, b)


def _simplified_cmyk_to_lab(
    c: float, m: float, y: float, k: float, paper: PaperProfile
) -> tuple[float, float, float]:
    """Simplified CMYK-to-Lab conversion using empirical formulas.

    Used as fallback when no conversion matrix is available.
    """
    cn = max(0.0, min(1.0, c / 100.0))
    mn = max(0.0, min(1.0, m / 100.0))
    yn = max(0.0, min(1.0, y / 100.0))
    kn = max(0.0, min(1.0, k / 100.0))

    dg = paper.dot_gain_factor()
    cn = _apply_dot_gain(cn, dg)
    mn = _apply_dot_gain(mn, dg)
    yn = _apply_dot_gain(yn, dg)
    kn = _apply_dot_gain(kn, dg)

    total_ink = cn + mn + yn + kn
    L = paper.white_point[0] * (1.0 - total_ink * 0.2)
    a = (mn - cn) * 50.0 + paper.white_point[1]
    b = (yn - cn) * 50.0 + paper.white_point[2]

    return (
        max(0.0, min(100.0, L)),
        max(-128.0, min(127.0, a)),
        max(-128.0, min(127.0, b)),
    )


class ColorConverter:
    """Converts CMYK values to CIE L*a*b* using paper-specific profiles.

    Uses a subtractive model:
        reflectance = 1 - matrix @ cmyk_vec
        XYZ = paper_white_XYZ * reflectance

    Where the matrix encodes per-channel absorption coefficients in XYZ space.
    This ensures:
        - CMYK(0,0,0,0) -> paper white
        - CMYK(100,100,100,100) -> very dark (low reflectance)
    """

    def __init__(self, paper: PaperProfile) -> None:
        self.paper = paper
        # Matrix shape (3, 4): rows = X,Y,Z channels; cols = C,M,Y,K absorption
        self._matrix = np.array(paper.conversion_matrix, dtype=np.float64)
        # Paper white in XYZ
        self._paper_xyz = np.array(
            _lab_to_xyz(*paper.white_point), dtype=np.float64
        )

    def cmyk_to_lab(self, c: float, m: float, y: float, k: float) -> tuple[float, float, float]:
        """Convert CMYK (0-100) to CIE L*a*b*.

        1. Validate and clamp CMYK to 0-100
        2. Normalize to 0-1
        3. Apply dot gain correction
        4. Compute reflectance = 1 - matrix @ cmyk (clamped to >= 0)
        5. XYZ = paper_white_XYZ * reflectance
        6. Convert XYZ to Lab
        """
        c = max(0.0, min(100.0, c))
        m = max(0.0, min(100.0, m))
        y = max(0.0, min(100.0, y))
        k = max(0.0, min(100.0, k))

        # Normalize to 0-1
        cmyk_vec = np.array([c, m, y, k], dtype=np.float64) / 100.0

        # Apply dot gain correction per channel
        dg = self.paper.dot_gain_factor()
        for i in range(4):
            cmyk_vec[i] = _apply_dot_gain(cmyk_vec[i], dg)
            cmyk_vec[i] = min(max(cmyk_vec[i], 0.0), 1.0)

        # Subtractive model: absorption = matrix @ cmyk_vec
        absorption = self._matrix @ cmyk_vec  # shape (3,)

        # Reflectance = 1 - absorption, clamped to [0, 1]
        reflectance = np.clip(1.0 - absorption, 0.0, 1.0)

        # XYZ = paper white * reflectance
        xyz = self._paper_xyz * reflectance

        # Convert XYZ to Lab
        lab = _xyz_to_lab(float(xyz[0]), float(xyz[1]), float(xyz[2]))
        return lab

    def cmyk_batch_to_lab(
        self, cmyk_list: list[tuple[float, float, float, float]]
    ) -> list[tuple[float, float, float]]:
        """Batch convert multiple CMYK values to Lab."""
        return [self.cmyk_to_lab(c, m, y, k) for c, m, y, k in cmyk_list]
