from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd


# -------------------------
# Config / Info
# -------------------------

@dataclass
class TiltAnalysisConfig:
    # MediaPipe Pose index
    LSHO: int = 11
    RSHO: int = 12
    LHIP: int = 23
    RHIP: int = 24

    # smoothing
    ma_window: int = 7

    # reference (pro runner)
    mu_ref: float = -82.5
    band_half: float = 4.5

    # thresholds
    hard_hi: float = -68.0
    hard_lo: float = -97.0
    k: float = 2.5
    max_abs_dtilt: float = 6.0
    consec_sec: float = 0.25


@dataclass
class TiltAnalysisInfo:
    sigma_robust: float
    delta_allow: float
    N_consec: int


# -------------------------
# Helpers
# -------------------------

def _robust_sigma_mad(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return float("nan")
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    return float(1.4826 * mad)


def _segments_from_bool(mask: np.ndarray, min_len: int) -> List[Tuple[int, int]]:
    segments = []
    start = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if i - start >= min_len:
                segments.append((start, i - 1))
            start = None
    if start is not None and len(mask) - start >= min_len:
        segments.append((start, len(mask) - 1))
    return segments


# -------------------------
# Core
# -------------------------

def compute_tilt_from_numpy(
    frames: np.ndarray,
    xyzv: np.ndarray,
    cfg: TiltAnalysisConfig,
) -> pd.DataFrame:
    """
    Args:
        frames: (T,)
        xyzv:   (T, 33, 4) [x, y, z, v]

    Returns:
        pandas DataFrame with tilt-related columns
    """
    LS, RS, LH, RH = cfg.LSHO, cfg.RSHO, cfg.LHIP, cfg.RHIP

    Sx = (xyzv[:, LS, 0] + xyzv[:, RS, 0]) / 2
    Sy = (xyzv[:, LS, 1] + xyzv[:, RS, 1]) / 2
    Hx = (xyzv[:, LH, 0] + xyzv[:, RH, 0]) / 2
    Hy = (xyzv[:, LH, 1] + xyzv[:, RH, 1]) / 2

    dx = Sx - Hx
    dy = Sy - Hy

    tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx)))

    tilt_smooth = (
        pd.Series(tilt_deg)
        .rolling(cfg.ma_window, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )

    dtilt = np.diff(tilt_deg, prepend=tilt_deg[0])
    abs_dtilt = np.abs(dtilt)

    return pd.DataFrame({
        "frame": frames,
        "tilt_deg": tilt_deg,
        "tilt_smooth": tilt_smooth,
        "abs_dtilt": abs_dtilt,
    })


def detect_tilt_error_segments(
    tilt_df: pd.DataFrame,
    fps: float,
    cfg: TiltAnalysisConfig,
) -> Tuple[np.ndarray, List[Tuple[int, int]], TiltAnalysisInfo]:

    tilt = tilt_df["tilt_smooth"].to_numpy()
    abs_dtilt = tilt_df["abs_dtilt"].to_numpy()

    ok = np.isfinite(tilt) & (abs_dtilt <= cfg.max_abs_dtilt)
    sigma = _robust_sigma_mad(tilt[ok])
    if not np.isfinite(sigma) or sigma < 1.0:
        sigma = 2.0

    delta_allow = cfg.band_half + cfg.k * sigma

    hard_err = (tilt >= cfg.hard_hi) | (tilt <= cfg.hard_lo)
    soft_err = np.abs(tilt - cfg.mu_ref) > delta_allow
    err_frame = (hard_err | soft_err) & np.isfinite(tilt)

    N_consec = max(1, int(round(cfg.consec_sec * fps)))
    segments = _segments_from_bool(err_frame, N_consec)

    info = TiltAnalysisInfo(
        sigma_robust=float(sigma),
        delta_allow=float(delta_allow),
        N_consec=int(N_consec),
    )

    return err_frame, segments, info
