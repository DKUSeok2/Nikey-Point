from __future__ import annotations

from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np
import mediapipe as mp


def make_overlay_video_from_numpy(
    video_path: str,
    xyzv: np.ndarray,          # (T, 33, 4)
    err_frame: np.ndarray,     # (T,)
    out_path: str,
    min_vis: float = 0.5,
    color_ok_bgr: Tuple[int, int, int] = (0, 255, 0),
    color_err_bgr: Tuple[int, int, int] = (0, 0, 255),
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

    mp_pose = mp.solutions.pose
    t = 0

    while True:
        ret, frame = cap.read()
        if not ret or t >= len(xyzv):
            break

        color = color_err_bgr if err_frame[t] else color_ok_bgr
        pts = xyzv[t]

        # draw skeleton
        for a, b in mp_pose.POSE_CONNECTIONS:
            xa, ya, _, va = pts[a]
            xb, yb, _, vb = pts[b]
            if va < min_vis or vb < min_vis:
                continue
            cv2.line(
                frame,
                (int(xa), int(ya)),
                (int(xb), int(yb)),
                color,
                3,
                cv2.LINE_AA,
            )

        writer.write(frame)
        t += 1

    cap.release()
    writer.release()
    return out_path
