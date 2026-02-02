from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# -------------------------
# Config / Info
# -------------------------

@dataclass
class TiltAnalysisConfig:
    # column preference
    frame_col_candidates: Tuple[str, ...] = ("Frame", "frame")

    # landmarks (MediaPipe Pose)
    LSHO: int = 11
    RSHO: int = 12
    LHIP: int = 23
    RHIP: int = 24

    # tilt smoothing
    ma_window: int = 7

    # error detection params
    use_col: str = "tilt_smooth_MA7"
    mu_ref: float = -82.5
    band_half: float = 4.5
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
    mu_ref: float
    band_half: float
    k: float
    hard_hi: float
    hard_lo: float
    max_abs_dtilt: float
    use_col: str


# -------------------------
# Helpers
# -------------------------

def _col_xy(df: pd.DataFrame, i: int) -> Tuple[str, str]:
    candidates = [
        (f"x_{i}", f"y_{i}"),
        (f"{i}_x", f"{i}_y"),
        (f"landmark_{i}_x", f"landmark_{i}_y"),
        (f"X_{i}", f"Y_{i}"),
    ]
    for cx, cy in candidates:
        if cx in df.columns and cy in df.columns:
            return cx, cy
    raise KeyError(f"landmark {i}의 x/y 컬럼을 못 찾았어. columns={list(df.columns)[:30]}...")


def _get_frame_col(df: pd.DataFrame, candidates: Sequence[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    df["Frame"] = np.arange(len(df))
    return "Frame"


def _robust_sigma_mad(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return float("nan")
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    return float(1.4826 * mad)


def _segments_from_bool(mask: np.ndarray, min_len: int) -> List[Tuple[int, int]]:
    segments: List[Tuple[int, int]] = []
    in_seg = False
    start = 0
    count = 0

    for i, m in enumerate(mask):
        if m:
            if not in_seg:
                in_seg = True
                start = i
                count = 1
            else:
                count += 1
        else:
            if in_seg:
                if count >= min_len:
                    segments.append((start, i - 1))
                in_seg = False
                count = 0

    if in_seg and count >= min_len:
        segments.append((start, len(mask) - 1))

    return segments


def resolve_use_col(cfg: TiltAnalysisConfig) -> str:
    """window가 바뀌면 use_col을 자동으로 맞춘다(하지만 cfg 자체는 안 바꿈)."""
    if cfg.use_col == "tilt_smooth_MA7" and cfg.ma_window != 7:
        return f"tilt_smooth_MA{cfg.ma_window}"
    return cfg.use_col


# -------------------------
# Core: compute tilt table
# -------------------------

def compute_tilt_table(df_keypoints: pd.DataFrame, cfg: TiltAnalysisConfig) -> pd.DataFrame:
    df = df_keypoints.copy()
    frame_col = _get_frame_col(df, cfg.frame_col_candidates)

    x11, y11 = df[_col_xy(df, cfg.LSHO)[0]], df[_col_xy(df, cfg.LSHO)[1]]
    x12, y12 = df[_col_xy(df, cfg.RSHO)[0]], df[_col_xy(df, cfg.RSHO)[1]]
    x23, y23 = df[_col_xy(df, cfg.LHIP)[0]], df[_col_xy(df, cfg.LHIP)[1]]
    x24, y24 = df[_col_xy(df, cfg.RHIP)[0]], df[_col_xy(df, cfg.RHIP)[1]]

    Sx = (x11 + x12) / 2
    Sy = (y11 + y12) / 2
    Hx = (x23 + x24) / 2
    Hy = (y23 + y24) / 2

    dx = (Sx - Hx).to_numpy(dtype=float)
    dy = (Sy - Hy).to_numpy(dtype=float)

    # 좌/우 무관: abs(dx)
    tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx)))

    tilt_smooth = (
        pd.Series(tilt_deg)
        .rolling(cfg.ma_window, center=True, min_periods=1)
        .mean()
        .to_numpy(dtype=float)
    )

    dtilt = np.diff(tilt_deg, prepend=tilt_deg[0])
    abs_dtilt = np.abs(dtilt)

    out = pd.DataFrame({
        "frame": df[frame_col].to_numpy(),
        "tilt_deg": tilt_deg,
        f"tilt_smooth_MA{cfg.ma_window}": tilt_smooth,
        "dtilt_deg_per_frame": dtilt,
        "abs_dtilt": abs_dtilt,
        "mid_shoulder_x": np.asarray(Sx),
        "mid_shoulder_y": np.asarray(Sy),
        "mid_hip_x": np.asarray(Hx),
        "mid_hip_y": np.asarray(Hy),
    })
    return out


