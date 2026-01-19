"""Dependency injection container for user module."""
from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from .service import UserService


class UserContainer(containers.DeclarativeContainer):
    """DI container for user module."""
    
    db = providers.Dependency(instance_of=Session)
    
    user_service = providers.Factory(
        UserService,
        db=db,
    )
