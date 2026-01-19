"""Pose detection API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from .schema import KeypointResponse, KeypointFrame, LandmarkPoint
from .service import PoseDetectionService

router = APIRouter(prefix="/api/pose", tags=["pose_detection"])


@router.get("/video/{video_id}/keypoints", response_model=KeypointResponse)
def get_video_keypoints(
    video_id: str,
    db: Session = Depends(get_db),
):
    """
    Get all extracted keypoints for a video.
    
    Returns keypoints for each processed frame with 33 body landmarks.
    Each landmark contains x, y, z coordinates and visibility score.
    """
    service = PoseDetectionService(db)
    keypoints = service.get_video_keypoints(video_id)
    
    if not keypoints:
        raise HTTPException(
            status_code=404,
            detail="No keypoints found for this video. Processing may not be complete.",
        )
    
    # Convert to response format
    keypoint_frames = []
    for kp in keypoints:
        # Convert landmarks dict to LandmarkPoint objects
        landmarks_dict = {
            name: LandmarkPoint(**coords)
            for name, coords in kp.landmarks.items()
        }
        
        keypoint_frames.append(
            KeypointFrame(
                frame_number=kp.frame_number,
                timestamp=kp.timestamp,
                landmarks=landmarks_dict,
                confidence=kp.confidence or 0.0,
            )
        )
    
    return KeypointResponse(
        video_id=video_id,
        frame_count=len(keypoint_frames),
        keypoints=keypoint_frames,
    )


@router.get("/video/{video_id}/frame/{frame_number}")
def get_frame_keypoint(
    video_id: str,
    frame_number: int,
    db: Session = Depends(get_db),
):
    """Get keypoint for a specific frame."""
    service = PoseDetectionService(db)
    keypoint = service.get_keypoint_by_frame(video_id, frame_number)
    
    if not keypoint:
        raise HTTPException(
            status_code=404,
            detail=f"Keypoint not found for frame {frame_number}",
        )
    
    return keypoint
