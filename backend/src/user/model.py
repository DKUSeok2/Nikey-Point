"""User database model."""
import uuid
from sqlalchemy import Column, String, Float, DateTime, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class User(Base):
    """User model for basic information."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = Column(String, nullable=False, index=True)
    height = Column(Float, nullable=False)  # cm
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, user_name={self.user_name})>"
