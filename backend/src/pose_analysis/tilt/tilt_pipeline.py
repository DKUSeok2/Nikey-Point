from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from .tilt_analysis import (
    TiltAnalysisConfig,
    compute_tilt_from_numpy,
    detect_tilt_error_segments,
)
from .tilt_overlay import make_overlay_video_from_numpy


def run_tilt_analysis(
    *,
    frames: np.ndarray,
    xyzv: np.ndarray,
    fps: float,
    cfg: Optional[TiltAnalysisConfig] = None,
    generate_overlay_video: bool = False,
    video_path: Optional[str] = None,
) -> float:
    """
    Args:
        frames: (T,)
        xyzv: (T, 33, 4)
        fps: video fps

    Returns:
        tilt_mean (float)
    """
    cfg = cfg or TiltAnalysisConfig()

    tilt_df = compute_tilt_from_numpy(frames, xyzv, cfg)
    err_frame, segments, info = detect_tilt_error_segments(tilt_df, fps, cfg)

    tilt_mean = float(np.nanmean(tilt_df["tilt_deg"].to_numpy()))

    if generate_overlay_video:
        if not video_path:
            raise ValueError("overlay 생성하려면 video_path 필요")

        out_path = Path("storage/videos") / "tilt_overlay.mp4"
        make_overlay_video_from_numpy(
            video_path=video_path,
            xyzv=xyzv,
            err_frame=err_frame,
            out_path=str(out_path),
        )

    return tilt_mean
