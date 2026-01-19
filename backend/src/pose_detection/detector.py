"""MediaPipe Pose detector wrapper."""
import cv2
import mediapipe as mp
from typing import Iterator
import numpy as np

from .settings import pose_settings


# MediaPipe landmark names (33 points)
LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index"
]


class MediaPipeDetector:
    """Wrapper for MediaPipe Pose detection."""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=pose_settings.model_complexity,
            min_detection_confidence=pose_settings.min_detection_confidence,
            min_tracking_confidence=pose_settings.min_tracking_confidence,
        )
    
    def _get_video_rotation(self, video_path: str) -> int:
        """
        Get video rotation angle from metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Rotation angle (0, 90, 180, 270)
        """
        import subprocess
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Try to get rotation using ffprobe
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        # Check for rotation tag
                        rotation = stream.get('tags', {}).get('rotate', '0')
                        rotation_int = int(rotation)
                        logger.info(f"Video rotation detected: {rotation_int}°")
                        
                        # If no rotation found, assume iPhone portrait (90°)
                        if rotation_int == 0:
                            logger.info("No rotation metadata found, assuming iPhone portrait (90°)")
                            return 90
                        
                        return rotation_int
        except Exception as e:
            logger.error(f"Failed to get video rotation: {e}")
        
        # Default: assume iPhone portrait orientation
        logger.info("Defaulting to 90° rotation (iPhone portrait)")
        return 90
    
    def _rotate_frame(self, frame: np.ndarray, rotation: int) -> np.ndarray:
        """
        Rotate frame based on metadata rotation.
        
        iPhone portrait videos need clockwise 90° rotation to display correctly.
        
        Args:
            frame: Input frame
            rotation: Rotation angle from metadata (0, 90, 180, 270)
            
        Returns:
            Rotated frame
        """
        if rotation == 90:
            # iPhone portrait: rotate clockwise 90° to correct
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == 270:
            # Rotate counter-clockwise to correct
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
    
    def process_video(self, video_path: str, user_height: float | None = None) -> Iterator[dict]:
        """
        Process video and extract keypoints from each frame.
        
        Args:
            video_path: Path to video file
            user_height: User height in cm (for normalization)
            
        Yields:
            Dictionary with frame_number, timestamp, landmarks, confidence
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        # Get video rotation
        rotation = self._get_video_rotation(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = 0
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames if needed
                if frame_number % pose_settings.frame_skip != 0:
                    frame_number += 1
                    continue
                
                # Rotate frame if needed
                if rotation != 0:
                    frame = self._rotate_frame(frame, rotation)
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process with MediaPipe
                results = self.pose.process(frame_rgb)
                
                if results.pose_landmarks:
                    # Extract landmarks
                    landmarks = self._extract_landmarks(
                        results.pose_landmarks,
                        user_height,
                    )
                    
                    # Calculate average confidence
                    confidences = [lm["visibility"] for lm in landmarks.values()]
                    avg_confidence = sum(confidences) / len(confidences)
                    
                    yield {
                        "frame_number": frame_number,
                        "timestamp": frame_number / fps if fps > 0 else 0,
                        "landmarks": landmarks,
                        "confidence": avg_confidence,
                    }
                
                frame_number += 1
        
        finally:
            cap.release()
            self.pose.close()
    
    def _extract_landmarks(
        self,
        pose_landmarks,
        user_height: float | None = None,
    ) -> dict[str, dict[str, float]]:
        """
        Extract and normalize landmarks.
        
        Args:
            pose_landmarks: MediaPipe pose landmarks
            user_height: User height for normalization
            
        Returns:
            Dictionary mapping landmark name to {x, y, z, visibility}
        """
        landmarks = {}
        
        for idx, landmark in enumerate(pose_landmarks.landmark):
            if idx < len(LANDMARK_NAMES):
                landmarks[LANDMARK_NAMES[idx]] = {
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility,
                }
        
        # Normalize by height if provided
        if user_height:
            landmarks = self._normalize_by_height(landmarks, user_height)
        
        return landmarks
    
    def _normalize_by_height(
        self,
        landmarks: dict[str, dict[str, float]],
        user_height: float,
    ) -> dict[str, dict[str, float]]:
        """
        Normalize landmarks based on user height.
        
        This helps compare poses across different body sizes.
        
        Args:
            landmarks: Raw landmarks
            user_height: User height in cm
            
        Returns:
            Normalized landmarks
        """
        # Calculate body height in the frame (hip to ankle distance)
        if "left_hip" in landmarks and "left_ankle" in landmarks:
            hip = landmarks["left_hip"]
            ankle = landmarks["left_ankle"]
            
            # Calculate vertical distance
            frame_height = abs(hip["y"] - ankle["y"])
            
            if frame_height > 0:
                # Scale factor (approximate body height proportion)
                # Hip to ankle is roughly 50% of total height
                scale_factor = user_height * 0.5 / (frame_height * 100)
                
                # Apply scaling (optional - for future analysis)
                # For now, we keep original normalized coordinates
                pass
        
        return landmarks
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Get video metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with fps, frame_count, duration
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
        }
