"""영상 회전 처리 확인 스크립트"""
import cv2
import numpy as np
from pathlib import Path

# detector.py의 회전 로직
def get_rotation_detector_style(video_path: str) -> int:
    """detector.py 방식: ffprobe로 메타데이터 확인"""
    import subprocess
    import json
    
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
               '-show_streams', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    rotation = stream.get('tags', {}).get('rotate', '0')
                    rotation_int = int(rotation)
                    
                    if rotation_int == 0:
                        print("  ⚠️  메타데이터 없음 → 기본값 90° 적용")
                        return 90
                    
                    print(f"  ✅ 메타데이터: {rotation_int}°")
                    return rotation_int
    except Exception as e:
        print(f"  ❌ ffprobe 실패: {e}")
    
    print("  ⚠️  기본값 90° 적용")
    return 90

def get_rotation_height_style(video_path: str) -> int:
    """extract_height.py 방식: width > height 체크"""
    cap = cv2.VideoCapture(video_path)
    ret, first_frame = cap.read()
    cap.release()
    
    if not ret:
        return 0
    
    h, w = first_frame.shape[:2]
    if w > h:
        print(f"  ✅ 가로가 더 김 ({w}x{h}) → 90° 회전 필요")
        return 90
    else:
        print(f"  ✅ 세로가 더 김 ({w}x{h}) → 회전 불필요")
        return 0

def rotate_frame(frame: np.ndarray, rotation: int) -> np.ndarray:
    """프레임 회전"""
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame

def visualize_rotation(video_path: str, output_path: str = "rotation_check.jpg"):
    """영상 회전 처리 시각화"""
    print(f"\n{'='*60}")
    print(f"📹 영상 분석: {Path(video_path).name}")
    print(f"{'='*60}\n")
    
    # 원본 프레임 읽기
    cap = cv2.VideoCapture(video_path)
    ret, original_frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ 영상을 읽을 수 없습니다")
        return
    
    print(f"원본 크기: {original_frame.shape[1]}x{original_frame.shape[0]}\n")
    
    # 1. detector.py 방식
    print("[1] detector.py 방식 (ffprobe 메타데이터)")
    rotation_detector = get_rotation_detector_style(video_path)
    frame_detector = rotate_frame(original_frame.copy(), rotation_detector)
    
    # 2. extract_height.py 방식
    print("\n[2] extract_height.py 방식 (width > height 체크)")
    rotation_height = get_rotation_height_style(video_path)
    frame_height = rotate_frame(original_frame.copy(), rotation_height)
    
    # 결과 비교
    print(f"\n{'='*60}")
    print("📊 결과 비교")
    print(f"{'='*60}")
    print(f"detector.py:      {rotation_detector}° 회전 → {frame_detector.shape[1]}x{frame_detector.shape[0]}")
    print(f"extract_height.py: {rotation_height}° 회전 → {frame_height.shape[1]}x{frame_height.shape[0]}")
    
    if rotation_detector != rotation_height:
        print("\n⚠️  두 방식이 다른 회전값을 사용합니다!")
    else:
        print("\n✅ 두 방식이 동일한 회전값을 사용합니다")
    
    # 이미지 합성 (나란히 배치)
    # 크기 통일 (세로 기준)
    target_height = 800
    
    def resize_keep_aspect(img, target_h):
        h, w = img.shape[:2]
        ratio = target_h / h
        new_w = int(w * ratio)
        return cv2.resize(img, (new_w, target_h))
    
    img1 = resize_keep_aspect(original_frame, target_height)
    img2 = resize_keep_aspect(frame_detector, target_height)
    img3 = resize_keep_aspect(frame_height, target_height)
    
    # 텍스트 추가
    def add_label(img, text, rotation):
        img_copy = img.copy()
        cv2.putText(img_copy, text, (10, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img_copy, f"Rotation: {rotation}", (10, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img_copy, f"Size: {img.shape[1]}x{img.shape[0]}", (10, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        return img_copy
    
    img1 = add_label(img1, "Original", 0)
    img2 = add_label(img2, "detector.py", rotation_detector)
    img3 = add_label(img3, "extract_height.py", rotation_height)
    
    # 가로로 합치기
    gap = 20  # 이미지 간 간격
    gap_img = np.ones((target_height, gap, 3), dtype=np.uint8) * 50
    result = np.hstack([img1, gap_img, img2, gap_img, img3])
    
    # 저장
    cv2.imwrite(output_path, result)
    print(f"\n💾 결과 이미지 저장: {output_path}")
    print(f"{'='*60}\n")
    
    return {
        'rotation_detector': rotation_detector,
        'rotation_height': rotation_height,
        'original_size': original_frame.shape,
        'detector_size': frame_detector.shape,
        'height_size': frame_height.shape
    }

if __name__ == "__main__":
    VIDEO_PATH = "src/test2.mp4"
    
    if not Path(VIDEO_PATH).exists():
        print(f"❌ 영상 파일이 없습니다: {VIDEO_PATH}")
    else:
        result = visualize_rotation(VIDEO_PATH)
        
        print("\n🎯 권장사항:")
        if result['rotation_detector'] != result['rotation_height']:
            print("  → extract_height.py도 detector.py와 동일한 회전 로직을 사용하도록 수정 필요")
        else:
            print("  → 두 방식이 일치하므로 문제없음")
