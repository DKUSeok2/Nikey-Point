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

    # ✅ 잘 뛰는(프로) 기준: -78 ~ -87 (중심 -82.5, 반폭 4.5)
    mu_ref: float = -82.5
    band_half: float = 4.5  # => pro range = [mu_ref - band_half, mu_ref + band_half] = [-87, -78]

    # ✅ 하드 코딩 기준(절대 에러): -68 이상(너무 세움) or -97 이하(너무 숙임)
    hard_hi: float = -68.0
    hard_lo: float = -97.0

    # soft error band = band_half + k*sigma
    k: float = 2.5

    # reject noisy frames
    max_abs_dtilt: float = 6.0

    # consecutive error duration (sec)
    consec_sec: float = 0.25


@dataclass
class TiltAnalysisInfo:
    sigma_robust: float
    delta_allow: float
    N_consec: int
    pro_lo: float
    pro_hi: float
    hard_hi: float
    hard_lo: float


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
    segments: List[Tuple[int, int]] = []
    start = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif (not m) and (start is not None):
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
        xyzv:   (T, 33, 4) [x, y, z, v]  (x,y는 픽셀)

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

    # 좌/우 방향 무관하게 abs(dx)
    tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx)))

    tilt_smooth = (
        pd.Series(tilt_deg)
        .rolling(cfg.ma_window, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )

    dtilt = np.diff(tilt_deg, prepend=tilt_deg[0])
    abs_dtilt = np.abs(dtilt)

    return pd.DataFrame(
        {
            "frame": frames,
            "tilt_deg": tilt_deg,
            "tilt_smooth": tilt_smooth,
            "abs_dtilt": abs_dtilt,
        }
    )


def detect_tilt_error_segments(
    tilt_df: pd.DataFrame,
    fps: float,
    cfg: TiltAnalysisConfig,
) -> Tuple[np.ndarray, List[Tuple[int, int]], TiltAnalysisInfo]:
    """
    에러 프레임 정의:
      - hard_err: tilt >= hard_hi(-68)  OR  tilt <= hard_lo(-97)
      - soft_err: |tilt - mu_ref| > (band_half + k*sigma)

    "잘 뛰는 범위"는 cfg.mu_ref ± cfg.band_half = [-87, -78]
    """
    tilt = tilt_df["tilt_smooth"].to_numpy(dtype=float)
    abs_dtilt = tilt_df["abs_dtilt"].to_numpy(dtype=float)

    # 안정적인 구간만 sigma 계산에 사용
    ok = np.isfinite(tilt) & (abs_dtilt <= cfg.max_abs_dtilt)

    sigma = _robust_sigma_mad(tilt[ok])
    if (not np.isfinite(sigma)) or sigma < 1.0:
        sigma = 2.0

    # soft 허용폭: 프로 밴드 + 개인 변동(robust sigma)
    delta_allow = cfg.band_half + cfg.k * sigma

    hard_err = (tilt >= cfg.hard_hi) | (tilt <= cfg.hard_lo)
    soft_err = np.abs(tilt - cfg.mu_ref) > delta_allow

    err_frame = (hard_err | soft_err) & np.isfinite(tilt)

    N_consec = max(1, int(round(cfg.consec_sec * fps)))
    segments = _segments_from_bool(err_frame, min_len=N_consec)

    pro_lo = float(cfg.mu_ref - cfg.band_half)  # -87
    pro_hi = float(cfg.mu_ref + cfg.band_half)  # -78

    info = TiltAnalysisInfo(
        sigma_robust=float(sigma),
        delta_allow=float(delta_allow),
        N_consec=int(N_consec),
        pro_lo=pro_lo,
        pro_hi=pro_hi,
        hard_hi=float(cfg.hard_hi),
        hard_lo=float(cfg.hard_lo),
    )

    return err_frame, segments, info
