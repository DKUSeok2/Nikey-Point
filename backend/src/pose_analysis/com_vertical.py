import numpy as np
import pandas as pd

class VerticalOscillationAnalyzer:
    def __init__(self, window_size=15, trend_window=101):
        self.window_size = window_size
        self.trend_window = trend_window
        self.LS, self.RS = 11, 12
        self.LH, self.RH = 23, 24

    def calculate_com(self, row, height=None): # height 파라미터 추가
        try:
            x1, y1 = row[f'x_{self.LS}'], row[f'y_{self.LS}']
            x2, y2 = row[f'x_{self.RH}'], row[f'y_{self.RH}']
            x3, y3 = row[f'x_{self.RS}'], row[f'y_{self.RS}']
            x4, y4 = row[f'x_{self.LH}'], row[f'y_{self.LH}']

            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

            if abs(den) < 1e-9:
                return (y1 + y2 + y3 + y4) / 4

            py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den

            # [핵심 수정] 0~1 사이가 아니라 0~영상 높이(height) 사이인지 확인(픽셀로 변환 시)
            # height 정보가 없다면 최소한 0보다 큰지만 확인하도록 유연하게 대처
            upper_limit = height if height else 5000 # 넉넉한 픽셀값
            if not (0 <= py <= upper_limit):
                return (y1 + y2 + y3 + y4) / 4

            return py
        except:
            return np.nan

    def analyze(self, df, height=None):
        # 1. 원본 CoM 추출 (row별로 height 전달)
        df['com_y_raw'] = df.apply(lambda row: self.calculate_com(row, height), axis=1)

        # 2. Smoothing
        df['com_y_smooth'] = df['com_y_raw'].rolling(
            window=self.window_size, center=True, min_periods=1
        ).mean()

        # 3. Detrending
        df['trend'] = df['com_y_smooth'].rolling(
            window=self.trend_window, center=True, min_periods=1
        ).mean()
        df['pure_oscillation'] = df['com_y_smooth'] - df['trend']

        # 4. Vertical Range (픽셀 단위로 나옴)
        df['vertical_range'] = df['pure_oscillation'].rolling(window=30, min_periods=1).apply(
            lambda x: x.max() - x.min()
        )

        # 5. 통계값 계산
        mean_val = df['vertical_range'].mean()
        std_val = df['vertical_range'].std()

        # [추가 지표] 해상도에 상관없이 비교하고 싶다면? (정규화 평균)
        norm_mean = mean_val / height if height else None

        summary = {
            'mean_px': mean_val,   # 픽셀 단위 평균 진폭
            'std_px': std_val,     # 픽셀 단위 표준편차
            'mean_norm': norm_mean # 해상도 대비 비율 (0~1)
        }

        return df, summary

# 사용 예시:
# analyzer = RunningPoseAnalyzer()
# mean_val, std_val = analyzer.analyze_vertical_oscillation(df_user_data)