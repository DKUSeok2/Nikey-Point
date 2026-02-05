"""User service for business logic."""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from .model import User
from .schema import UserCreate


class UserService:
    """Service for user management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User registration data (user_name, height)
            
        Returns:
            Created user
        """
        # Create user
        user = User(
            user_name=user_data.user_name,
            height=user_data.height,
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user",
            )
