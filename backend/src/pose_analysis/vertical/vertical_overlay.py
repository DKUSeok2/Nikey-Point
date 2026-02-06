from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

import cv2
import numpy as np


# =========================
# Config
# =========================
@dataclass
class VerticalOverlayConfig:
    # CoM = mean(y of 11,12,23,24) when visible
    com_indices: Tuple[int, int, int, int] = (11, 12, 23, 24)
    vis_th: float = 0.5

    # Visual
    trail_len: int = 30          # 과거 궤적 길이(프레임)
    band_window: int = 30        # 최근 윈도우(amp/height)
    com_radius: int = 10

    # 정상 범위(색상 기준)
    good_lo: float = 0.01
    good_hi: float = 0.08

    # rotate: None | "ccw90" | "cw90"
    rotate_mode: Optional[str] = None

    # Draw skeleton (선택)
    draw_skeleton: bool = False


# 최소 스켈레톤 (원하면 확장)
POSE_EDGES = [
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 12),
    (11, 23), (12, 24),
    (23, 24),
    (23, 25), (25, 27),
    (24, 26), (26, 28),
]


# =========================
# Helpers
# =========================
def _compute_com_y_per_frame(
    xyzv: np.ndarray,
    cfg: VerticalOverlayConfig,
) -> np.ndarray:
    """
    xyzv: (T,33,4) [x_px,y_px,z,v]
    Returns com_y (T,) with NaNs if invalid
    """
    idx = np.array(cfg.com_indices, dtype=int)
    y = xyzv[:, idx, 1]   # (T,4)
    v = xyzv[:, idx, 3]   # (T,4)

    ok = np.all(np.isfinite(y), axis=1) & np.all(v >= cfg.vis_th, axis=1)
    com_y = np.full((xyzv.shape[0],), np.nan, dtype=float)
    com_y[ok] = np.mean(y[ok], axis=1)
    return com_y


def _interp_nans_1d(x: np.ndarray) -> np.ndarray:
    x = x.astype(float)
    mask = ~np.isfinite(x)
    if np.all(mask):
        return x
    if np.any(mask):
        x[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), x[~mask])
    return x


def _moving_average(x: np.ndarray, w: int) -> np.ndarray:
    if w <= 1:
        return x
    w = int(w)
    kernel = np.ones(w, dtype=float) / w
    return np.convolve(x, kernel, mode="same")


def _rotate_point(x: float, y: float, w: int, h: int, mode: Optional[str]) -> Tuple[float, float]:
    """
    프레임 자체를 회전하지 않고, 좌표만 보정하고 싶을 때 사용.
    """
    if mode is None:
        return x, y
    if mode == "ccw90":
        return y, w - x
    if mode == "cw90":
        return h - y, x
    raise ValueError(f"Invalid rotate_mode: {mode}")


def _get_height_for_frame(pixel_heights: Dict[int, float], frame_no: int) -> Optional[float]:
    hh = pixel_heights.get(int(frame_no))
    if hh is None:
        return None
    try:
        hh = float(hh)
    except Exception:
        return None
    return hh if hh > 0 else None


