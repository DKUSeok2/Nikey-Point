"""러닝 지표 기준 범위 정의"""

# 3가지 지표의 정상 범위 (Ground Truth)
METRICS_REFERENCE = {
    'overstride': {
        'normal_range': (0.00, 0.18),  # 키의 12~18%
        'name': '과보폭',
        'unit': 'ratio',
        'description': '착지 시 발이 골반보다 앞으로 나가는 정도'
    },
    'tilt': {
        'normal_range': (-88.0, -72.0),  # -88도 ~ -72도 (프로 러너 범위)
        'ideal': -80.0,  # 프로 러너 평균
        'name': '상체 기울기',
        'unit': 'degrees',
        'description': '상체가 수직에서 얼마나 기울어져 있는지'
    },
    'vertical': {
        'normal_range': (0.01, 0.08),  # 변경된 범위
        'name': '수직 진동',
        'unit': 'ratio',
        'description': '러닝 중 몸의 상하 움직임 폭'
    }
}


def is_in_range(value: float, metric_name: str) -> bool:
    """지표가 정상 범위 안에 있는지 확인"""
    if metric_name not in METRICS_REFERENCE:
        return False
    
    min_val, max_val = METRICS_REFERENCE[metric_name]['normal_range']
    return min_val <= value <= max_val


def get_status(value: float, metric_name: str) -> str:
    """지표 상태 반환"""
    if is_in_range(value, metric_name):
        return '✅ 정상'
    return '⚠️ 범위 벗어남'
