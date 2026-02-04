"""Celery tasks for background processing."""
import logging
from celery import Celery
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..video.service import VideoService
from ..pose_detection.service import PoseDetectionService
from ..user.model import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "nikepoint",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
)


@celery_app.task(bind=True, max_retries=3)
def extract_keypoints_task(self, video_id: str):
    """
    Background task to extract keypoints from video.
    
    Args:
        video_id: Video ID to process
        
    Returns:
        Dictionary with results
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Starting keypoint extraction for video {video_id}")
        
        # Get video and user information
        video_service = VideoService(db)
        video = video_service.get_video_by_id(video_id)
        
        if not video:
            logger.error(f"Video {video_id} not found")
            return {"status": "failed", "error": "Video not found"}
        
        # Update status to processing
        video_service.update_video_status(video_id, "processing")
        
        # Get user height
        user = db.query(User).filter(User.id == video.user_id).first()
        user_height = user.height if user else None
        
        # Extract keypoints
        pose_service = PoseDetectionService(db)
        keypoints = pose_service.extract_keypoints(
            video_id=video_id,
            video_path=video.file_path,
            user_height=user_height,
        )
        
        logger.info(f"Extracted {len(keypoints)} keypoints for video {video_id}")
        
        # Update status to completed
        video_service.update_video_status(video_id, "completed")
        
        return {
            "status": "completed",
            "video_id": video_id,
            "keypoint_count": len(keypoints),
        }
    
    except Exception as exc:
        logger.error(f"Failed to process video {video_id}: {str(exc)}")
        
        # Update status to failed
        try:
            video_service = VideoService(db)
            video_service.update_video_status(
                video_id,
                "failed",
                error_message=str(exc),
            )
        except Exception:
            pass
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)  # Retry after 1 minute
        
        return {
            "status": "failed",
            "video_id": video_id,
            "error": str(exc),
        }
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_videos_task(days: int = 30):
    """
    Cleanup videos older than N days (future implementation).
    
    Args:
        days: Number of days to keep videos
    """
    logger.info(f"Cleanup task started (keeping videos from last {days} days)")
    # TODO: Implement cleanup logic in Phase 2
    return {"status": "not_implemented"}


@celery_app.task
def analyze_video_task(video_id: str):
    """
    영상 분석 Task - Keypoint 추출 + 3가지 지표 계산
    
    Args:
        video_id: Video ID to analyze
        
    Returns:
        Dictionary with analysis results
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(f"분석 시작: video_id={video_id}")
        
        # 1. Video 조회
        from ..video.model import Video
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            logger.error(f"Video not found: {video_id}")
            return {"status": "failed", "error": "Video not found"}
        
        video.status = "processing"
        db.commit()
        
        # 2. Keypoint 추출 (메모리에서만)
        from ..pose_detection.extract_keypoints import PoseDetectionService
        
        pose_service = PoseDetectionService()
        frames, xyzv = pose_service.extract_keypoints_numpy(video_path=video.file_path)
        
        logger.info(f"Keypoint 추출 완료: {len(frames)} frames")
        
        # 3. Pixel heights 계산
        from ..pose_detection.extract_height import get_pixel_heights
        
        pixel_heights = get_pixel_heights(video.file_path)
        logger.info(f"Pixel heights 계산 완료")
        
        # 4. 3가지 지표 계산
        from ..analysis.service import AnalysisService
        
        service = AnalysisService()
        metrics = service.calculate_metrics(
            frames=frames,
            xyzv=xyzv,
            pixel_heights=pixel_heights,
            fps=30.0  # TODO: video에서 fps 가져오기
        )
        
        logger.info(f"지표 계산 완료: {metrics}")
        
        # 5. 결과 저장
        from ..analysis.model import UserData
        from datetime import datetime
        
        result = UserData(
            user_id=video.user_id,
            original_video_path=video.file_path,
            overstride_avg=metrics['overstride'],
            tilt_avg=metrics['tilt'],
            com_vertical_avg=metrics['vertical'],
            overstride_overlay_path=None,
            tilt_overlay_path=None,
            com_vertical_overlay_path=None,
            llm_feedback=None,
            completed_at=datetime.utcnow()
        )
        
        db.add(result)
        video.status = "completed"
        db.commit()
        
        logger.info(f"✅ 분석 완료: user_data_id={result.id}")
        
        return {
            "status": "success",
            "user_data_id": result.id,
            "metrics": metrics
        }
        
    except Exception as exc:
        logger.error(f"❌ 분석 실패: {exc}", exc_info=True)
        db.rollback()
        
        try:
            video.status = "failed"
            video.error_message = str(exc)
            db.commit()
        except Exception:
            pass
        
        return {
            "status": "failed",
            "video_id": video_id,
            "error": str(exc)
        }
        
    finally:
        db.close()


@celery_app.task
def health_check_task():
    """Health check task for Celery worker."""
    logger.info("Celery worker health check")
    return {"status": "healthy", "worker": "nikepoint"}
