import os
import cv2 as cv
import mediapipe as mp

def get_pixel_heights(video_path: str):
    mp_pose = mp.solutions.pose
    cap = cv.VideoCapture(video_path)
    
    # 결과를 담을 딕셔너리 {프레임번호: 픽셀키값}
    height_results = {}

    if not cap.isOpened():
        print(f"❌ 비디오를 열 수 없습니다: {video_path}")
        return None

    # 회전 및 기초 정보 설정
    ret, first_frame = cap.read()
    if not ret: return None
    h, w = first_frame.shape[:2]
    rotated = True if w > h else False
    cap.set(cv.CAP_PROP_POS_FRAMES, 0) # 다시 처음으로

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break

        if rotated:
            frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)

        frame_height = frame.shape[0]
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        pixel_height = None
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # 좌표 추출 (Nose, Eyes, Heels)
            nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
            left_eye = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value]
            right_eye = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value]
            left_heel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value]
            right_heel = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]

            # 기존 코드의 키 계산 수식 그대로 유지
            eye_center_y = (left_eye.y + right_eye.y) / 2
            head_offset = abs(nose.y - eye_center_y) * 1.5
            head_top_y = max(0.0, nose.y - head_offset)
            foot_bottom_y = min(1.0, max(left_heel.y, right_heel.y))

            # 정규화된 좌표를 실제 픽셀 높이로 변환
            pixel_height = abs(foot_bottom_y - head_top_y) * frame_height

        # 딕셔너리에 저장 (감지 안 되면 None)
        height_results[frame_count] = pixel_height
        frame_count += 1

    pose.close()
    cap.release()
    
    return height_results # {0: 850.2, 1: 852.1, ...} 형식으로 반환