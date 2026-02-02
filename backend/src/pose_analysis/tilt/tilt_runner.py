from __future__ import annotations
from .tilt_overlay import make_overlay_video_from_keypoints_and_errframe

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .tilt_analysis import (
    TiltAnalysisConfig,
    compute_tilt_table,
    detect_tilt_error_segments,
)


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_basename(path: str | Path) -> str:
    return Path(path).stem


def _now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_tilt_analysis_and_save_results(
    keypoints_csv_path: str,
    fps: float,
    cfg: Optional[TiltAnalysisConfig] = None,
    results_dir: str = "storage/results",
    result_prefix: Optional[str] = None,
    save_tilt_table_csv: bool = True,
    save_timeline_in_json: bool = True,
    generate_overlay_video: bool = False,
    video_path: Optional[str] = None,
    overlay_min_vis: float = 0.5,
) -> Dict:
    """
    저장:
      - {base}_tilt_table.csv (옵션)
      - {base}_tilt_result.json
      - {base}_tilt_config.json

    반환:
      - 프롬프트로 보내기 좋은 dict (저장 경로 포함)
    """
    cfg = cfg or TiltAnalysisConfig()
    results_dir_path = _ensure_dir(results_dir)

    base = result_prefix or f"{_safe_basename(keypoints_csv_path)}_{_now_tag()}"

    tilt_csv_path = results_dir_path / f"{base}_tilt_table.csv"
    result_json_path = results_dir_path / f"{base}_tilt_result.json"
    config_json_path = results_dir_path / f"{base}_tilt_config.json"

    # 1) load
    df_keypoints = pd.read_csv(keypoints_csv_path)

    # 2) compute + detect
    tilt_table = compute_tilt_table(df_keypoints, cfg)
    err_frame, segments, info = detect_tilt_error_segments(tilt_table, fps, cfg)

    # 3) stats
    tilt_raw = tilt_table["tilt_deg"].to_numpy(dtype=float)

    user_mean = float(np.nanmean(tilt_raw))
    user_std = float(np.nanstd(tilt_raw))
    user_min = float(np.nanmin(tilt_raw))
    user_max = float(np.nanmax(tilt_raw))

    pro_lo = float(cfg.mu_ref - cfg.band_half)
    pro_hi = float(cfg.mu_ref + cfg.band_half)

    segments_sec = [(s / fps, e / fps) for (s, e) in segments]

    # 4) result dict
    result: Dict = {
        "input": {
            "keypoints_csv_path": str(keypoints_csv_path),
            "fps": float(fps),
            "n_frames": int(len(tilt_table)),
        },
        "pro_reference": {
            "mu_ref": float(cfg.mu_ref),
            "band_half": float(cfg.band_half),
            "pro_range_deg": [pro_lo, pro_hi],
        },
        "user_stats": {
            "tilt_mean_deg": user_mean,
            "tilt_std_deg": user_std,
            "tilt_min_deg": user_min,
            "tilt_max_deg": user_max,
        },
        "error": {
            "segments_frame": segments,
            "segments_sec": [(round(s, 2), round(e, 2)) for (s, e) in segments_sec],
            "n_segments": int(len(segments)),
            "err_ratio": float(np.mean(err_frame)) if len(err_frame) else 0.0,
            "info": asdict(info),
        },
        "artifacts": {
            "results_dir": str(results_dir_path),
            "tilt_csv_path": str(tilt_csv_path) if save_tilt_table_csv else None,
            "result_json_path": str(result_json_path),
            "config_json_path": str(config_json_path),
            "overlay_video_path": overlay_video_path,

        },
    }

    # timeline은 크니까 옵션으로
    if save_timeline_in_json:
        use_col = info.use_col
        result["timeline"] = {
            "frame": tilt_table["frame"].to_list(),
            "tilt_deg": tilt_table["tilt_deg"].to_list(),
            use_col: tilt_table[use_col].to_list(),
            "abs_dtilt": tilt_table["abs_dtilt"].to_list(),
        }
        
        overlay_video_path = None
    if generate_overlay_video:
        if not video_path:
            raise ValueError("generate_overlay_video=True면 video_path가 필요해.")
        # keypoints_csv_path는 이미 함수 입력에 있음(그걸 그대로 씀)

        overlay_out = results_dir_path / f"{base}_tilt_overlay.mp4"
        overlay_video_path = make_overlay_video_from_keypoints_and_errframe(
            video_path=video_path,
            keypoints_csv_path=keypoints_csv_path,
            err_frame=err_frame,
            out_path=str(overlay_out),
            fps_out=fps,              # 분석 fps와 동일하게
            min_vis=overlay_min_vis,
        )

    # 5) save
    if save_tilt_table_csv:
        tilt_table.to_csv(tilt_csv_path, index=False, encoding="utf-8-sig")

    with open(result_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(config_json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)

    return result
