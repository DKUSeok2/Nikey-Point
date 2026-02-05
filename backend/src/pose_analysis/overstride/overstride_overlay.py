from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import mediapipe as mp


# =========================================================
# Config
# =========================================================
@dataclass
class OverstrideOverlayConfig:
    ratio_hi: float = 0.18     # 키 대비 18% 이상 → ERR
    ratio_lo: float = 0.00     # 0 이하는 이미 필터링 -> ERR
    foot_point: str = "toe"    # "toe" | "heel" | "ankle" 발 기준점 선택 가능

    # draw options
    min_vis: float = 0.5
    show_text: bool = True

    color_ok: Tuple[int, int, int] = (0, 255, 0)    # green
    color_err: Tuple[int, int, int] = (0, 0, 255)   # red
    color_midhip: Tuple[int, int, int] = (255, 255, 255)  # white
    color_foot: Tuple[int, int, int] = (0, 255, 255)      # yellow


# =========================================================
# Helpers
# =========================================================
LH, RH = 23, 24
L_ANKLE, R_ANKLE = 27, 28
L_HEEL, R_HEEL = 29, 30
L_TOE, R_TOE = 31, 32


def _midhip_xy(pts: np.ndarray) -> Tuple[float, float]:
    x = (pts[LH, 0] + pts[RH, 0]) / 2.0
    y = (pts[LH, 1] + pts[RH, 1]) / 2.0
    return float(x), float(y)


def _foot_xy(pts: np.ndarray, side: str, point: str) -> Tuple[float, float]:
    if side == "L":
        idx = {"toe": L_TOE, "heel": L_HEEL, "ankle": L_ANKLE}[point]
    else:
        idx = {"toe": R_TOE, "heel": R_HEEL, "ankle": R_ANKLE}[point]
    return float(pts[idx, 0]), float(pts[idx, 1])


# =========================================================
# Main API
# =========================================================
def make_overstride_overlay_video_from_pipeline(
    *,
    video_path: str,
    xyzv: np.ndarray,          # (T, 33, 4)  [x_px, y_px, z, vis]
    frames: np.ndarray,        # (T,)
    contact_L: np.ndarray,     # (T,)
    contact_R: np.ndarray,     # (T,)
    over_frames: np.ndarray,   # (K,)
    over_values: np.ndarray,   # (K,)
    out_path: str,
    cfg: OverstrideOverlayConfig,
) -> str:
    """
    Overstride overlay video generator.
    """

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"비디오 열기 실패: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_path = str(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(
        out_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
    )

    # frame → ratio lookup
    ratio_map = {
        int(f): float(v) for f, v in zip(over_frames, over_values)
    }

    mp_pose = mp.solutions.pose
    t = 0

    while True:
        ret, frame = cap.read()
        if not ret or t >= len(xyzv):
            break

        pts = xyzv[t]
        frame_id = int(frames[t])

        # ----------------------------
        # Contact / ratio
        # ----------------------------
        side = None
        ratio = None
        is_contact = False

        if contact_L[t]:
            side = "L"
            is_contact = True
        elif contact_R[t]:
            side = "R"
            is_contact = True

        if is_contact and frame_id in ratio_map:
            ratio = ratio_map[frame_id]

        if ratio is None:
            is_err = False   # 색은 OK로 두거나
        else:
            is_err = ratio < cfg.ratio_lo or ratio > cfg.ratio_hi

        color = cfg.color_err if is_err else cfg.color_ok


        # ----------------------------
        # Skeleton
        # ----------------------------
        for a, b in mp_pose.POSE_CONNECTIONS:
            xa, ya, _, va = pts[a]
            xb, yb, _, vb = pts[b]
            if va < cfg.min_vis or vb < cfg.min_vis:
                continue
            cv2.line(
                frame,
                (int(xa), int(ya)),
                (int(xb), int(yb)),
                color,
                3,
                cv2.LINE_AA,
            )

        # ----------------------------
        # Contact visualization
        # ----------------------------
        if is_contact and side is not None:
            mx, my = _midhip_xy(pts)
            fx, fy = _foot_xy(pts, side, cfg.foot_point)

            # vertical guides
            cv2.line(frame, (int(mx), 0), (int(mx), h), cfg.color_midhip, 2)
            cv2.line(frame, (int(fx), 0), (int(fx), h), cfg.color_foot, 2)

            # points
            cv2.circle(frame, (int(mx), int(my)), 7, cfg.color_midhip, -1)
            cv2.circle(frame, (int(fx), int(fy)), 9, cfg.color_foot, -1)

            # HUD
            cv2.rectangle(frame, (10, 10), (380, 85), (0, 0, 0), -1)

            if ratio is None:
                label = f"OVERSTRIDE  N/A  ({side})"
            else:
                label = f"OVERSTRIDE  {ratio:.3f}  ({side})"

            cv2.putText(
                frame,
                label,
                (20, 60),
                cv2.FONT_HERSHEY_DUPLEX,
                1.3,
                (255, 255, 255),
                3,
                cv2.LINE_AA,
            )

        writer.write(frame)
        t += 1

    cap.release()
    writer.release()
    return out_path
