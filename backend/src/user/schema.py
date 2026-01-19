"""User schemas for API requests and responses."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    height: float = Field(..., gt=0, le=300, description="Height in cm")
    weight: float | None = Field(None, gt=0, le=500, description="Weight in kg")
    age: int | None = Field(None, gt=0, le=150)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    height: float
    weight: float | None
    age: int | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    """Schema for login response."""
    user_id: str
    email: str
    message: str = "Login successful"
