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

    # ✅ 하드 코딩 기준(절대 에러): -68 이상(너무 세움) or -97 이하(뒤로 젖힘/과도한 각)
    # (이번 수정으로 -90 이하가 실제로 나오므로 hard_lo가 의미를 갖게 됨)
    hard_hi: float = -68.0
    hard_lo: float = -97.0

    # soft error band = band_half + k*sigma
    k: float = 2.5

    # reject noisy frames
    max_abs_dtilt: float = 6.0

    # consecutive error duration (sec)
    consec_sec: float = 0.25

    # direction estimation
    dir_smooth_window: int = 15   # Hx 변화의 중앙값을 낼 때 참조 구간(프레임)
    dir_min_median_dx: float = 0.05  # 너무 미세하면 방향을 확정하지 않음(픽셀 단위, 상황에 맞게 조절)


@dataclass
class TiltAnalysisInfo:
    sigma_robust: float
    delta_allow: float
    N_consec: int
    pro_lo: float
    pro_hi: float
    hard_hi: float
    hard_lo: float
    dir_sign: int  # +1: 오른쪽으로 달림, -1: 왼쪽으로 달림


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


def _estimate_dir_sign_from_Hx(Hx: np.ndarray, cfg: TiltAnalysisConfig) -> int:
    """
    +1: 전반적으로 x가 증가(오른쪽 진행)
    -1: 전반적으로 x가 감소(왼쪽 진행)

    Hx(hip center x)의 diff 중앙값을 써서 방향을 안정적으로 추정.
    """
    hx = np.asarray(Hx, dtype=float)
    hx = hx[np.isfinite(hx)]
    if len(hx) < 5:
        return +1

    # 원래 길이에 맞춰 diff 계산하고, 너무 짧지 않게
    # (Hx가 NaN 많으면 위에서 줄어들 수 있음)
    dh = np.diff(hx)
    if len(dh) < 3:
        return +1

    # 중앙값(robust)
    med = float(np.median(dh))

    if abs(med) < cfg.dir_min_median_dx:
        # 거의 정지/카메라 흔들림/방향 불명 -> 기본값 +1
        return +1

    return +1 if med > 0 else -1


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

    핵심 변경점:
      - abs(dx) 제거
      - 달리는 방향(dir_sign)을 추정해서 dx에 반영 -> 뒤로 젖힘(>90°)이 실제로 계산됨
      - right_angle(0~180), left_angle(0~180)도 함께 제공
    """
    LS, RS, LH, RH = cfg.LSHO, cfg.RSHO, cfg.LHIP, cfg.RHIP

    Sx = (xyzv[:, LS, 0] + xyzv[:, RS, 0]) / 2.0
    Sy = (xyzv[:, LS, 1] + xyzv[:, RS, 1]) / 2.0
    Hx = (xyzv[:, LH, 0] + xyzv[:, RH, 0]) / 2.0
    Hy = (xyzv[:, LH, 1] + xyzv[:, RH, 1]) / 2.0

    # 어깨-골반 벡터
    dx = Sx - Hx
    dy = Sy - Hy  # 이미지 좌표계: y 아래로 증가 → 정상 달리면 dy 보통 음수(어깨가 위)

    # 달리는 방향 추정(+1: 오른쪽, -1: 왼쪽)
    dir_sign = _estimate_dir_sign_from_Hx(Hx, cfg)

    # 진행 방향 기준으로 정규화한 dx (앞으로 숙이면 dx_dir > 0, 뒤로 젖히면 dx_dir < 0)
    dx_dir = dx * float(dir_sign)

    # ✅ 부호 있는 arctan2로 "90° 초과"가 나오게 됨
    # range: (-180, 180]
    tilt_deg = np.degrees(np.arctan2(dy, dx_dir))

    # 사람 해석용: "오른쪽(진행방향) 기준 각도" / "왼쪽 기준 각도"
    # dy는 절대값을 써서 0~180로 만들고, dx_dir의 부호로 예각/둔각이 갈림
    right_angle = np.degrees(np.arctan2(np.abs(dy), dx_dir))  # 0~180
    left_angle = 180.0 - right_angle

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
            "dir_sign": np.full_like(frames, dir_sign, dtype=int),

            # 원본/스무딩 (이 값으로 에러 판단)
            "tilt_deg": tilt_deg,
            "tilt_smooth": tilt_smooth,

            # 사람이 보기 쉬운 양쪽 각도
            "right_angle": right_angle,
            "left_angle": left_angle,

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

    이번 수정으로:
      - 뒤로 젖힘(>90°)이 tilt_smooth에서 -90 이하(예: -100)로 잡히므로
        hard_lo(-97) 같은 기준이 실제로 동작함.
    """
    tilt = tilt_df["tilt_smooth"].to_numpy(dtype=float)
    abs_dtilt = tilt_df["abs_dtilt"].to_numpy(dtype=float)

    # 방향 정보(전 프레임 동일)
    if "dir_sign" in tilt_df.columns:
        dir_sign = int(pd.Series(tilt_df["dir_sign"]).mode().iloc[0])
        if dir_sign not in (+1, -1):
            dir_sign = +1
    else:
        dir_sign = +1

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
        dir_sign=int(dir_sign),
    )

    return err_frame, segments, info