# =========================
# Main
# =========================
def make_vertical_overlay(
    *,
    video_path: str,
    frames: np.ndarray,
    xyzv: np.ndarray,
    pixel_heights: Dict[int, float],
    output_path: str,
    cfg: Optional[VerticalOverlayConfig] = None,
) -> Dict[str, float]:
    """
    무게중심(CoM) 상하 움직임을 오버레이한 영상 생성.
    HUD: ratio 한 줄만 표시(숫자가 절대 잘리지 않게 ratio를 앞에 둠)

    ✅ 정상 범위(0.01~0.08)면 오버레이는 초록색
    ❌ 범위 벗어나면 오버레이는 빨간색
    """
    cfg = cfg or VerticalOverlayConfig()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 항상 90도 회전 → width/height 교환
    w, h = h, w

    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (w, h),
    )

    # 1) CoM y 계산 + 보간/스무딩
    com_y = _compute_com_y_per_frame(xyzv, cfg)
    com_y_filled = _interp_nans_1d(com_y.copy())

    ma_w = min(15, len(com_y_filled))
    if ma_w % 2 == 0:
        ma_w -= 1
    if ma_w < 1:
        ma_w = 1

    com_y_smooth = _moving_average(com_y_filled, w=ma_w)

    # 2) 프레임별 vertical ratio (최근 band_window에서 amp/height)
    T = len(frames)
    ratio = np.zeros(T, dtype=float)
    amp_px = np.zeros(T, dtype=float)

    for t in range(T):
        s = max(0, t - cfg.band_window + 1)
        seg = com_y_smooth[s: t + 1]
        seg = seg[np.isfinite(seg)]
        if seg.size == 0:
            continue

        amp = float(np.max(seg) - np.min(seg))
        amp_px[t] = amp

        hh = _get_height_for_frame(pixel_heights, int(frames[t]))
        if hh is not None:
            ratio[t] = amp / hh

    valid_heights = [float(v) for v in pixel_heights.values() if v is not None and float(v) > 0]
    avg_height_px = float(np.mean(valid_heights)) if valid_heights else float("nan")

    # 3) Draw loop
    font_scale = h / 720 * 0.7   # 글자 작게
    thickness = max(1, int(h / 720 * 2))

    cx = w // 2

    def fit_text_1line_keep_prefix(prefix: str, suffix: str, max_text_w: int) -> str:
        """prefix는 유지, suffix만 줄임"""
        if max_text_w <= 20:
            return prefix

        full = prefix + suffix
        (tw, _), _ = cv2.getTextSize(full, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        if tw <= max_text_w:
            return full

        ell = "..."
        s2 = suffix
        while True:
            if len(s2) <= 0:
                return prefix + ell
            s2 = s2[:-1]
            cand = prefix + s2 + ell
            (tw2, _), _ = cv2.getTextSize(cand, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            if tw2 <= max_text_w:
                return cand

    t = 0
    while True:
        ret, frame = cap.read()
        if not ret or t >= T:
            break
        
        # 항상 90도 시계방향 회전 (iPhone portrait)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        r = float(ratio[t])

        # ✅ 정상/비정상 색상 결정
        is_good = (cfg.good_lo <= r <= cfg.good_hi)
        overlay_color = (0, 255, 0) if is_good else (0, 0, 255)  # green / red
        hud_border = overlay_color

        # =========================
        # Skeleton (선택)
        # =========================
        if cfg.draw_skeleton:
            for a, b in POSE_EDGES:
                x1, y1, _, v1 = xyzv[t, a]
                x2, y2, _, v2 = xyzv[t, b]
                if v1 < cfg.vis_th or v2 < cfg.vis_th:
                    continue
                if (not np.isfinite(x1)) or (not np.isfinite(y1)) or (not np.isfinite(x2)) or (not np.isfinite(y2)):
                    continue
                x1, y1 = _rotate_point(float(x1), float(y1), w, h, cfg.rotate_mode)
                x2, y2 = _rotate_point(float(x2), float(y2), w, h, cfg.rotate_mode)
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), overlay_color, 2)

        # =========================
        # CoM y + trail
        # =========================
        cy = float(com_y_smooth[t]) if np.isfinite(com_y_smooth[t]) else float("nan")
        if np.isfinite(cy):
            _, cy_draw = _rotate_point(0.0, cy, w, h, cfg.rotate_mode)
        else:
            cy_draw = float("nan")

        if np.isfinite(cy_draw):
            pts: List[Tuple[int, int]] = []
            for k in range(max(0, t - cfg.trail_len + 1), t + 1):
                yk = float(com_y_smooth[k])
                if not np.isfinite(yk):
                    continue
                _, yk_draw = _rotate_point(0.0, yk, w, h, cfg.rotate_mode)
                pts.append((cx, int(yk_draw)))

            # trail 색상도 정상/비정상에 맞춰 변경
            for i in range(1, len(pts)):
                cv2.line(frame, pts[i - 1], pts[i], overlay_color, 2)

            # 현재 CoM 점도 동일 색상
            cv2.circle(frame, (cx, int(cy_draw)), cfg.com_radius, overlay_color, -1)

        # =========================
        # HUD
        # =========================
        prefix = f"Ratio: {r:.3f}  "
        suffix = ""  # win 제거

        pad = 14
        max_box_w = int(w * 0.65)
        max_text_w = max_box_w - pad * 2

        text1 = fit_text_1line_keep_prefix(prefix, suffix, max_text_w)
        (tw1, th1), _ = cv2.getTextSize(text1, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)

        box_w = min(tw1 + pad * 2, max_box_w)
        box_h = th1 + pad * 2

        x0 = 20
        y0 = 20
        x0 = max(0, min(x0, w - box_w - 1))
        y0 = max(0, min(y0, h - box_h - 1))

        # 흰 박스
        cv2.rectangle(frame, (x0, y0), (x0 + box_w, y0 + box_h), (255, 255, 255), -1)
        # ✅ 박스 테두리를 정상/비정상 색상으로
        cv2.rectangle(frame, (x0, y0), (x0 + box_w, y0 + box_h), hud_border, 2)

        # 텍스트
        cv2.putText(
            frame,
            text1,
            (x0 + pad, y0 + pad + th1),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 0, 0),
            thickness,
        )

        out.write(frame)
        t += 1

    cap.release()
    out.release()

    metrics = {
        "mean_ratio": float(np.nanmean(ratio)) if ratio.size else 0.0,
        "mean_amp_px": float(np.nanmean(amp_px)) if amp_px.size else 0.0,
        "avg_height_px": float(avg_height_px) if np.isfinite(avg_height_px) else float("nan"),
    }
    return metrics
