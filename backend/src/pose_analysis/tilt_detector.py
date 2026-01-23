from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# -------------------------
# Config / Result types
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
    mu_ref: float = -82.5       # “정답 중심”
    band_half: float = 4.5      # 정답밴드 반폭 ([-87, -78])
    hard_hi: float = -68.0      # 너무 덜 숙임 -> 즉시 에러
    hard_lo: float = -97.0      # 너무 과숙임 -> 즉시 에러
    k: float = 2.5              # 적응형 허용폭 계수
    max_abs_dtilt: float = 6.0  # 프레임당 변화량 너무 크면 포즈 깨짐으로 제외
    consec_sec: float = 0.25    # 연속 판정 시간(초)


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
    # 없으면 생성
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


# -------------------------
# Core: compute tilt table
# -------------------------

def compute_tilt_table(df_keypoints: pd.DataFrame, cfg: TiltAnalysisConfig) -> pd.DataFrame:
    """
    입력: 키포인트 CSV를 읽은 DataFrame
    출력: frame/tilt/tilt_smooth/abs_dtilt + midpoints 포함한 DataFrame
    """
    df = df_keypoints.copy()

    frame_col = _get_frame_col(df, cfg.frame_col_candidates)

    # landmarks
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

    # ✅ 좌/우 무관하게 (abs(dx))
    tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx)))

    # smoothing + delta
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

    # config use_col 기본값은 tilt_smooth_MA7인데, window 바뀌면 맞춰주기
    if cfg.use_col == "tilt_smooth_MA7" and cfg.ma_window != 7:
        cfg.use_col = f"tilt_smooth_MA{cfg.ma_window}"

    return out


# -------------------------
# Core: detect error segments
# -------------------------

def detect_tilt_error_segments(
    tilt_table: pd.DataFrame,
    fps: float,
    cfg: TiltAnalysisConfig
) -> Tuple[np.ndarray, List[Tuple[int, int]], TiltAnalysisInfo]:
    """
    입력: compute_tilt_table 결과, fps
    출력: err_frame(bool array), segments(list), info(dataclass)
    """
    if cfg.use_col not in tilt_table.columns:
        raise ValueError(f"{cfg.use_col} 컬럼이 없어. columns={list(tilt_table.columns)}")

    tilt = tilt_table[cfg.use_col].to_numpy(dtype=float)

    if "abs_dtilt" in tilt_table.columns:
        abs_dtilt = tilt_table["abs_dtilt"].to_numpy(dtype=float)
    else:
        abs_dtilt = np.abs(np.diff(tilt, prepend=tilt[0]))

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
    )
    return err_frame, segments, info


# -------------------------
# One-shot API: path -> outputs
# -------------------------

def run_tilt_analysis_from_keypoints_csv(
    keypoints_csv_path: str,
    fps: float,
    cfg: Optional[TiltAnalysisConfig] = None,
    save_tilt_csv_path: Optional[str] = None,
) -> Dict:
    """
    다른 어떤 파일(Workers/Video 파이프라인)에서 이 함수만 호출하면 됨.

    반환값은 '생성형 AI 입력으로 쓰기 좋은 dict' 형태.
    """
    cfg = cfg or TiltAnalysisConfig()

    df_keypoints = pd.read_csv(keypoints_csv_path)
    tilt_table = compute_tilt_table(df_keypoints, cfg)

    err_frame, segments, info = detect_tilt_error_segments(tilt_table, fps, cfg)

    if save_tilt_csv_path:
        tilt_table.to_csv(save_tilt_csv_path, index=False, encoding="utf-8-sig")

    # AI/피드백 생성 입력용 요약 만들기
    segments_sec = [(s / fps, e / fps) for (s, e) in segments]
    result = {
        "input": {
            "keypoints_csv_path": keypoints_csv_path,
            "fps": float(fps),
        },
        "tilt_stats": {
            "tilt_mean": float(np.nanmean(tilt_table["tilt_deg"].to_numpy(dtype=float))),
            "tilt_std": float(np.nanstd(tilt_table["tilt_deg"].to_numpy(dtype=float))),
            "tilt_min": float(np.nanmin(tilt_table["tilt_deg"].to_numpy(dtype=float))),
            "tilt_max": float(np.nanmax(tilt_table["tilt_deg"].to_numpy(dtype=float))),
        },
        "error": {
            "segments_frame": segments,          # [(start_frame, end_frame), ...]
            "segments_sec": [(round(s, 2), round(e, 2)) for (s, e) in segments_sec],
            "n_segments": int(len(segments)),
            "err_ratio": float(np.mean(err_frame)) if len(err_frame) else 0.0,
            "info": asdict(info),                # sigma, delta_allow 등
        },
        # 필요하면 생성형 AI에 “상세 타임라인”도 줄 수 있음(무거우면 끄면 됨)
        "timeline": {
            "frame": tilt_table["frame"].to_list(),
            "tilt_deg": tilt_table["tilt_deg"].to_list(),
            cfg.use_col: tilt_table[cfg.use_col].to_list(),
        },
        # 저장했으면 경로도 같이
        "artifacts": {
            "tilt_csv_path": save_tilt_csv_path,
        }
    }
    return result
