from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd


# MediaPipe Pose indices (fixed)
LH, RH = 23, 24
L_KNEE, R_KNEE = 25, 26
L_HEEL, R_HEEL = 29, 30
L_TOE, R_TOE = 31, 32


def expand_bool(x: np.ndarray, k: int = 1) -> np.ndarray:
    """Expand boolean array by +/-k frames (tolerance)."""
    x = np.asarray(x, bool)
    n = len(x)
    out = np.zeros(n, bool)
    for dt in range(-k, k + 1):
        if dt < 0:
            out[-dt:] |= x[: n + dt]
        elif dt > 0:
            out[: n - dt] |= x[dt:]
        else:
            out |= x
    return out


@dataclass(frozen=True)
class ABKDebug:
    gapL: np.ndarray
    gapR: np.ndarray
    knee_dx: np.ndarray
    condA_L: np.ndarray
    condB_L: np.ndarray
    condA_R: np.ndarray
    condB_R: np.ndarray
    condK: np.ndarray
    A_Lx: np.ndarray
    B_Lx: np.ndarray
    A_Rx: np.ndarray
    B_Rx: np.ndarray
    Kx: np.ndarray
    green_L: np.ndarray
    green_R: np.ndarray
    max_y_all: np.ndarray


def detect_contacts_abk(
    df: pd.DataFrame,
    *,
    eps: float = 0.003,
    k_tol: int = 1,
    cooldown: int = 8,
    return_debug: bool = True,
) -> Tuple[np.ndarray, np.ndarray, ABKDebug | None]:
    """
    ABK logic:
      A: gap local max (toe_y - opposite_heel_y)
      B: toe almost global lowest (y close to max_y_all)
      K: knee x-distance local min
      green = expand(A) & expand(B) & expand(K)
      contact = first frame in green region with cooldown
    """
    n = len(df)

    toeL_y = df[f"y_{L_TOE}"].to_numpy(float)
    toeR_y = df[f"y_{R_TOE}"].to_numpy(float)
    heelL_y = df[f"y_{L_HEEL}"].to_numpy(float)
    heelR_y = df[f"y_{R_HEEL}"].to_numpy(float)

    kneeL_x = df[f"x_{L_KNEE}"].to_numpy(float)
    kneeR_x = df[f"x_{R_KNEE}"].to_numpy(float)

    # A: gap local max
    gapL = toeL_y - heelR_y
    gapR = toeR_y - heelL_y

    condA_L = np.zeros(n, bool)
    condA_R = np.zeros(n, bool)
    for t in range(1, n - 1):
        if not np.isnan(gapL[t - 1 : t + 2]).any():
            condA_L[t] = gapL[t - 1] < gapL[t] > gapL[t + 1]
        if not np.isnan(gapR[t - 1 : t + 2]).any():
            condA_R[t] = gapR[t - 1] < gapR[t] > gapR[t + 1]

    # B: toe almost lowest (y max)
    all_y = df[[f"y_{i}" for i in range(33)]].to_numpy(float)
    max_y_all = np.nanmax(all_y, axis=1)
    condB_L = toeL_y >= (max_y_all - eps)
    condB_R = toeR_y >= (max_y_all - eps)

    # K: knee dx local min
    knee_dx = np.abs(kneeL_x - kneeR_x)
    condK = np.zeros(n, bool)
    for t in range(1, n - 1):
        if not np.isnan(knee_dx[t - 1 : t + 2]).any():
            condK[t] = knee_dx[t - 1] > knee_dx[t] < knee_dx[t + 1]

    # expand tolerance
    A_Lx = expand_bool(condA_L, k_tol)
    B_Lx = expand_bool(condB_L, k_tol)
    A_Rx = expand_bool(condA_R, k_tol)
    B_Rx = expand_bool(condB_R, k_tol)
    Kx = expand_bool(condK, k_tol)

    green_L = A_Lx & B_Lx & Kx
    green_R = A_Rx & B_Rx & Kx

    # cooldown pick (L first else R), exactly like your code
    contact_L = np.zeros(n, bool)
    contact_R = np.zeros(n, bool)
    last = -10**9
    for t in range(n):
        if (t - last) < cooldown:
            continue
        if green_L[t]:
            contact_L[t] = True
            last = t
        elif green_R[t]:
            contact_R[t] = True
            last = t

    dbg = None
    if return_debug:
        dbg = ABKDebug(
            gapL=gapL,
            gapR=gapR,
            knee_dx=knee_dx,
            condA_L=condA_L,
            condB_L=condB_L,
            condA_R=condA_R,
            condB_R=condB_R,
            condK=condK,
            A_Lx=A_Lx,
            B_Lx=B_Lx,
            A_Rx=A_Rx,
            B_Rx=B_Rx,
            Kx=Kx,
            green_L=green_L,
            green_R=green_R,
            max_y_all=max_y_all,
        )

    return contact_L, contact_R, dbg
