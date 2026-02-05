"""User API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from .schema import UserCreate, UserResponse
from .service import UserService

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.
    
    - **user_name**: User name
    - **height**: Height in cm
    """
    service = UserService(db)
    user = service.create_user(user_data)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get user information by ID."""
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
