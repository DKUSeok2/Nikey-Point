"""테스트 실행 스크립트 - 3가지 지표 + LLM 피드백 + 오버레이 생성"""
from pathlib import Path
import numpy as np
from src.pose_detection.extract_keypoints import PoseDetectionService
from src.pose_detection.extract_height import get_pixel_heights
from src.analysis.service import AnalysisService
from src.feedback.service import FeedbackService

# 테스트할 영상 경로
VIDEO_PATH = "src/test.mp4"
USER_HEIGHT = 175.0  # 테스트용 사용자 키 (cm)
OUTPUT_DIR = Path("storage/test_outputs")

if __name__ == "__main__":
    print("=" * 50)
    print("🏃 러닝 분석 시작")
    print("=" * 50)
    
    # 1. Keypoint 추출
    print("\n[1/3] Keypoint 추출 중...")
    pose_service = PoseDetectionService()
    frames, xyzv = pose_service.extract_keypoints_numpy(video_path=VIDEO_PATH)
    print(f"✅ {len(frames)} 프레임 추출 완료")
    print(f"   xyzv shape: {xyzv.shape}")
    
    # 2. Pixel heights 계산
    print("\n[2/3] Pixel heights 계산 중...")
    pixel_heights = get_pixel_heights(VIDEO_PATH)
    print(f"✅ Pixel heights 계산 완료")
    
    # 3. 3가지 지표 계산
    print("\n[3/3] 지표 계산 중...")
    service = AnalysisService()
    metrics = service.calculate_metrics(
        frames=frames,
        xyzv=xyzv,
        pixel_heights=pixel_heights,
        fps=30.0
    )
    
    # 결과 출력
    print("\n" + "=" * 50)
    print("📊 분석 결과")
    print("=" * 50)
    print(f"Overstride (과보폭):     {metrics['overstride']:.4f}")
    print(f"Tilt (상체 기울기):      {metrics['tilt']:.2f}°")
    print(f"Vertical (수직 진동):    {metrics['vertical']:.4f}")
    print("=" * 50)
    
    # 4. LLM 피드백 생성
    print("\n[4/4] LLM 피드백 생성 중...")
    feedback_service = FeedbackService()
    feedback = feedback_service.generate_feedback(
        overstride=metrics['overstride'],
        tilt=metrics['tilt'],
        vertical=metrics['vertical'],
        user_height=USER_HEIGHT
    )
    
    print("\n" + "=" * 50)
    print("💬 LLM 피드백")
    print("=" * 50)
    print(feedback)
    print("=" * 50)
    
    # 5. Tilt 오버레이 생성
    print("\n[5/6] Tilt 오버레이 생성 중...")
    from src.pose_analysis.tilt.tilt_analysis import (
        TiltAnalysisConfig,
        compute_tilt_from_numpy,
        detect_tilt_error_segments,
    )
    from src.pose_analysis.tilt.tilt_overlay import (
        make_overlay_video_from_numpy as make_tilt_overlay,
        TiltHardConfig
    )
    
    tilt_cfg = TiltAnalysisConfig()
    tilt_df = compute_tilt_from_numpy(frames, xyzv, tilt_cfg)
    tilt_deg = tilt_df["tilt_smooth"].to_numpy(dtype=float)
    err_frame, segments, info = detect_tilt_error_segments(tilt_df, 30.0, tilt_cfg)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tilt_output = OUTPUT_DIR / "tilt_overlay.mp4"
    
    overlay_cfg = TiltHardConfig(hard_hi=-72.0, hard_lo=-92.0)
    make_tilt_overlay(
        video_path=VIDEO_PATH,
        xyzv=xyzv,
        tilt_deg=tilt_deg,
        err_frame=err_frame,
        out_path=str(tilt_output),
        cfg=overlay_cfg
    )
    print(f"✅ Tilt 오버레이 저장: {tilt_output}")
    
    # 6. Overstride 오버레이 생성
    print("\n[6/6] Overstride 오버레이 생성 중...")
    from src.pose_analysis.overstride.abk import detect_contacts_abk
    from src.pose_analysis.overstride.overstride import (
        xyzv_to_keypoints_df,
        compute_overstride_numpy,
        height_dict_to_df
    )
    from src.pose_analysis.overstride.overstride_overlay import (
        make_overstride_overlay_video_from_pipeline,
        OverstrideOverlayConfig
    )
    
    keypoints_df = xyzv_to_keypoints_df(frames, xyzv)
    contact_L, contact_R, debug = detect_contacts_abk(keypoints_df)
    height_df = height_dict_to_df(pixel_heights)
    
    over_frames, over_values, mean_overstride = compute_overstride_numpy(
        keypoints_df=keypoints_df,
        contact_L=contact_L,
        contact_R=contact_R,
        height_df=height_df,
        frames=frames,
        point="toe"
    )
    
    overstride_output = OUTPUT_DIR / "overstride_overlay.mp4"
    overstride_cfg = OverstrideOverlayConfig(ratio_hi=0.18, ratio_lo=0.0)
    
    make_overstride_overlay_video_from_pipeline(
        video_path=VIDEO_PATH,
        xyzv=xyzv,
        frames=frames,
        contact_L=contact_L,
        contact_R=contact_R,
        over_frames=over_frames,
        over_values=over_values,
        out_path=str(overstride_output),
        cfg=overstride_cfg
    )
    print(f"✅ Overstride 오버레이 저장: {overstride_output}")
    
    print("\n" + "=" * 50)
    print("🎉 모든 작업 완료!")
    print("=" * 50)
    print(f"📁 출력 디렉토리: {OUTPUT_DIR}")
    print(f"   - tilt_overlay.mp4")
    print(f"   - overstride_overlay.mp4")
    print("=" * 50)
