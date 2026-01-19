"""User database model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.orm import relationship

from ..core.database import Base


class User(Base):
    """User model for authentication and profile."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    
    # Physical information
    height = Column(Float, nullable=False)  # cm
    weight = Column(Float, nullable=True)  # kg
    age = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