# -------------------------
# Core: detect error segments
# -------------------------

def detect_tilt_error_segments(
    tilt_table: pd.DataFrame,
    fps: float,
    cfg: TiltAnalysisConfig
) -> Tuple[np.ndarray, List[Tuple[int, int]], TiltAnalysisInfo]:
    use_col = resolve_use_col(cfg)

    if use_col not in tilt_table.columns:
        raise ValueError(f"{use_col} 컬럼이 없어. columns={list(tilt_table.columns)}")

    tilt = tilt_table[use_col].to_numpy(dtype=float)

    abs_dtilt = (
        tilt_table["abs_dtilt"].to_numpy(dtype=float)
        if "abs_dtilt" in tilt_table.columns
        else np.abs(np.diff(tilt, prepend=tilt[0]))
    )

    ok = np.isfinite(tilt) & (abs_dtilt <= cfg.max_abs_dtilt)

    sigma = _robust_sigma_mad(tilt[ok])
    if not np.isfinite(sigma) or sigma < 1.0:
        sigma = 2.0

    delta_allow = cfg.band_half + cfg.k * sigma

    hard_err = (tilt >= cfg.hard_hi) | (tilt <= cfg.hard_lo)
    soft_err = np.abs(tilt - cfg.mu_ref) > delta_allow

    err_frame = (hard_err | soft_err) & np.isfinite(tilt)

    N_consec = max(1, int(round(cfg.consec_sec * fps)))
    segments = _segments_from_bool(err_frame, min_len=N_consec)

    info = TiltAnalysisInfo(
        sigma_robust=float(sigma),
        delta_allow=float(delta_allow),
        N_consec=int(N_consec),
        mu_ref=float(cfg.mu_ref),
        band_half=float(cfg.band_half),
        k=float(cfg.k),
        hard_hi=float(cfg.hard_hi),
        hard_lo=float(cfg.hard_lo),
        max_abs_dtilt=float(cfg.max_abs_dtilt),
        use_col=str(use_col),
    )
    return err_frame, segments, info


from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# -------------------------
# Config / Info
# -------------------------

@dataclass
class TiltAnalysisConfig:
    # column preference
    frame_col_candidates: Tuple[str, ...] = ("Frame", "frame")

    # landmarks (MediaPipe Pose)
    LSHO: int = 11
    RSHO: int = 12
    LHIP: int = 23
    RHIP: int = 24

    # tilt smoothing
    ma_window: int = 7

    # error detection params
    use_col: str = "tilt_smooth_MA7"
    mu_ref: float = -82.5
    band_half: float = 4.5
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
    mu_ref: float
    band_half: float
    k: float
    hard_hi: float
    hard_lo: float
    max_abs_dtilt: float
    use_col: str


# -------------------------
# Helpers
# -------------------------

def _col_xy(df: pd.DataFrame, i: int) -> Tuple[str, str]:
    candidates = [
        (f"x_{i}", f"y_{i}"),
        (f"{i}_x", f"{i}_y"),
        (f"landmark_{i}_x", f"landmark_{i}_y"),
        (f"X_{i}", f"Y_{i}"),
    ]
    for cx, cy in candidates:
        if cx in df.columns and cy in df.columns:
            return cx, cy
    raise KeyError(f"landmark {i}의 x/y 컬럼을 못 찾았어. columns={list(df.columns)[:30]}...")


