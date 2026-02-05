"""
러닝 분석 배치 실행 스크립트

- storage/videos 내 모든 mp4 처리
- 러너(영상)별 3가지 지표 계산
- 프레임별 CSV 저장
  1) overstride (정규화, 착지 프레임만)
  2) height (pixel height)
  3) keypoints (x, y, z, v)
"""

from pathlib import Path
import pandas as pd

from backend.src.pose_detection.extract_keypoints import PoseDetectionService
from backend.src.pose_detection.extract_height import get_pixel_heights
from backend.src.analysis.service import AnalysisService

from backend.src.pose_analysis.overstride.overstride import (
    xyzv_to_keypoints_df,
    height_dict_to_df,
    compute_overstride_numpy,
)
from backend.src.pose_analysis.overstride.abk import detect_contacts_abk


# =========================
# 경로 설정
# =========================

BASE_DIR = Path(__file__).resolve().parent          # backend
VIDEO_DIR = BASE_DIR / "storage" / "videos"
RESULTS_DIR = BASE_DIR / "storage" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# 메인 실행
# =========================
if __name__ == "__main__":
    print("=" * 60)
    print("🏃 러닝 분석 배치 시작")
    print("=" * 60)

    video_paths = sorted(VIDEO_DIR.glob("*.mp4"))
    if not video_paths:
        raise RuntimeError(f"❌ mp4 파일이 없습니다: {VIDEO_DIR}")

    analysis_service = AnalysisService()
    all_results = []

    for video_path in video_paths:
        runner_id = video_path.stem

        print("\n" + "-" * 60)
        print(f"🏃 러너 분석 시작: {runner_id}")
        print("-" * 60)

        # ---------------------------------
        # 0. Pose 서비스 (영상마다 새로)
        # ---------------------------------
        pose_service = PoseDetectionService()

        # ---------------------------------
        # 1. Keypoints
        # ---------------------------------
        print("[1/3] Keypoint 추출 중...")
        frames, xyzv = pose_service.extract_keypoints_numpy(
            video_path=str(video_path)
        )
        print(f"✅ 프레임 수: {len(frames)}, xyzv: {xyzv.shape}")

        # ---------------------------------
        # 2. Pixel heights
        # ---------------------------------
        print("[2/3] Pixel heights 계산 중...")
        pixel_heights = get_pixel_heights(str(video_path))
        print("✅ Pixel heights 완료")

        # ---------------------------------
        # 3. 요약 지표 계산
        # ---------------------------------
        print("[3/3] 지표 계산 중...")
        metrics = analysis_service.calculate_metrics(
            frames=frames,
            xyzv=xyzv,
            pixel_heights=pixel_heights,
            fps=30.0,
        )

        print("📊 분석 결과")
        print(f"  Overstride : {metrics['overstride']}")
        print(f"  Tilt       : {metrics['tilt']:.2f}°")
        print(f"  Vertical   : {metrics['vertical']:.4f}")

        metrics["runner"] = runner_id
        all_results.append(metrics)

        # =========================================================
        # 📁 CSV 저장 파트
        # =========================================================

        # ---------- A. Height CSV ----------
        height_df = pd.DataFrame([
            {
                "frame": int(f),
                "pixel_height": h,
                "detected": h is not None
            }
            for f, h in pixel_heights.items()
        ])

        height_csv = RESULTS_DIR / f"{runner_id}_height.csv"
        height_df.to_csv(height_csv, index=False)
        print(f"💾 Height CSV 저장: {height_csv.name}")

        # ---------- B. Keypoints CSV ----------
        rows = []
        for t, frame in enumerate(frames):
            for lm_id in range(xyzv.shape[1]):
                x, y, z, v = xyzv[t, lm_id]
                rows.append({
                    "frame": int(frame),
                    "landmark": lm_id,
                    "x": x,
                    "y": y,
                    "z": z,
                    "v": v,
                })

        keypoints_df = pd.DataFrame(rows)
        keypoints_csv = RESULTS_DIR / f"{runner_id}_keypoints.csv"
        keypoints_df.to_csv(keypoints_csv, index=False)
        print(f"💾 Keypoints CSV 저장: {keypoints_csv.name}")

        # ---------- C. Overstride (per-frame) CSV ----------
        kp_df = xyzv_to_keypoints_df(frames, xyzv)
        height_df2 = height_dict_to_df(pixel_heights)
        contact_L, contact_R, _ = detect_contacts_abk(kp_df)

        os_frames, os_values, os_mean = compute_overstride_numpy(
            keypoints_df=kp_df,
            contact_L=contact_L,
            contact_R=contact_R,
            height_df=height_df2,
            frames=frames,
            point="toe",
        )

        overstride_df = pd.DataFrame({
            "frame": os_frames,
            "overstride_norm": os_values,
        })

        overstride_csv = RESULTS_DIR / f"{runner_id}_overstride.csv"
        overstride_df.to_csv(overstride_csv, index=False)
        print(f"💾 Overstride CSV 저장: {overstride_csv.name}")

        # =========================================================
        # 🎥 Overstride Overlay Video 생성
        # =========================================================
        from backend.src.pose_analysis.overstride.overstride_overlay import (
            make_overstride_overlay_video_from_pipeline,
            OverstrideOverlayConfig,
        )

        OVERLAY_DIR = RESULTS_DIR / "overstride_overlay"
        OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

        overlay_out = OVERLAY_DIR / f"{runner_id}_overstride_overlay.mp4"

        overlay_cfg = OverstrideOverlayConfig(
            ratio_hi=0.18,
            ratio_lo=0.00,
            foot_point="toe",
        )

        make_overstride_overlay_video_from_pipeline(
            video_path=str(video_path),
            xyzv=xyzv,
            frames=frames,
            contact_L=contact_L,
            contact_R=contact_R,
            over_frames=os_frames,
            over_values=os_values,
            out_path=str(overlay_out),
            cfg=overlay_cfg,
        )

        print(f"🎥 Overstride Overlay 저장: {overlay_out.name}")


    print("\n" + "=" * 60)
    print("🎉 모든 러너 분석 완료")
    print("=" * 60)
