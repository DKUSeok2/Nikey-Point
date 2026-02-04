"""User data database model."""
import uuid
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class UserData(Base):
    """User data model for storing running analysis results."""
    
    __tablename__ = "user_datas"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Video paths
    original_video_path = Column(String, nullable=False)
    
    # Overstride analysis
    overstride_overlay_path = Column(String, nullable=True)
    overstride_avg = Column(Float, nullable=True)
    
    # COM (Center of Mass) vertical movement analysis
    com_vertical_overlay_path = Column(String, nullable=True)
    com_vertical_avg = Column(Float, nullable=True)
    
    # Body tilt analysis
    tilt_overlay_path = Column(String, nullable=True)
    tilt_avg = Column(Float, nullable=True)
    
    # LLM feedback
    llm_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="user_datas")
    
    def __repr__(self) -> str:
        return f"<UserData(id={self.id}, user_id={self.user_id})>"
