"""Video database model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..core.database import Base


class Video(Base):
    """Video model for uploaded running videos."""
    
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # File information
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    duration = Column(Float, nullable=True)  # seconds
    
    # Processing status
    status = Column(
        String,
        default="uploaded",
        nullable=False,
    )  # uploaded, processing, completed, failed
    
    error_message = Column(String, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    keypoints = relationship(
        "Keypoint",
        back_populates="video",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Video(id={self.id}, user_id={self.user_id}, status={self.status})>"
