from __future__ import annotations

from typing import Literal, Tuple
import numpy as np
import pandas as pd


# =========================
# Landmark indices
# =========================
LH, RH = 23, 24
L_ANKLE, R_ANKLE = 27, 28
L_HEEL, R_HEEL = 29, 30
L_TOE, R_TOE = 31, 32

FootPoint = Literal["toe", "heel", "ankle"]
Side = Literal["L", "R"]


# =========================
# Adapter 1
# NumPy keypoints → DataFrame
# =========================
def xyzv_to_keypoints_df(frames: np.ndarray, xyzv: np.ndarray) -> pd.DataFrame:
    """
    frames: (T,)
    xyzv:   (T, 33, 4)
    return:
      DataFrame with columns x_i, y_i
      index == frame number
    """
    rows = {}
    for t, frame in enumerate(frames):
        row = {}
        for i in range(xyzv.shape[1]):
            row[f"x_{i}"] = xyzv[t, i, 0]
            row[f"y_{i}"] = xyzv[t, i, 1]
        rows[int(frame)] = row

    df = pd.DataFrame.from_dict(rows, orient="index")
    df.index.name = "frame"
    return df.sort_index()


# =========================
# Adapter 2
# height dict → DataFrame
# =========================
def height_dict_to_df(height_results: dict[int, float | None]) -> pd.DataFrame:
    """
    {frame: pixel_height | None}
      → DataFrame(frame, pixel_height, detected)
    """
    rows = []
    for frame, h in height_results.items():
        rows.append({
            "frame": int(frame),
            "pixel_height": float(h) if h is not None else np.nan,
            "detected": "Yes" if h is not None else "No",
        })
    return pd.DataFrame(rows)


# =========================
# Geometry helpers
# =========================
def midhip_xy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    hx = (df[f"x_{LH}"].to_numpy(float) + df[f"x_{RH}"].to_numpy(float)) / 2.0
    hy = (df[f"y_{LH}"].to_numpy(float) + df[f"y_{RH}"].to_numpy(float)) / 2.0
    return hx, hy


def foot_xy(
    df: pd.DataFrame,
    *,
    side: Side,
    point: FootPoint = "toe",
) -> Tuple[np.ndarray, np.ndarray]:
    if side == "L":
        idx = {"toe": L_TOE, "heel": L_HEEL, "ankle": L_ANKLE}[point]
    else:
        idx = {"toe": R_TOE, "heel": R_HEEL, "ankle": R_ANKLE}[point]

    return df[f"x_{idx}"].to_numpy(float), df[f"y_{idx}"].to_numpy(float)


# =========================
# Overstride core
# =========================
def compute_overstride_dx(
    df: pd.DataFrame,
    *,
    side: Side,
    point: FootPoint = "toe",
) -> np.ndarray:
    """
    dx = foot_x - midhip_x
    """
    hx, _ = midhip_xy(df)
    fx, _ = foot_xy(df, side=side, point=point)
    return fx - hx


# =========================
# Final fast pipeline
# =========================
def compute_overstride_numpy(
    *,
    keypoints_df: pd.DataFrame,
    contact_L: np.ndarray,
    contact_R: np.ndarray,
    height_df: pd.DataFrame,
    point: FootPoint = "toe",
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Returns:
      frames : np.ndarray (N,)
      values : np.ndarray (N,)   # normalized overstride
      mean   : float
    """

    # ---------- 1. raw dx ----------
    dxL = compute_overstride_dx(keypoints_df, side="L", point=point)
    dxR = compute_overstride_dx(keypoints_df, side="R", point=point)

    # ---------- 2. height preprocessing ----------
    height_map = (
        height_df[height_df["detected"] == "Yes"]
        .loc[:, ["frame", "pixel_height"]]
        .astype({"frame": int, "pixel_height": float})
        .set_index("frame")
    )

    frames: list[int] = []
    values: list[float] = []

    # ---------- 3. collect normalized values ----------
    for t in np.where(contact_L)[0]:
        if t in height_map.index and dxL[t] >= 0:
            frames.append(t)
            values.append(dxL[t] / height_map.loc[t, "pixel_height"])

    for t in np.where(contact_R)[0]:
        if t in height_map.index and dxR[t] >= 0:
            frames.append(t)
            values.append(dxR[t] / height_map.loc[t, "pixel_height"])

    # ---------- 4. finalize ----------
    if len(values) == 0:
        return (
            np.array([], dtype=np.int32),
            np.array([], dtype=np.float32),
            np.nan,
        )

    frames_np = np.asarray(frames, dtype=np.int32)
    values_np = np.asarray(values, dtype=np.float32)

    return frames_np, values_np, float(values_np.mean())
