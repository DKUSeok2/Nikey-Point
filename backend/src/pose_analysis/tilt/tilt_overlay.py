
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp


def get_video_fps_and_shape(video_path: str) -> Tuple[float, Tuple[int, int], int]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"비디오를 열 수 없습니다: {video_path}")
    fps_meta = float(cap.get(cv2.CAP_PROP_FPS))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return fps_meta, (w, h), n


def draw_skeleton_on_frame(
    frame: np.ndarray,
    keypoints_row: dict,
    color_bgr: Tuple[int, int, int],
    min_vis: float = 0.5,
    thickness: int = 3,
    circle_radius: int = 3,
) -> np.ndarray:
    """
    네가 올린 방식 그대로:
    - keypoints_row에서 x_i, y_i, v_i를 읽어 33개 점 구성
    - mp.solutions.pose.POSE_CONNECTIONS로 선 그리기
    """
    h, w = frame.shape[:2]
    mp_pose = mp.solutions.pose

    pts = []
    vis = []

    for i in range(33):
        x = keypoints_row.get(f"x_{i}", np.nan)
        y = keypoints_row.get(f"y_{i}", np.nan)
        v = keypoints_row.get(f"v_{i}", np.nan)

        if np.isfinite(x) and np.isfinite(y):
            px = int(np.clip(float(x), 0.0, 1.0) * w)
            py = int(np.clip(float(y), 0.0, 1.0) * h)
            pts.append((px, py))
        else:
            pts.append(None)

        vis.append(float(v) if np.isfinite(v) else 1.0)

    # connections
    for a, b in mp_pose.POSE_CONNECTIONS:
        pa, pb = pts[a], pts[b]
        if pa is None or pb is None:
            continue
        if (vis[a] < min_vis) or (vis[b] < min_vis):
            continue
        cv2.line(frame, pa, pb, color_bgr, thickness, lineType=cv2.LINE_AA)

    # points
    for i, p in enumerate(pts):
        if p is None:
            continue
        if vis[i] < min_vis:
            continue
        cv2.circle(frame, p, circle_radius, color_bgr, -1, lineType=cv2.LINE_AA)

    return frame


def make_overlay_video_from_keypoints_and_errframe(
    video_path: str,
    keypoints_csv_path: str,
    err_frame: np.ndarray,
    out_path: str,
    fps_out: Optional[float] = None,
    min_vis: float = 0.5,
    color_ok_bgr: Tuple[int, int, int] = (0, 255, 0),
    color_err_bgr: Tuple[int, int, int] = (0, 0, 255),
    thickness: int = 3,
    circle_radius: int = 3,
) -> str:
    """
    - 원본 영상 읽기
    - keypoints CSV 읽기
    - err_frame True면 빨강, False면 초록 스켈레톤
    - mp4로 저장
    """
    kp_df = pd.read_csv(keypoints_csv_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"비디오를 열 수 없습니다: {video_path}")

    fps_meta = float(cap.get(cv2.CAP_PROP_FPS))
    fps_use = float(fps_out) if fps_out is not None else fps_meta

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    max_idx = min(total_frames, len(kp_df), len(err_frame))

    out_path = str(out_path)
    os.makedirs(str(Path(out_path).parent), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps_use, (w, h))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"VideoWriter 열기 실패: {out_path}")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or frame_idx >= max_idx:
            break

        row = kp_df.iloc[frame_idx].to_dict()
        is_err = bool(err_frame[frame_idx])

        color = color_err_bgr if is_err else color_ok_bgr

        frame = draw_skeleton_on_frame(
            frame,
            row,
            color_bgr=color,
            min_vis=min_vis,
            thickness=thickness,
            circle_radius=circle_radius,
        )

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    return out_path

