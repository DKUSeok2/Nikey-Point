import numpy as np
import pandas as pd

class RunningPoseAnalyzer:
    def __init__(self, window_size=15):
        self.window_size = window_size
        # MediaPipe Landmark Indices
        self.LS, self.RS, self.LH, self.RH = 11, 12, 23, 24

    def _line_intersection(self, p1, p2, p3, p4):
        """두 직선의 교차점을 찾아 무게중심(CoM) 추정"""
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9: return None
        px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / den
        py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / den
        return np.array([px, py])

    def calculate_com(self, row):
        """한 프레임의 데이터에서 CoM(y) 좌표 추출"""
        try:
            p_ls = (row['x_11'], row['y_11'])
            p_rs = (row['x_12'], row['y_12'])
            p_lh = (row['x_23'], row['y_23'])
            p_rh = (row['x_24'], row['y_24'])
            
            # 대각선 교차점 계산 (어깨-골반)
            inter = self._line_intersection(p_ls, p_rh, p_rs, p_lh)
            if inter is None: # 교차점 실패 시 중점의 중점 사용
                return (p_ls[1] + p_rs[1] + p_lh[1] + p_rh[1]) / 4
            return inter[1] # y좌표만 반환
        except:
            return np.nan

    def analyze_vertical_oscillation(self, df):
        """상하 움직임의 평균과 표준편차를 계산하여 반환"""
        # 1. CoM y값 추출
        com_y = df.apply(self.calculate_com, axis=1)
        
        # 2. 노이즈 제거 (Smoothing)
        com_y_smooth = com_y.rolling(window=self.window_size, center=True).mean().dropna()
        
        # 3. 상하 움직임 폭 계산 (Sliding Window Range)
        # 런닝 한 사이클(약 30프레임) 내의 최대-최소 차이
        movement_range = com_y_smooth.rolling(window=30).apply(lambda x: x.max() - x.min()).dropna()
        
        # 4. 최종 지표 산출
        user_mean = float(movement_range.mean())
        user_std = float(movement_range.std())
        
        return user_mean, user_std

# 사용 예시:
# analyzer = RunningPoseAnalyzer()
# mean_val, std_val = analyzer.analyze_vertical_oscillation(df_user_data)