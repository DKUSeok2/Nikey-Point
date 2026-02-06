"""Generate video with keypoints overlay."""
import cv2
import numpy as np
from pathlib import Path
from mediapipe import solutions as mp_solutions
import logging

logger = logging.getLogger(__name__)

# MediaPipe drawing utils
mp_drawing = mp_solutions.drawing_utils
mp_drawing_styles = mp_solutions.drawing_styles
mp_pose = mp_solutions.pose


def generate_keypoint_video(
    video_path: str,
    output_path: str,
    frames: np.ndarray,
    xyzv: np.ndarray,
) -> str:
    """
    Generate video with keypoints drawn on each frame.
    
    Args:
        video_path: Path to original video
        output_path: Path to save output video
        frames: Frame numbers array
        xyzv: Keypoints array (T, L, 4) - [x_px, y_px, z, v]
        
    Returns:
        Path to generated video
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Detect rotation
    rotation = _get_video_rotation(video_path)
    
    # Adjust dimensions if rotated
    if rotation in [90, 270]:
        frame_width, frame_height = frame_height, frame_width
    
    # Create output directory
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    frame_idx = 0
    keypoint_idx = 0
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Rotate frame if needed
            if rotation != 0:
                frame = _rotate_frame(frame, rotation)
            
            # Check if this frame has keypoints
            if keypoint_idx < len(frames) and frame_idx == frames[keypoint_idx]:
                # Get keypoints for this frame
                keypoints = xyzv[keypoint_idx]
                
                # Draw keypoints on frame
                frame = _draw_keypoints(frame, keypoints)
                
                keypoint_idx += 1
            
            # Write frame to output
            out.write(frame)
            frame_idx += 1
            
    finally:
        cap.release()
        out.release()
    
    logger.info(f"Keypoint video generated: {output_path}")
    return output_path


def _get_video_rotation(video_path: str) -> int:
    """Get video rotation angle from metadata."""
    import subprocess
    import json
    
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    rotation = stream.get('tags', {}).get('rotate', '0')
                    rotation_int = int(rotation)
                    
                    if rotation_int == 0:
                        logger.info("No rotation metadata, assuming 90° (iPhone portrait)")
                        return 90
                    
                    return rotation_int
    except Exception as e:
        logger.error(f"Failed to get video rotation: {e}")
    
    logger.info("Defaulting to 90° rotation")
    return 90


def _rotate_frame(frame: np.ndarray, rotation: int) -> np.ndarray:
    """Rotate frame based on metadata rotation."""
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame


def _draw_keypoints(frame: np.ndarray, keypoints: np.ndarray) -> np.ndarray:
    """
    Draw keypoints on frame using MediaPipe drawing utilities.
    
    Args:
        frame: Input frame
        keypoints: Keypoints array (L, 4) - [x_px, y_px, z, v]
        
    Returns:
        Frame with keypoints drawn
    """
    height, width = frame.shape[:2]
    
    # Create landmark list for MediaPipe drawing
    from mediapipe.framework.formats import landmark_pb2
    
    pose_landmarks = landmark_pb2.NormalizedLandmarkList()
    
    for i in range(min(33, len(keypoints))):  # MediaPipe has 33 landmarks
        x_px, y_px, z, visibility = keypoints[i]
        
        # Skip if NaN
        if np.isnan(x_px) or np.isnan(y_px):
            # Add placeholder landmark
            landmark = pose_landmarks.landmark.add()
            landmark.x = 0
            landmark.y = 0
            landmark.z = 0
            landmark.visibility = 0
            continue
        
        # Convert pixel coordinates back to normalized
        landmark = pose_landmarks.landmark.add()
        landmark.x = float(x_px / width)
        landmark.y = float(y_px / height)
        landmark.z = float(z) if not np.isnan(z) else 0
        landmark.visibility = float(visibility) if not np.isnan(visibility) else 0
    
    # Draw landmarks on frame
    mp_drawing.draw_landmarks(
        frame,
        pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
    )
    
    return frame
