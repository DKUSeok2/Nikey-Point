from __future__ import annotations

import argparse
import glob
import os
from typing import List

import pandas as pd
import cv2
import numpy as np

from .overlay import make_overlay, OverlayConfig
from .abk import detect_contacts_abk
from .overstride import build_contact_overstride_table

def parse_args():
    p = argparse.ArgumentParser(description="Generate overstride overlay videos using ABK contacts.")
    p.add_argument("--video_dir", required=True, help="Folder containing *.mp4 and *_keypoints.csv")
    p.add_argument("--pattern", default="pro*.mp4", help="Video glob pattern (default: pro*.mp4)")
    p.add_argument("--out_dir", default="", help="Output folder (default: same as video_dir)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing overlay mp4s")

    p.add_argument("--eps", type=float, default=0.003)
    p.add_argument("--k_tol", type=int, default=1)
    p.add_argument("--cooldown", type=int, default=8)
    p.add_argument("--no_debug", action="store_true", help="Disable debug text overlay")
    p.add_argument("--point", choices=["toe", "heel", "ankle"], default="toe")

    return p.parse_args()


def main():
    args = parse_args()
    video_dir = args.video_dir
    out_dir = args.out_dir or video_dir

    cfg = OverlayConfig(
        eps=args.eps,
        k_tol=args.k_tol,
        cooldown=args.cooldown,
        show_debug_text=(not args.no_debug),
        point=args.point,
        overwrite=args.overwrite,
    )

    os.makedirs(out_dir, exist_ok=True)

    video_paths = sorted(glob.glob(os.path.join(video_dir, args.pattern)))
    summaries: List[dict] = []
    all_tables: list[pd.DataFrame] = []


    for vp in video_paths:
        base = os.path.splitext(os.path.basename(vp))[0]
        csvp = os.path.join(video_dir, f"{base}_keypoints.csv")
        outp = os.path.join(out_dir, f"{base}_overstride.mp4")
        csv_outp = os.path.join(out_dir, f"{base}_overstride.csv")

        if not os.path.exists(csvp):
            print(f"[SKIP] no csv: {csvp}")
            summaries.append({"video": base, "status": "SKIP_NO_CSV", "out": outp})
            continue

        if (not cfg.overwrite) and os.path.exists(outp):
            print(f"[SKIP] exists: {outp}")
            summaries.append({"video": base, "status": "SKIPPED_EXISTS", "out": outp})
            continue

        try:
            print(f"\n[RUN] {base}")
            res = make_overlay(vp, csvp, outp, cfg=cfg)

            df_kp = pd.read_csv(csvp)

            '''
            video마다 overstride table csv 저장
            '''
            cap = cv2.VideoCapture(vp)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.release()

            contact_L, contact_R, _ = detect_contacts_abk(
                df_kp, eps=cfg.eps, k_tol=cfg.k_tol, cooldown=cfg.cooldown, return_debug=False
            )

            table = build_contact_overstride_table(
                df_kp,
                video_name=os.path.basename(vp),
                fps=float(fps),
                contact_L=contact_L,
                contact_R=contact_R,
                point=cfg.point,
                norm=None,
                direction="right",
                csv_out_path=csv_outp,
            )
            all_tables.append(table)

            res["csv"] = csv_outp

            '''
            이 위까지
            '''

            res["status"] = "CREATED"
            summaries.append(res)
            print(f"[OK] {outp} | L={res['L_contacts']} R={res['R_contacts']}")
        except Exception as e:
            print(f"[FAIL] {base}: {e}")
            summaries.append({"video": base, "status": f"FAIL: {e}", "out": outp})

    df = pd.DataFrame(summaries)
    print("\n=== SUMMARY ===")
    print(df)

    summary_path = os.path.join(out_dir, "overlay_make_summary.csv")
    df.to_csv(summary_path, index=False)
    print(f"[SAVED] {summary_path}")

    # ---- per-runner stats (mean/std) ----
    if len(all_tables) > 0:
        all_tbl = pd.concat(all_tables, ignore_index=True)
        if "overstride_dx" in all_tbl.columns and len(all_tbl) > 0:
            stats = (
                all_tbl.groupby("video")["overstride_dx"]
                .agg(n="count", mean="mean", std="std")
                .reset_index()
            )

            stats_path = os.path.join(out_dir, "overstride_stats_by_video.csv")
            stats.to_csv(stats_path, index=False)
            print(f"[SAVED] {stats_path}")



if __name__ == "__main__":
    main()
