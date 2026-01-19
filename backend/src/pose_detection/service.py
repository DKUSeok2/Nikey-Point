"""Pose detection service for business logic."""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .model import Keypoint
from .detector import MediaPipeDetector
from ..video.model import Video


class PoseDetectionService:
    """Service for pose detection and keypoint management."""
    
    def __init__(self, db: Session, detector: MediaPipeDetector | None = None):
        self.db = db
        self.detector = detector or MediaPipeDetector()
    
    def extract_keypoints(
        self,
        video_id: str,
        video_path: str,
        user_height: float | None = None,
    ) -> list[Keypoint]:
        """
        Extract keypoints from video and save to database.
        
        Args:
            video_id: Video ID
            video_path: Path to video file
            user_height: User height in cm
            
        Returns:
            List of created keypoint records
        """
        keypoints = []
        
        # Process video with MediaPipe
        for frame_data in self.detector.process_video(video_path, user_height):
            keypoint = Keypoint(
                video_id=video_id,
                frame_number=frame_data["frame_number"],
                timestamp=frame_data["timestamp"],
                landmarks=frame_data["landmarks"],
                confidence=frame_data["confidence"],
            )
            keypoints.append(keypoint)
        
        # Batch insert for performance
        if keypoints:
            self.db.bulk_save_objects(keypoints)
            self.db.commit()
        
        return keypoints
    
    def get_video_keypoints(self, video_id: str) -> list[Keypoint]:
        """
        Get all keypoints for a video.
        
        Args:
            video_id: Video ID
            
        Returns:
            List of keypoints ordered by frame number
        """
        return (
            self.db.query(Keypoint)
            .filter(Keypoint.video_id == video_id)
            .order_by(Keypoint.frame_number)
            .all()
        )
    
    def get_keypoint_by_frame(
        self,
        video_id: str,
        frame_number: int,
    ) -> Keypoint | None:
        """Get keypoint for a specific frame."""
        return (
            self.db.query(Keypoint)
            .filter(
                Keypoint.video_id == video_id,
                Keypoint.frame_number == frame_number,
            )
            .first()
        )
    
    def delete_video_keypoints(self, video_id: str) -> int:
        """
        Delete all keypoints for a video.
        
        Args:
            video_id: Video ID
            
        Returns:
            Number of deleted keypoints
        """
        count = (
            self.db.query(Keypoint)
            .filter(Keypoint.video_id == video_id)
            .delete()
        )
        self.db.commit()
        return count
