"""Schemas for pose detection API."""
from pydantic import BaseModel


class LandmarkPoint(BaseModel):
    """Single landmark point (x, y, z, visibility)."""
    x: float
    y: float
    z: float
    visibility: float


class KeypointFrame(BaseModel):
    """Keypoints for a single frame."""
    frame_number: int
    timestamp: float
    landmarks: dict[str, LandmarkPoint]
    confidence: float
    
    class Config:
        from_attributes = True


class KeypointResponse(BaseModel):
    """Response for keypoint retrieval."""
    video_id: str
    frame_count: int
    keypoints: list[KeypointFrame]
    
    class Config:
        from_attributes = True
