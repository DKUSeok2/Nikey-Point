"""Video schemas for API requests and responses."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    """Video processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStep(str, Enum):
    """Video processing step."""
    EXTRACTING_KEYPOINTS = "extracting_keypoints"
    EXTRACTING_HEIGHT = "extracting_height"
    CALCULATING_METRICS = "calculating_metrics"
    GENERATING_FEEDBACK = "generating_feedback"
    COMPLETED = "completed"


class VideoUploadResponse(BaseModel):
    """Response for video upload."""
    video_id: str
    status: VideoStatus
    message: str = "Video uploaded successfully"
    
    class Config:
        from_attributes = True


class VideoStatusResponse(BaseModel):
    """Response for video status check."""
    video_id: str
    status: VideoStatus
    processing_step: str | None = None
    uploaded_at: datetime
    processed_at: datetime | None = None
    error_message: str | None = None
    
    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    """Full video information response."""
    id: str
    user_id: str
    file_path: str
    file_size: int | None = None
    duration: float | None = None
    status: VideoStatus
    processing_step: str | None = None
    uploaded_at: datetime
    processed_at: datetime | None = None
    
    class Config:
        from_attributes = True
