from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np
from fastapi import HTTPException, status

# MediaPipe detector import
from .detector import MediaPipeDetector


DEFAULT_VIDEOS_DIR = Path("storage/videos")


# =========================
# Utils
# =========================

def _find_latest_mp4(videos_dir: Path = DEFAULT_VIDEOS_DIR) -> Path:
    if not videos_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Videos directory not found: {videos_dir}",
        )

    mp4_files = [p for p in videos_dir.glob("*.mp4") if p.is_file()]
    if not mp4_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mp4 files found in: {videos_dir}",
        )

    mp4_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return mp4_files[0]


def _landmarks_to_numpy(
    landmarks: Any,
    frame_width: int,
    frame_height: int,
) -> np.ndarray:
    """
    MediaPipe normalized landmarks -> pixel numpy array

    Returns:
        np.ndarray shape (L, 4) = [x_px, y_px, z, v]
        - x, y: pixel coordinates
        - z: normalized depth (as-is)
        - v: visibility (없으면 np.nan)
        - landmarks가 없으면 (0, 4) 반환
    """
    if landmarks is None:
        return np.empty((0, 4), dtype=np.float32)

    w = float(frame_width)
    h = float(frame_height)

    # Case 1) dict[str, dict] - from detector
    if isinstance(landmarks, dict) and landmarks:
        # Convert dict to list in order
        landmark_list = []
        for name, lm in landmarks.items():
            landmark_list.append(lm)
        
        arr = np.full((len(landmark_list), 4), np.nan, dtype=np.float32)
        for i, lm in enumerate(landmark_list):
            x = lm.get("x")
            y = lm.get("y")
            z = lm.get("z")
            v = lm.get("visibility", lm.get("v"))

            arr[i, 0] = np.nan if x is None else float(x) * w
            arr[i, 1] = np.nan if y is None else float(y) * h
            arr[i, 2] = np.nan if z is None else float(z)
            arr[i, 3] = np.nan if v is None else float(v)
        return arr

    # Case 2) list[dict]
    if isinstance(landmarks, list) and landmarks and isinstance(landmarks[0], dict):
        arr = np.full((len(landmarks), 4), np.nan, dtype=np.float32)
        for i, lm in enumerate(landmarks):
            x = lm.get("x")
            y = lm.get("y")
            z = lm.get("z")
            v = lm.get("visibility", lm.get("v"))

            arr[i, 0] = np.nan if x is None else float(x) * w
            arr[i, 1] = np.nan if y is None else float(y) * h
            arr[i, 2] = np.nan if z is None else float(z)
            arr[i, 3] = np.nan if v is None else float(v)
        return arr

    # Case 2) list of objects with attributes
    if isinstance(landmarks, list) and landmarks:
        first = landmarks[0]
        if hasattr(first, "x") and hasattr(first, "y"):
            arr = np.full((len(landmarks), 4), np.nan, dtype=np.float32)
            for i, lm in enumerate(landmarks):
                x = getattr(lm, "x", None)
                y = getattr(lm, "y", None)
                z = getattr(lm, "z", None)
                v = getattr(lm, "visibility", None)

                arr[i, 0] = np.nan if x is None else float(x) * w
                arr[i, 1] = np.nan if y is None else float(y) * h
                arr[i, 2] = np.nan if z is None else float(z)
                arr[i, 3] = np.nan if v is None else float(v)
            return arr

    return np.empty((0, 4), dtype=np.float32)


# =========================
# Core Service (DB ❌)
# =========================

class PoseDetectionService:
    """
    영상 -> 프레임별 (frame_number, xyzv 픽셀/값) numpy 배열로 반환
    """

    def __init__(self, detector: Optional[MediaPipeDetector] = None):
        self.detector = detector or MediaPipeDetector()

    def extract_keypoints_numpy(
        self,
        *,
        video_path: str,
        user_height: float | None = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Args:
            video_path: mp4 경로
            user_height: detector에 전달 (옵션)

        Returns:
            frames: np.ndarray shape (T,) int32
            xyzv:   np.ndarray shape (T, L, 4) float32
                    [x_px, y_px, z, v]
        """
        video_path_p = Path(video_path)
        if not video_path_p.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video not found: {video_path}",
            )

        frame_numbers: list[int] = []
        xyzv_frames: list[np.ndarray] = []

        for frame_data in self.detector.process_video(str(video_path_p), user_height):
            frame_w = frame_data.get("frame_width")
            frame_h = frame_data.get("frame_height")

            if frame_w is None or frame_h is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Detector must provide frame_width/frame_height.",
                )

            lm_arr = _landmarks_to_numpy(
                landmarks=frame_data.get("landmarks"),
                frame_width=int(frame_w),
                frame_height=int(frame_h),
            )

            frame_numbers.append(int(frame_data["frame_number"]))
            xyzv_frames.append(lm_arr)

        if not xyzv_frames:
            return (
                np.empty((0,), dtype=np.int32),
                np.empty((0, 0, 4), dtype=np.float32),
            )

        # pad to (T, maxL, 4)
        maxL = max(a.shape[0] for a in xyzv_frames)
        T = len(xyzv_frames)

        xyzv = np.full((T, maxL, 4), np.nan, dtype=np.float32)
        for t, a in enumerate(xyzv_frames):
            if a.size == 0:
                continue
            L = a.shape[0]
            xyzv[t, :L, :] = a

        frames = np.asarray(frame_numbers, dtype=np.int32)
        return frames, xyzv


# =========================
# Entry Point (테스트용)
# =========================

def extract_latest_video_keypoints_numpy(
    *,
    videos_dir: Path = DEFAULT_VIDEOS_DIR,
    user_height: float | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    latest_mp4 = _find_latest_mp4(videos_dir)
    svc = PoseDetectionService()
    return svc.extract_keypoints_numpy(
        video_path=str(latest_mp4),
        user_height=user_height,
    )


if __name__ == "__main__":
    frames, xyzv = extract_latest_video_keypoints_numpy(user_height=None)

    print("✅ frames shape:", frames.shape, "dtype:", frames.dtype)
    print("✅ xyzv shape:", xyzv.shape, "dtype:", xyzv.dtype)
    if frames.size > 0:
        print("✅ first frame_number:", int(frames[0]))
        print("✅ first frame xyzv (first 5 landmarks):\n", xyzv[0, :5, :])
