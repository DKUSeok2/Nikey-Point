from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import mediapipe as mp

# =========================
# Config
# =========================
@dataclass
class TiltHardConfig:
    # MediaPipe Pose index
    LSHO: int = 11
    RSHO: int = 12
    LHIP: int = 23
    RHIP: int = 24

    # visibility threshold
    min_vis: float = 0.5

    # ✅ 하드 기준 (요청대로)
    # -72 이상: 너무 직립(세움)
    # -92 이하: 너무 숙임
    hard_hi: float = -72.0
    hard_lo: float = -92.0

    # overlay style
    color_ok_bgr: Tuple[int, int, int] = (0, 255, 0)
    color_err_bgr: Tuple[int, int, int] = (0, 0, 255)
    line_thickness: int = 6
    draw_points: bool = True
    draw_text: bool = True


# =========================
# Tilt definition (no smoothing)
# =========================
def compute_tilt_deg_absdx(shoulder_xy: tuple[float, float], hip_xy: tuple[float, float]) -> float:
    """
    기존 너의 tilt 정의 유지(좌/우 무관): degrees(atan2(dy, abs(dx)))
    OpenCV 좌표: x→, y↓
    """
    sx, sy = shoulder_xy
    hx, hy = hip_xy
    dx = sx - hx
    dy = sy - hy
    return float(np.degrees(np.arctan2(dy, np.abs(dx))))


def is_error_hard(tilt_deg: float, cfg: TiltHardConfig) -> bool:
    return (tilt_deg >= cfg.hard_hi) or (tilt_deg <= cfg.hard_lo)


# =========================
# 1) Extract xyzv from video (MediaPipe)
# =========================
def extract_xyzv_from_video_mediapipe(
    video_path: str,
    *,
    model_complexity: int = 1,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> Tuple[np.ndarray, float, int, int]:
    """
    Returns:
      xyzv: (T,33,4) [x_px, y_px, z, vis]
      fps, w, h
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"비디오 열기 실패: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=model_complexity,
        enable_segmentation=False,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    xyzv_list: List[np.ndarray] = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)

        if res.pose_landmarks:
            lm = res.pose_landmarks.landmark
            arr = np.zeros((33, 4), dtype=np.float32)
            for i in range(33):
                arr[i, 0] = lm[i].x * w
                arr[i, 1] = lm[i].y * h
                arr[i, 2] = lm[i].z
                arr[i, 3] = lm[i].visibility
        else:
            arr = np.zeros((33, 4), dtype=np.float32)

        xyzv_list.append(arr)

    cap.release()
    pose.close()

    xyzv = np.stack(xyzv_list, axis=0)
    return xyzv, fps, w, h


# =========================
# 2) Compute err_frame by hard thresholds only
# =========================
def compute_err_frame_hard(xyzv: np.ndarray, cfg: TiltHardConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns:
      tilt_deg: (T,)
      err_frame: (T,) bool
    """
    LS, RS, LH, RH = cfg.LSHO, cfg.RSHO, cfg.LHIP, cfg.RHIP

    # midpoints
    Sx = (xyzv[:, LS, 0] + xyzv[:, RS, 0]) / 2
    Sy = (xyzv[:, LS, 1] + xyzv[:, RS, 1]) / 2
    Hx = (xyzv[:, LH, 0] + xyzv[:, RH, 0]) / 2
    Hy = (xyzv[:, LH, 1] + xyzv[:, RH, 1]) / 2

    dx = Sx - Hx
    dy = Sy - Hy

    tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx))).astype(np.float32)

    # visibility gate: 4점 중 하나라도 min_vis 미만이면 tilt 무효(에러도 False 처리)
    vis_ok = (
        (xyzv[:, LS, 3] >= cfg.min_vis)
        & (xyzv[:, RS, 3] >= cfg.min_vis)
        & (xyzv[:, LH, 3] >= cfg.min_vis)
        & (xyzv[:, RH, 3] >= cfg.min_vis)
    )

    err_frame = np.zeros((len(xyzv),), dtype=bool)
    err_frame[vis_ok] = (tilt_deg[vis_ok] >= cfg.hard_hi) | (tilt_deg[vis_ok] <= cfg.hard_lo)

    return tilt_deg, err_frame


# =========================
# 3) Overlay: torso line only (red on error)
# =========================
def make_overlay_video_from_numpy(
    video_path: str,
    xyzv: np.ndarray,          # (T,33,4)
    tilt_deg: np.ndarray,      # (T,)
    err_frame: np.ndarray,     # (T,) bool
    out_path: str,
    cfg: TiltHardConfig,
) -> str:
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
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("VideoWriter 열기 실패 (mp4v 코덱 문제 가능)")

    LS, RS, LH, RH = cfg.LSHO, cfg.RSHO, cfg.LHIP, cfg.RHIP

    t = 0
    while True:
        ret, frame = cap.read()
        if not ret or t >= len(xyzv):
            break

        pts = xyzv[t]

        # visibility 체크
        vmin = min(float(pts[LS, 3]), float(pts[RS, 3]), float(pts[LH, 3]), float(pts[RH, 3]))
        if vmin >= cfg.min_vis:
            # midpoints
            sx = (float(pts[LS, 0]) + float(pts[RS, 0])) * 0.5
            sy = (float(pts[LS, 1]) + float(pts[RS, 1])) * 0.5
            hx = (float(pts[LH, 0]) + float(pts[RH, 0])) * 0.5
            hy = (float(pts[LH, 1]) + float(pts[RH, 1])) * 0.5

            color = cfg.color_err_bgr if bool(err_frame[t]) else cfg.color_ok_bgr

            # torso line
            cv2.line(frame, (int(hx), int(hy)), (int(sx), int(sy)), color, cfg.line_thickness, cv2.LINE_AA)

            if cfg.draw_points:
                cv2.circle(frame, (int(hx), int(hy)), 7, color, -1, cv2.LINE_AA)
                cv2.circle(frame, (int(sx), int(sy)), 7, color, -1, cv2.LINE_AA)

            if cfg.draw_text:
                cv2.putText(
                    frame,
                    f"tilt={float(tilt_deg[t]):.1f}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    color,
                    2,
                    cv2.LINE_AA,
                )

        writer.write(frame)
        t += 1

    cap.release()
    writer.release()
    return out_path
