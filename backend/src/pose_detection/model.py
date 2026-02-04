"""Keypoint database model."""
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.database import Base


class Keypoint(Base):
    """Keypoint model for storing MediaPipe pose landmarks."""
    
    __tablename__ = "keypoints"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), nullable=False, index=True)
    
    frame_number = Column(Integer, nullable=False, index=True)
    timestamp = Column(Float, nullable=False)  # seconds
    
    # MediaPipe landmarks (33 points × x,y,z,visibility)
    # Stored as JSONB for efficient querying
    landmarks = Column(JSONB, nullable=False)
    
    # Average confidence/visibility of all landmarks
    confidence = Column(Float, nullable=True)
    
    # Relationships
    video = relationship("Video", back_populates="keypoints")
    
    def __repr__(self) -> str:
        return f"<Keypoint(id={self.id}, video_id={self.video_id}, frame={self.frame_number})>"
