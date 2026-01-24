from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

import os
import cv2
import numpy as np
import pandas as pd

from .abk import detect_contacts_abk
from .overstride import midhip_xy, foot_xy


# Pose edges for drawing skeleton
POSE_EDGES = [
    (11, 12), (11, 23), (12, 24), (23, 24),
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
    (23, 25), (25, 27), (27, 29), (29, 31),
    (24, 26), (26, 28), (28, 30), (30, 32),
]


@dataclass
class OverlayConfig:
    eps: float = 0.003
    k_tol: int = 1
    cooldown: int = 8
    show_debug_text: bool = True
    point: str = "toe"  # "toe" / "heel" / "ankle"
    overwrite: bool = False


def make_overlay(
    video_path: str,
    csv_path: str,
    out_path: str,
    *,
    cfg: OverlayConfig = OverlayConfig(),
) -> dict:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    n = len(df)

    # contact + debug
    contact_L, contact_R, dbg = detect_contacts_abk(
        df, eps=cfg.eps, k_tol=cfg.k_tol, cooldown=cfg.cooldown, return_debug=cfg.show_debug_text
    )

    # overstride at contact frames only (raw dx: foot_x - midhip_x)
    hx, hy = midhip_xy(df)
    toeL_x, toeL_y = foot_xy(df, side="L", point=cfg.point)  # works for toe/heel/ankle
    toeR_x, toeR_y = foot_xy(df, side="R", point=cfg.point)

    over_L = np.full(n, np.nan, float)
    over_R = np.full(n, np.nan, float)
    over_L[contact_L] = toeL_x[contact_L] - hx[contact_L]
    over_R[contact_R] = toeR_x[contact_R] - hx[contact_R]

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if abs(vid_frames - n) > 3:
        print(f"[WARN] frame mismatch: video={vid_frames}, csv={n} ({os.path.basename(video_path)})")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    def norm_to_px(x, y):
        x = 0.0 if np.isnan(x) else float(np.clip(x, 0.0, 1.0))
        y = 0.0 if np.isnan(y) else float(np.clip(y, 0.0, 1.0))
        return int(x * W), int(y * H)

    def get_xy(t, i):
        return float(df.loc[t, f"x_{i}"]), float(df.loc[t, f"y_{i}"])

    # ---- auto scale (your logic)
    BASE_H = 720.0
    S = max(0.5, min(1.5, H / BASE_H))

    FS_TITLE = 0.55 * S
    FS_DEBUG = 0.40 * S
    FS_CONTACT = 0.50 * S
    FS_LABEL = 0.45 * S

    TH_TITLE = max(1, int(round(1 * S)))
    TH_DEBUG = max(1, int(round(1 * S)))
    TH_CONTACT = max(1, int(round(1 * S)))
    TH_LABEL = max(1, int(round(1 * S)))

    R_SMALL_PT = max(2, int(round(3 * S)))
    R_USED_PT = max(4, int(round(7 * S)))
    R_MIDHIP = max(6, int(round(10 * S)))
    TH_SKEL = max(1, int(round(2 * S)))
    TH_RING = max(1, int(round(3 * S)))

    HUD_X0, HUD_Y0 = 10, 10
    HUD_W = int(min(W * 0.95, 760 * S))
    HUD_H = int(105 * S)

    # Colors (BGR)
    C_BG = (0, 0, 0)
    C_TXT = (255, 255, 255)
    C_SKEL = (0, 200, 0)
    C_PT = (0, 255, 0)

    C_TOE = (0, 165, 255)
    C_HEEL = (255, 0, 255)
    C_KNEE = (0, 255, 255)
    C_HIP = (0, 0, 255)
    C_MID = (0, 0, 255)

    C_CONTACT_L = (0, 255, 255)
    C_CONTACT_R = (255, 255, 0)

    def draw_labeled_point(frame, t, idx, label, color, radius=None, text_offset=None):
        x, y = get_xy(t, idx)
        px, py = norm_to_px(x, y)
        rad = R_USED_PT if radius is None else radius
        if text_offset is None:
            text_offset = (int(10 * S), int(-10 * S))
        cv2.circle(frame, (px, py), rad, color, -1)
        cv2.putText(
            frame,
            label,
            (px + text_offset[0], py + text_offset[1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            FS_LABEL,
            color,
            TH_LABEL,
        )

    t = 0
    while True:
        ok, frame = cap.read()
        if not ok or t >= n:
            break

        # 1) skeleton
        for a, b in POSE_EDGES:
            xa, ya = get_xy(t, a)
            xb, yb = get_xy(t, b)
            cv2.line(frame, norm_to_px(xa, ya), norm_to_px(xb, yb), C_SKEL, TH_SKEL)

        # 2) all keypoints
        for i in range(33):
            x, y = get_xy(t, i)
            cv2.circle(frame, norm_to_px(x, y), R_SMALL_PT, C_PT, -1)

        # 3) highlight a few points + labels
        # (keep minimal labels; you can add more later)
        draw_labeled_point(frame, t, 31, "toeL(31)", C_TOE)
        draw_labeled_point(frame, t, 32, "toeR(32)", C_TOE)
        draw_labeled_point(frame, t, 23, "hipL(23)", C_HIP, radius=max(4, int(round(6 * S))))
        draw_labeled_point(frame, t, 24, "hipR(24)", C_HIP, radius=max(4, int(round(6 * S))))

        # 4) mid-hip
        mhx, mhy = norm_to_px(hx[t], hy[t])
        cv2.circle(frame, (mhx, mhy), R_MIDHIP, C_MID, -1)
        cv2.putText(
            frame,
            "mid-hip",
            (mhx + int(10 * S), mhy - int(10 * S)),
            cv2.FONT_HERSHEY_SIMPLEX,
            FS_LABEL,
            C_MID,
            TH_LABEL,
        )

        # 5) HUD
        cv2.rectangle(frame, (HUD_X0, HUD_Y0), (HUD_X0 + HUD_W, HUD_Y0 + HUD_H), C_BG, -1)
        cv2.putText(
            frame,
            f"frame: {t}/{n-1}",
            (HUD_X0 + 10, HUD_Y0 + int(35 * S)),
            cv2.FONT_HERSHEY_SIMPLEX,
            FS_TITLE,
            C_TXT,
            TH_TITLE,
        )

        # 6) debug text (ABK)
        if cfg.show_debug_text and dbg is not None:
            gL = int(dbg.green_L[t])
            gR = int(dbg.green_R[t])
            kdx = float(dbg.knee_dx[t])
            k0 = int(dbg.condK[t])
            aL = int(dbg.condA_L[t]); bL = int(dbg.condB_L[t])
            aR = int(dbg.condA_R[t]); bR = int(dbg.condB_R[t])

            cv2.putText(
                frame,
                f"green(L,R)={gL},{gR} | knee_dx={kdx:.3f} | K(localmin)={k0}",
                (HUD_X0 + 10, HUD_Y0 + int(65 * S)),
                cv2.FONT_HERSHEY_SIMPLEX,
                FS_DEBUG,
                (200, 200, 200),
                TH_DEBUG,
            )
            cv2.putText(
                frame,
                f"A,B (orig)  L:({aL},{bL})  R:({aR},{bR})   tol=k{cfg.k_tol}",
                (HUD_X0 + 10, HUD_Y0 + int(90 * S)),
                cv2.FONT_HERSHEY_SIMPLEX,
                FS_DEBUG,
                (200, 200, 200),
                TH_DEBUG,
            )

        # 7) contact 표시
        y_base = int(170 * S)
        if contact_L[t] or contact_R[t]:
            cv2.rectangle(frame, (10, y_base - int(35 * S)), (int(W * 0.98), y_base + int(80 * S)), C_BG, -1)

        if contact_L[t]:
            ptx, pty = norm_to_px(toeL_x[t], toeL_y[t])
            cv2.circle(frame, (ptx, pty), int(18 * S), C_CONTACT_L, TH_RING)
            cv2.putText(
                frame,
                f"CONTACT: LEFT   Overstride_dx = {over_L[t]:+.3f}",
                (20, y_base),
                cv2.FONT_HERSHEY_SIMPLEX,
                FS_CONTACT,
                C_CONTACT_L,
                TH_CONTACT,
            )
            y_base += int(35 * S)

        if contact_R[t]:
            ptx, pty = norm_to_px(toeR_x[t], toeR_y[t])
            cv2.circle(frame, (ptx, pty), int(18 * S), C_CONTACT_R, TH_RING)
            cv2.putText(
                frame,
                f"CONTACT: RIGHT  Overstride_dx = {over_R[t]:+.3f}",
                (20, y_base),
                cv2.FONT_HERSHEY_SIMPLEX,
                FS_CONTACT,
                C_CONTACT_R,
                TH_CONTACT,
            )

        out.write(frame)
        t += 1

    cap.release()
    out.release()

    return {
        "video": os.path.basename(video_path),
        "out": out_path,
        "N": n,
        "L_contacts": int(np.sum(contact_L)),
        "R_contacts": int(np.sum(contact_R)),
        "L_contact_frames": np.where(contact_L)[0].tolist(),
        "R_contact_frames": np.where(contact_R)[0].tolist(),
    }
