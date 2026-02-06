from pathlib import Path
from src.pose_detection.extract_keypoints import PoseDetectionService
from src.pose_detection.extract_height import get_pixel_heights
from src.pose_analysis.vertical.vertical_overlay import make_vertical_overlay, VerticalOverlayConfig


def main():
    video_path = "storage/videos/video.mp4"
    output_path = "storage/results/video_com_overlay.mp4"

    pose = PoseDetectionService()
    frames, xyzv = pose.extract_keypoints_numpy(video_path=video_path)

    pixel_heights = get_pixel_heights(video_path)

    cfg = VerticalOverlayConfig(
        band_window=30,
        trail_len=30,
        draw_skeleton=False,
    )

    make_vertical_overlay(
        video_path=video_path,
        frames=frames,
        xyzv=xyzv,
        pixel_heights=pixel_heights,
        output_path=output_path,
        cfg=cfg,
    )


if __name__ == "__main__":
    main()
