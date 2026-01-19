"""Video file storage management."""
import os
import uuid
from pathlib import Path
from typing import BinaryIO
from fastapi import HTTPException, status, UploadFile

from ..core.config import settings


class VideoStorage:
    """Handle video file storage operations."""
    
    def __init__(self):
        self.storage_path = Path(settings.STORAGE_PATH)
        self.max_size_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
        self.allowed_extensions = settings.ALLOWED_VIDEO_EXTENSIONS
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded video file.
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in self.allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file extension. Allowed: {', '.join(self.allowed_extensions)}",
                )
        
        # Check file size
        if file.size and file.size > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_VIDEO_SIZE_MB}MB",
            )
    
    def generate_filename(self, original_filename: str) -> str:
        """
        Generate unique filename for storage.
        
        Args:
            original_filename: Original uploaded filename
            
        Returns:
            Unique filename with UUID
        """
        ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"
    
    async def save(self, file: UploadFile) -> tuple[str, int]:
        """
        Save uploaded video file to storage.
        
        Args:
            file: Uploaded video file
            
        Returns:
            Tuple of (file_path, file_size)
            
        Raises:
            HTTPException: If save fails
        """
        self.validate_file(file)
        
        # Generate unique filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )
        
        filename = self.generate_filename(file.filename)
        file_path = self.storage_path / filename
        
        # Save file
        try:
            content = await file.read()
            file_size = len(content)
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            return str(file_path), file_size
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}",
            )
    
    def delete(self, file_path: str) -> None:
        """
        Delete video file from storage.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except Exception:
            # Log error but don't raise - file cleanup is best effort
            pass
    
    def get_video_duration(self, file_path: str) -> float | None:
        """
        Get video duration using OpenCV.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Duration in seconds, or None if unable to determine
        """
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            
            if fps > 0:
                return frame_count / fps
            return None
        except Exception:
            return None
