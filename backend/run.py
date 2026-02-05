"""테스트 실행 스크립트 - 3가지 지표 + LLM 피드백"""
from pathlib import Path
from src.pose_detection.extract_keypoints import PoseDetectionService
from src.pose_detection.extract_height import get_pixel_heights
from src.analysis.service import AnalysisService
from src.feedback.service import FeedbackService

# 테스트할 영상 경로
VIDEO_PATH = "src/test.mp4"
USER_HEIGHT = 175.0  # 테스트용 사용자 키 (cm)

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
