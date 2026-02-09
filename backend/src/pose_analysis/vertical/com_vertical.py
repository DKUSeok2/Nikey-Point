import numpy as np


def calculate_vertical_oscillation(xyzv: np.ndarray, pixel_heights: dict) -> float:
    """
    xyzv: np.ndarray shape (T, 33, 4) -> [x_px, y_px, z, v]
    pixel_heights: dict {frame_no: pixel_height_px}

    Returns: 정규화된 수직 진동 평균값 (키 대비 비율, 예: 0.05 -> 키의 5%)
    """
    T = xyzv.shape[0]
    com_y_list = []

    # 1. 프레임별 CoM(수직 중심점) 계산 (y값만 사용)
    for t in range(T):
        # 11:왼쪽어깨, 12:오른쪽어깨, 23:왼쪽골반, 24:오른쪽골반
        # xyzv의 인덱스 1이 y_px 값임
        y_indices = [11, 12, 23, 24]
        y_values = xyzv[t, y_indices, 1]
        v_values = xyzv[t, y_indices, 3]  # 가시성(Visibility)

        # 모든 포인트가 유효하고 가시성이 0.5 이상인 경우만 계산
        if np.any(np.isnan(y_values)) or np.any(v_values < 0.5):
            com_y_list.append(np.nan)
        else:
            com_y_list.append(np.mean(y_values))

    com_y_arr = np.array(com_y_list)

    # 2. 결측치 처리 및 노이즈 제거 (Smoothing)
    mask = np.isnan(com_y_arr)
    if np.all(mask): return 0.0

    # 결측치 보간 (선형 보간)
    com_y_arr[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), com_y_arr[~mask])
    
    # 이동 평균으로 데이터 부드럽게 (window=15, 데이터 길이에 맞게 조정)
    smooth_window = min(15, len(com_y_arr))
    if smooth_window % 2 == 0:
        smooth_window -= 1  # 홀수로 만들기
    smoothed = np.convolve(com_y_arr, np.ones(smooth_window)/smooth_window, mode='same')

    # 3. 추세 제거 (Detrending) - 순수 진동 성분만 추출
    trend_window = min(101, len(smoothed))
    if trend_window % 2 == 0:
        trend_window -= 1  # 홀수로 만들기
    trend = np.convolve(smoothed, np.ones(trend_window)/trend_window, mode='same')
    pure_oscillation = smoothed - trend

    # 4. 수직 진폭(Range) 계산 (30프레임 윈도우 내 max - min)
    # 처음 30프레임과 마지막 30프레임 제외 (이상치 제거)
    skip_frames = 30
    ranges = []
    
    start_idx = skip_frames
    end_idx = max(start_idx, len(pure_oscillation) - 30 - skip_frames)
    
    for i in range(start_idx, end_idx):
        window = pure_oscillation[i: i + 30]
        ranges.append(np.max(window) - np.min(window))

    if not ranges: return 0.0

    # 5. [중요] 정규화 단계
    # 픽셀 단위의 평균 진동 폭
    mean_oscillation_px = np.mean(ranges)

    # 영상 전체에서 감지된 평균 키 픽셀값 (기준자)
    valid_heights = [h for h in pixel_heights.values() if h is not None]
    if not valid_heights: return 0.0
    avg_person_height_px = np.mean(valid_heights)

    # 최종 정규화 값 (키 대비 진동 비율)
    normalized_oscillation = mean_oscillation_px / avg_person_height_px

    return float(normalized_oscillation)