"""Dependency injection container for pose detection module."""
from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from .service import PoseDetectionService
from .detector import MediaPipeDetector


class PoseDetectionContainer(containers.DeclarativeContainer):
    """DI container for pose detection module."""
    
    db = providers.Dependency(instance_of=Session)
    
    detector = providers.Singleton(MediaPipeDetector)
    
    pose_detection_service = providers.Factory(
        PoseDetectionService,
        db=db,
        detector=detector,
    )
