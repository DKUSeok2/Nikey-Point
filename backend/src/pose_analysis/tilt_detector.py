#%%
# 입력
CSV_PATH = "/Users/yoochaewon/Desktop/after/keypoints_3_2.csv"

# 출력 및 측정
OUT_PATH = "/Users/yoochaewon/Desktop/after/tilt_values_keypoints_3_2.csv"
#%%
# csv 파일 뽑아내는 코드
import numpy as np
import pandas as pd

# =========================
# CSV 로드 + 컬럼 찾기
# =========================
df = pd.read_csv(CSV_PATH)


def col_xy(i: int):
    candidates = [
        (f"x_{i}", f"y_{i}"),
        (f"{i}_x", f"{i}_y"),
        (f"landmark_{i}_x", f"landmark_{i}_y"),
        (f"X_{i}", f"Y_{i}")
    ]
    for cx, cy in candidates:
        if cx in df.columns and cy in df.columns:
            return cx, cy
    raise KeyError(f"landmark {i}의 x/y 컬럼을 못 찾았어.")


FRAME_COL = "Frame" if "Frame" in df.columns else ("frame" if "frame" in df.columns else None)
if FRAME_COL is None:
    df["Frame"] = np.arange(len(df))
    FRAME_COL = "Frame"

# =========================
# TiltAngle 계산 (mid-hip -> mid-shoulder)
# =========================
LSHO, RSHO, LHIP, RHIP = 11, 12, 23, 24

x11, y11 = df[col_xy(LSHO)[0]], df[col_xy(LSHO)[1]]
x12, y12 = df[col_xy(RSHO)[0]], df[col_xy(RSHO)[1]]
x23, y23 = df[col_xy(LHIP)[0]], df[col_xy(LHIP)[1]]
x24, y24 = df[col_xy(RHIP)[0]], df[col_xy(RHIP)[1]]

Sx = (x11 + x12) / 2
Sy = (y11 + y12) / 2
Hx = (x23 + x24) / 2
Hy = (y23 + y24) / 2

dx = (Sx - Hx).to_numpy()
dy = (Sy - Hy).to_numpy()

tilt_deg = np.degrees(np.arctan2(dy, np.abs(dx)))  # ✅ 좌/우 무관

# =========================
# 스무딩 + 변화량(옵션)
# =========================
win = 7
tilt_smooth = pd.Series(tilt_deg).rolling(win, center=True, min_periods=1).mean().to_numpy()
dtilt = np.diff(tilt_deg, prepend=tilt_deg[0])
dtilt_abs = np.abs(dtilt)

# =========================
# 결과 CSV 생성
# =========================
out_df = pd.DataFrame({
    "frame": df[FRAME_COL].to_numpy(),
    "tilt_deg": tilt_deg,
    "tilt_smooth_MA7": tilt_smooth,
    "dtilt_deg_per_frame": dtilt,
    "abs_dtilt": dtilt_abs,
    "mid_shoulder_x": Sx.to_numpy() if hasattr(Sx, "to_numpy") else np.array(Sx),
    "mid_shoulder_y": Sy.to_numpy() if hasattr(Sy, "to_numpy") else np.array(Sy),
    "mid_hip_x": Hx.to_numpy() if hasattr(Hx, "to_numpy") else np.array(Hx),
    "mid_hip_y": Hy.to_numpy() if hasattr(Hy, "to_numpy") else np.array(Hy),
})

out_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

print("✅ 저장 완료:", OUT_PATH)
print("rows:", len(out_df), "cols:", len(out_df.columns))
print(out_df.head())

# =========================
# 상체 기울기 에러 찾기
# =========================

import numpy as np


def robust_sigma_mad(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return np.nan
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    return 1.4826 * mad


def find_error_segments_from_tilt_csv(
        tilt_csv_path: str,
        fps: float,
        use_col: str = "tilt_smooth_MA7",
        mu_ref: float = -82.5,  # 정답 중심
        band_half: float = 4.5,  # 정답 밴드 반폭 ([-87,-78])
        hard_hi: float = -68.0,  # 즉시 에러 상한 (너무 덜 숙임)
        hard_lo: float = -97.0,  # 즉시 에러 하한 (너무 숙임)
        k: float = 2.5,  # 적응형 허용폭 계수
        max_abs_dtilt: float = 6.0,  # 프레임당 변화량 너무 크면 제외(포즈 깨짐)
        min_vis: float = 0.5,  # visibility 컬럼이 있으면 활용 가능
        consec_sec: float = 0.25  # 연속 판정 시간(초)
):
    df = pd.read_csv(tilt_csv_path)

    if use_col not in df.columns:
        raise ValueError(f"{use_col} 컬럼이 없어. 사용 가능한 컬럼: {list(df.columns)}")

    tilt = df[use_col].to_numpy(dtype=float)

    # (선택) 변화량 컬럼이 있으면 포즈 깨짐 프레임 걸러내기
    if "abs_dtilt" in df.columns:
        abs_dtilt = df["abs_dtilt"].to_numpy(dtype=float)
    else:
        abs_dtilt = np.abs(np.diff(tilt, prepend=tilt[0]))

    # (선택) visibility 기반 필터 (네 CSV에는 v_i를 안 넣었지만, 원하면 추가 가능)
    # 여기서는 tilt csv에는 vis가 없다고 가정 → abs_dtilt와 NaN만으로 필터
    ok = np.isfinite(tilt) & (abs_dtilt <= max_abs_dtilt)

    tilt_run = tilt[ok]
    sigma = robust_sigma_mad(tilt_run)

    # sigma가 너무 작거나 NaN이면 안전장치(고정 여유폭)
    if not np.isfinite(sigma) or sigma < 1.0:
        sigma = 2.0  # 경험적으로 mediapipe tilt 흔들림 최소 여유

    delta_allow = band_half + k * sigma

    # 프레임별 에러 판정
    hard_err = (tilt >= hard_hi) | (tilt <= hard_lo)
    soft_err = np.abs(tilt - mu_ref) > delta_allow

    err_frame = hard_err | soft_err
    err_frame = err_frame & np.isfinite(tilt)

    # 연속 프레임 기준으로 “진짜 에러” 구간 만들기
    N_consec = max(1, int(round(consec_sec * fps)))

    segments = []
    in_seg = False
    start = 0
    count = 0

    for i, e in enumerate(err_frame):
        if e:
            if not in_seg:
                in_seg = True
                start = i
                count = 1
            else:
                count += 1
        else:
            if in_seg:
                if count >= N_consec:
                    end = i - 1
                    segments.append((start, end))
                in_seg = False
                count = 0

    # 끝까지 에러로 끝난 경우
    if in_seg and count >= N_consec:
        segments.append((start, len(err_frame) - 1))

    info = {
        "sigma_robust": float(sigma),
        "delta_allow": float(delta_allow),
        "N_consec": int(N_consec),
        "mu_ref": float(mu_ref),
        "band_half": float(band_half),
        "k": float(k),
        "hard_hi": float(hard_hi),
        "hard_lo": float(hard_lo),
        "max_abs_dtilt": float(max_abs_dtilt),
    }

    return df, err_frame, segments, info
#%%

fps = 60

df, err_frame, segments, info = find_error_segments_from_tilt_csv(OUT_PATH, fps)

print(info)
print("에러 구간(프레임):", segments)

# 초 단위로 보고 싶으면
segments_sec = [(round(s / fps, 2), round(e / fps, 2)) for (s, e) in segments]
print("에러 구간(초):", segments_sec)
