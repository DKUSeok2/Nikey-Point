"""Dependency injection container for video module."""
from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from .service import VideoService
from .storage import VideoStorage


class VideoContainer(containers.DeclarativeContainer):
    """DI container for video module."""
    
    db = providers.Dependency(instance_of=Session)
    
    storage = providers.Singleton(VideoStorage)
    
    video_service = providers.Factory(
        VideoService,
        db=db,
        storage=storage,
    )
