"""User schemas for API requests and responses."""
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    user_name: str = Field(..., min_length=1, max_length=100)
    height: float = Field(..., gt=0, le=300, description="Height in cm")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    user_name: str
    height: float
    created_at: datetime
    
    class Config:
        from_attributes = True
