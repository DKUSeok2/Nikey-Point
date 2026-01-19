"""MediaPipe Pose detection settings."""
from pydantic_settings import BaseSettings
from ..core.config import settings as global_settings


class PoseSettings(BaseSettings):
    """Settings for MediaPipe Pose detection."""
    
    model_complexity: int = global_settings.MEDIAPIPE_MODEL_COMPLEXITY
    min_detection_confidence: float = global_settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE
    min_tracking_confidence: float = global_settings.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
    
    # Processing settings
    target_fps: int = 30  # Process every N frames
    frame_skip: int = 1   # Process every N frames (1 = all frames)


# Global settings instance
pose_settings = PoseSettings()
