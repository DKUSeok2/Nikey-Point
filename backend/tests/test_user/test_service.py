"""Tests for user service."""
import pytest
from src.user.service import UserService
from src.user.schema import UserCreate, UserLogin


def test_create_user(db_session):
    """Test user creation."""
    service = UserService(db_session)
    
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        height=175.5,
    )
    
    user = service.create_user(user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.height == 175.5
    assert user.password_hash != "password123"  # Should be hashed


def test_create_duplicate_user(db_session):
    """Test that duplicate email raises error."""
    service = UserService(db_session)
    
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        height=175.5,
    )
    
    service.create_user(user_data)
    
    with pytest.raises(Exception):  # Should raise HTTPException
        service.create_user(user_data)


def test_authenticate_user(db_session):
    """Test user authentication."""
    service = UserService(db_session)
    
    # Create user
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        height=175.5,
    )
    service.create_user(user_data)
    
    # Authenticate
    login_data = UserLogin(
        email="test@example.com",
        password="password123",
    )
    
    user = service.authenticate_user(login_data)
    assert user.email == "test@example.com"


def test_authenticate_wrong_password(db_session):
    """Test authentication with wrong password."""
    service = UserService(db_session)
    
    # Create user
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        height=175.5,
    )
    service.create_user(user_data)
    
    # Try wrong password
    login_data = UserLogin(
        email="test@example.com",
        password="wrongpassword",
    )
    
    with pytest.raises(Exception):
        service.authenticate_user(login_data)
