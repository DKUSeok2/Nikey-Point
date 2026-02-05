from __future__ import annotations

from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np

# MediaPipe Pose landmark indices
LSHO, RSHO = 11, 12
LHIP, RHIP = 23, 24


def compute_tilt_deg(shoulder_xy: tuple[float, float], hip_xy: tuple[float, float]) -> float:
    """
    mediapipe 실시간 버전과 동일한 방식:
    angle = degrees(atan2(dy, dx))
    (OpenCV 좌표: x→, y↓)
    """
    sx, sy = shoulder_xy
    hx, hy = hip_xy
    dx = sx - hx
    dy = sy - hy
    return float(np.degrees(np.arctan2(dy, dx)))


def make_overlay_video_from_numpy(
    video_path: str,
    xyzv: np.ndarray,          # (T, 33, 4)  x,y: 픽셀 / v: visibility
    err_frame: np.ndarray,     # (T,) bool 또는 0/1
    out_path: str,
    min_vis: float = 0.5,
    color_ok_bgr: Tuple[int, int, int] = (0, 255, 0),
    color_err_bgr: Tuple[int, int, int] = (0, 0, 255),
    line_thickness: int = 6,
    draw_points: bool = True,
    draw_text: bool = True,
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

    # err_frame 안전 처리 (float 들어와도 OK)
    err_bool = (err_frame.astype(np.float32) > 0)

    t = 0
    while True:
        ret, frame = cap.read()
        if not ret or t >= len(xyzv):
            break

        color = color_err_bgr if bool(err_bool[t]) else color_ok_bgr
        pts = xyzv[t]  # (33,4)

        # ---- (핵심) 어깨 중앙 / 골반 중앙 계산 ----
        lsho = pts[LSHO]  # (x,y,z,v)
        rsho = pts[RSHO]
        lhip = pts[LHIP]
        rhip = pts[RHIP]

        vmin = min(float(lsho[3]), float(rsho[3]), float(lhip[3]), float(rhip[3]))

        if vmin >= min_vis:
            sx = (float(lsho[0]) + float(rsho[0])) * 0.5
            sy = (float(lsho[1]) + float(rsho[1])) * 0.5
            hx = (float(lhip[0]) + float(rhip[0])) * 0.5
            hy = (float(lhip[1]) + float(rhip[1])) * 0.5

            # ---- 몸통(기울기) 선만 그림 ----
            cv2.line(
                frame,
                (int(hx), int(hy)),
                (int(sx), int(sy)),
                color,
                line_thickness,
                cv2.LINE_AA,
            )

            # 점 표시 (mediapipe 버전과 동일 옵션)
            if draw_points:
                cv2.circle(frame, (int(hx), int(hy)), 7, color, -1, cv2.LINE_AA)
                cv2.circle(frame, (int(sx), int(sy)), 7, color, -1, cv2.LINE_AA)

            # 각도 텍스트 표시 (원하면)
            if draw_text:
                tilt_deg = compute_tilt_deg((sx, sy), (hx, hy))
                cv2.putText(
                    frame,
                    f"tilt={tilt_deg:.1f}",
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
