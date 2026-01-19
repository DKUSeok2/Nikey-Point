"""User API routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from .schema import UserCreate, UserLogin, UserResponse, UserLoginResponse
from .service import UserService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **password**: Minimum 6 characters
    - **height**: Height in cm (required)
    - **weight**: Weight in kg (optional)
    - **age**: Age (optional)
    """
    service = UserService(db)
    user = service.create_user(user_data)
    return user


@router.post("/login", response_model=UserLoginResponse)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Login user with email and password.
    
    - **email**: Registered email
    - **password**: User password
    
    Returns user_id for subsequent requests (Phase 1 simple auth).
    """
    service = UserService(db)
    user = service.authenticate_user(login_data)
    
    return UserLoginResponse(
        user_id=user.id,
        email=user.email,
    )


@router.get("/user/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get user information by ID."""
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
