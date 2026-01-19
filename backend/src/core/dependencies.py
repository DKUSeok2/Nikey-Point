"""Common dependencies for FastAPI routes."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db

# Type alias for database session dependency
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user_id(user_id: str | None = None) -> str:
    """
    Get current user ID (simplified for Phase 1).
    
    In Phase 2, this will be replaced with JWT token validation.
    For now, we just accept a user_id parameter.
    
    Args:
        user_id: User ID from request
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If user_id is not provided
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID required",
        )
    return user_id


# Type alias for current user dependency
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
