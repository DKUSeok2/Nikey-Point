"""Video service for business logic."""
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile

from .model import Video
from .storage import VideoStorage
from ..user.model import User


class VideoService:
    """Service for video management."""
    
    def __init__(self, db: Session, storage: VideoStorage | None = None):
        self.db = db
        self.storage = storage or VideoStorage()
    
    def get_video_by_id(self, video_id: str) -> Video | None:
        """Get video by ID."""
        return self.db.query(Video).filter(Video.id == video_id).first()
    
    def get_user_videos(self, user_id: str, limit: int = 50) -> list[Video]:
        """Get all videos for a user."""
        return (
            self.db.query(Video)
            .filter(Video.user_id == user_id)
            .order_by(Video.uploaded_at.desc())
            .limit(limit)
            .all()
        )
    
    async def upload_video(
        self,
        user_id: str,
        file: UploadFile,
    ) -> Video:
        """
        Upload and save video file.
        
        Args:
            user_id: ID of user uploading video
            file: Uploaded video file
            
        Returns:
            Created video record
            
        Raises:
            HTTPException: If upload fails or user doesn't exist
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Save file to storage
        file_path, file_size = await self.storage.save(file)
        
        # Get video duration
        duration = self.storage.get_video_duration(file_path)
        
        # Create video record
        video = Video(
            user_id=user_id,
            file_path=file_path,
            file_size=file_size,
            duration=duration,
            status="uploaded",
        )
        
        try:
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            return video
        except Exception as e:
            self.db.rollback()
            # Clean up file if DB insert fails
            self.storage.delete(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create video record: {str(e)}",
            )
    
    def update_video_status(
        self,
        video_id: str,
        status: str,
        error_message: str | None = None,
    ) -> Video:
        """
        Update video processing status.
        
        Args:
            video_id: Video ID
            status: New status
            error_message: Optional error message if failed
            
        Returns:
            Updated video
            
        Raises:
            HTTPException: If video not found
        """
        video = self.get_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )
        
        video.status = status
        video.error_message = error_message
        
        if status in ["completed", "failed"]:
            video.processed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(video)
        return video
    
    def delete_video(self, video_id: str, user_id: str) -> None:
        """
        Delete video and associated file.
        
        Args:
            video_id: Video ID
            user_id: User ID (for authorization)
            
        Raises:
            HTTPException: If video not found or unauthorized
        """
        video = self.get_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )
        
        if video.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this video",
            )
        
        # Delete file from storage
        self.storage.delete(video.file_path)
        
        # Delete from database
        self.db.delete(video)
        self.db.commit()