def _get_frame_col(df: pd.DataFrame, candidates: Sequence[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    df["Frame"] = np.arange(len(df))
    return "Frame"


def _robust_sigma_mad(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return float("nan")
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    return float(1.4826 * mad)


def _segments_from_bool(mask: np.ndarray, min_len: int) -> List[Tuple[int, int]]:
    segments: List[Tuple[int, int]] = []
    in_seg = False
    start = 0
    count = 0

    for i, m in enumerate(mask):
        if m:
            if not in_seg:
                in_seg = True
                start = i
                count = 1
            else:
                count += 1
        else:
            if in_seg:
                if count >= min_len:
                    segments.append((start, i - 1))
                in_seg = False
                count = 0

    if in_seg and count >= min_len:
        segments.append((start, len(mask) - 1))

    return segments


def resolve_use_col(cfg: TiltAnalysisConfig) -> str:
    """window가 바뀌면 use_col을 자동으로 맞춘다(하지만 cfg 자체는 안 바꿈)."""
    if cfg.use_col == "tilt_smooth_MA7" and cfg.ma_window != 7:
        return f"tilt_smooth_MA{cfg.ma_window}"
    return cfg.use_col


# -------------------------
# Core: compute tilt table
# -------------------------

def compute_tilt_table(df_keypoints: pd.DataFrame, cfg: TiltAnalysisConfig) -> pd.DataFrame:
    df = df_keypoints.copy()
    frame_col = _get_frame_col(df, cfg.frame_col_candidates)

    x11, y11 = df[_col_xy(df, cfg.LSHO)[0]], df[_col_xy(df, cfg.LSHO)[1]]
    x12, y12 = df[_col_xy(df, cfg.RSHO)[0]], df[_col_xy(df, cfg.RSHO)[1]]
    x23, y23 = df[_col_xy(df, cfg.LHIP)[0]], df[_col_xy(df, cfg.LHIP)[1]]
    x24, y24 = df[_col_xy(df, cfg.RHIP)[0]], df[_col_xy(df, cfg.RHIP)[1]]

    Sx = (x11 + x12) / 2
    Sy = (y11 + y12) / 2
    Hx = (x23 + x24) / 2
    Hy = (y23 + y24) / 2

    dx = (Sx - Hx).to_numpy(dtype=float)
    dy = (Sy - Hy).to_numpy(dtype=float)

    # 좌/우 무관: abs(dx)
    tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx)))

    tilt_smooth = (
        pd.Series(tilt_deg)
        .rolling(cfg.ma_window, center=True, min_periods=1)
        .mean()
        .to_numpy(dtype=float)
    )

    dtilt = np.diff(tilt_deg, prepend=tilt_deg[0])
    abs_dtilt = np.abs(dtilt)

    out = pd.DataFrame({
        "frame": df[frame_col].to_numpy(),
        "tilt_deg": tilt_deg,
        f"tilt_smooth_MA{cfg.ma_window}": tilt_smooth,
        "dtilt_deg_per_frame": dtilt,
        "abs_dtilt": abs_dtilt,
        "mid_shoulder_x": np.asarray(Sx),
        "mid_shoulder_y": np.asarray(Sy),
        "mid_hip_x": np.asarray(Hx),
        "mid_hip_y": np.asarray(Hy),
    })
    return out


# -------------------------
# Core: detect error segments
# -------------------------

def detect_tilt_error_segments(
    tilt_table: pd.DataFrame,
    fps: float,
    cfg: TiltAnalysisConfig
) -> Tuple[np.ndarray, List[Tuple[int, int]], TiltAnalysisInfo]:
    use_col = resolve_use_col(cfg)

    if use_col not in tilt_table.columns:
        raise ValueError(f"{use_col} 컬럼이 없어. columns={list(tilt_table.columns)}")

    tilt = tilt_table[use_col].to_numpy(dtype=float)

    abs_dtilt = (
        tilt_table["abs_dtilt"].to_numpy(dtype=float)
        if "abs_dtilt" in tilt_table.columns
        else np.abs(np.diff(tilt, prepend=tilt[0]))
    )

    ok = np.isfinite(tilt) & (abs_dtilt <= cfg.max_abs_dtilt)

    sigma = _robust_sigma_mad(tilt[ok])
    if not np.isfinite(sigma) or sigma < 1.0:
        sigma = 2.0

    delta_allow = cfg.band_half + cfg.k * sigma

    hard_err = (tilt >= cfg.hard_hi) | (tilt <= cfg.hard_lo)
    soft_err = np.abs(tilt - cfg.mu_ref) > delta_allow

    err_frame = (hard_err | soft_err) & np.isfinite(tilt)

    N_consec = max(1, int(round(cfg.consec_sec * fps)))
    segments = _segments_from_bool(err_frame, min_len=N_consec)

    info = TiltAnalysisInfo(
        sigma_robust=float(sigma),
        delta_allow=float(delta_allow),
        N_consec=int(N_consec),
        mu_ref=float(cfg.mu_ref),
        band_half=float(cfg.band_half),
        k=float(cfg.k),
        hard_hi=float(cfg.hard_hi),
        hard_lo=float(cfg.hard_lo),
        max_abs_dtilt=float(cfg.max_abs_dtilt),
        use_col=str(use_col),
    )
    return err_frame, segments, info
