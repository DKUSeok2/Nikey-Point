from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import os
import numpy as np
import pandas as pd


LH, RH = 23, 24
L_ANKLE, R_ANKLE = 27, 28
L_HEEL, R_HEEL = 29, 30
L_TOE, R_TOE = 31, 32


FootPoint = Literal["toe", "heel", "ankle"]
Side = Literal["L", "R"]


def midhip_xy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    hx = (df[f"x_{LH}"].to_numpy(float) + df[f"x_{RH}"].to_numpy(float)) / 2.0
    hy = (df[f"y_{LH}"].to_numpy(float) + df[f"y_{RH}"].to_numpy(float)) / 2.0
    return hx, hy


def foot_xy(df: pd.DataFrame, side: Side, point: FootPoint) -> Tuple[np.ndarray, np.ndarray]:
    if side == "L":
        idx = {"toe": L_TOE, "heel": L_HEEL, "ankle": L_ANKLE}[point]
    else:
        idx = {"toe": R_TOE, "heel": R_HEEL, "ankle": R_ANKLE}[point]
    return df[f"x_{idx}"].to_numpy(float), df[f"y_{idx}"].to_numpy(float)


def compute_overstride_dx(
    df: pd.DataFrame,
    *,
    side: Side,
    point: FootPoint = "toe",
) -> np.ndarray:
    """
    Raw overstride proxy per frame:
      dx = foot_x - midhip_x
    (positive means foot in front if running left->right in camera coordinates)
    """
    hx, _ = midhip_xy(df)
    fx, _ = foot_xy(df, side=side, point=point)
    return fx - hx


def compute_overstride_ratio(
    overstride_dx: np.ndarray,
    *,
    norm: np.ndarray | float,
    direction: Literal["right", "left"] = "right",
    eps: float = 1e-9,
) -> np.ndarray:
    """
    Normalize dx by norm:
      ratio = dx / norm
    If direction == "left", invert sign so "positive always means ahead of hip".
    """
    dx = np.asarray(overstride_dx, float)
    if direction == "left":
        dx = -dx

    if np.isscalar(norm):
        denom = float(norm)
        denom = denom if abs(denom) > eps else eps
        return dx / denom

    denom = np.asarray(norm, float)
    denom = np.where(np.abs(denom) > eps, denom, eps)
    return dx / denom


@dataclass(frozen=True)
class ContactOverstrideRow:
    video: str
    frame: int
    time_s: float
    side: Side
    overstride_dx: float
    overstride_ratio: Optional[float]  # None if norm not provided


def build_contact_overstride_table(
    df: pd.DataFrame,
    *,
    video_name: str,
    fps: float,
    contact_L: np.ndarray,
    contact_R: np.ndarray,
    point: FootPoint = "toe",
    norm: np.ndarray | float | None = None,
    direction: Literal["right", "left"] = "right",
    csv_out_path: str | None = None, 
    overwrite: bool = False, 
) -> pd.DataFrame:
    """
    Create a tidy table only at contact frames (like your code).
    If csv_out_path is provided, also save the table to CSV.
    """
    dxL = compute_overstride_dx(df, side="L", point=point)
    dxR = compute_overstride_dx(df, side="R", point=point)

    rows: list[dict] = []

    if norm is not None:
        ratioL = compute_overstride_ratio(dxL, norm=norm, direction=direction)
        ratioR = compute_overstride_ratio(dxR, norm=norm, direction=direction)
    else:
        ratioL = None
        ratioR = None

    for t in np.where(contact_L)[0]:
        if np.isnan(dxL[t]):
            continue
        rows.append(
            {
                "video": video_name,
                "frame": int(t),
                "time_s": float(t / fps),
                "side": "L",
                "overstride_dx": float(dxL[t]),
                "overstride_ratio": (float(ratioL[t]) if ratioL is not None else np.nan),
            }
        )

    for t in np.where(contact_R)[0]:
        if np.isnan(dxR[t]):
            continue
        rows.append(
            {
                "video": video_name,
                "frame": int(t),
                "time_s": float(t / fps),
                "side": "R",
                "overstride_dx": float(dxR[t]),
                "overstride_ratio": (float(ratioR[t]) if ratioR is not None else np.nan),
            }
        )

    out = pd.DataFrame(rows)
    '''
    1) 이상치 처리: 음수 제거 (원하면 옵션으로 끌 수 있게)
       방향(direction)을 고려해 "앞"이 +가 되게 만들려면 ratio/dx 계산 정책도 같이 봐야 하지만,
       지금은 네 요구대로 dx<0 제거를 기본으로 둠.
    '''
    drop_negative = True  # <- 기본 정책 (원하면 함수 인자로 빼자)
    if drop_negative and ("overstride_dx" in out.columns):
        out = out[out["overstride_dx"] >= 0].reset_index(drop=True)

    #2) 정렬
    if len(out) > 0:
        out = out.sort_values(["frame", "side"]).reset_index(drop=True)
    
    #3) CSV저장 (필터/정렬 적용된 결과를 저장)
    if csv_out_path is not None:
        os.makedirs(os.path.dirname(csv_out_path) or ".", exist_ok=True)
        out.to_csv(csv_out_path, index=False)
    
    return out

