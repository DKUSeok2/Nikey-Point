"""Video API routes."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from .schema import VideoUploadResponse, VideoStatusResponse, VideoResponse
from .service import VideoService

router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    user_id: str = Form(..., description="User ID"),
    file: UploadFile = File(..., description="Video file"),
    db: Session = Depends(get_db),
):
    """
    Upload a running video for analysis.
    
    - **user_id**: ID of the user uploading the video
    - **file**: Video file (mp4, mov, avi)
    
    Maximum file size: 100MB
    
    The video will be processed asynchronously. Use the status endpoint to check progress.
    """
    service = VideoService(db)
    video = await service.upload_video(user_id, file)
    
    # Queue keypoint extraction task
    from ..workers.tasks import extract_keypoints_task
    extract_keypoints_task.delay(video.id)
    
    return VideoUploadResponse(
        video_id=video.id,
        status=video.status,
        message="Video uploaded successfully. Processing started.",
    )


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(
    video_id: str,
    db: Session = Depends(get_db),
):
    """
    Get video processing status.
    
    - **video_id**: ID of the video
    
    Status values:
    - `uploaded`: Video uploaded, waiting for processing
    - `processing`: Currently extracting keypoints
    - `completed`: Processing completed successfully
    - `failed`: Processing failed (check error_message)
    """
    service = VideoService(db)
    video = service.get_video_by_id(video_id)
    
    if not video:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoStatusResponse(
        video_id=video.id,
        status=video.status,
        uploaded_at=video.uploaded_at,
        processed_at=video.processed_at,
        error_message=video.error_message,
    )


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: str,
    db: Session = Depends(get_db),
):
    """Get full video information."""
    service = VideoService(db)
    video = service.get_video_by_id(video_id)
    
    if not video:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video


@router.get("/user/{user_id}/videos", response_model=list[VideoResponse])
def get_user_videos(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get all videos for a user."""
    service = VideoService(db)
    videos = service.get_user_videos(user_id, limit)
    return videos


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: str,
    user_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Delete a video."""
    service = VideoService(db)
    service.delete_video(video_id, user_id)
    return None
