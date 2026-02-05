"""Celery tasks for background processing."""
import logging
from celery import Celery
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..video.service import VideoService
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
        
        # 2. Keypoint 추출 + 캐싱
        from ..pose_detection.extract_keypoints import PoseDetectionService
        from pathlib import Path
        import numpy as np
        
        pose_service = PoseDetectionService()
        frames, xyzv = pose_service.extract_keypoints_numpy(video_path=video.file_path)
        
        logger.info(f"Keypoint 추출 완료: {len(frames)} frames")
        
        # 3. Pixel heights 계산
        from ..pose_detection.extract_height import get_pixel_heights
        
        pixel_heights = get_pixel_heights(video.file_path)
        logger.info(f"Pixel heights 계산 완료")
        
        # 4. Keypoints 캐싱 (오버레이 생성용)
        import pickle
        
        cache_dir = Path("/app/storage/keypoints")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / f"{video_id}.npz"
        np.savez_compressed(
            cache_file,
            frames=frames,
            xyzv=xyzv,
            pixel_heights=np.array([pixel_heights.get(i, np.nan) for i in range(len(frames))])
        )
        
        # pixel_heights dict도 별도 저장 (overstride용)
        heights_dict_file = cache_dir / f"{video_id}_heights.pkl"
        with open(heights_dict_file, 'wb') as f:
            pickle.dump(pixel_heights, f)
        
        logger.info(f"Keypoints 캐싱 완료: {cache_file}")
        
        # 5. 3가지 지표 계산
        from ..analysis.service import AnalysisService
        
        service = AnalysisService()
        metrics = service.calculate_metrics(
            frames=frames,
            xyzv=xyzv,
            pixel_heights=pixel_heights,
            fps=30.0  # TODO: video에서 fps 가져오기
        )
        
        logger.info(f"지표 계산 완료: {metrics}")
        
        # 6. LLM 피드백 생성
        from ..feedback.service import FeedbackService
        from ..user.model import User
        
        user = db.query(User).filter(User.id == video.user_id).first()
        user_height = user.height if user else 170.0  # 기본값
        
        feedback_service = FeedbackService()
        llm_feedback = feedback_service.generate_feedback(
            overstride=metrics['overstride'],
            tilt=metrics['tilt'],
            vertical=metrics['vertical'],
            user_height=user_height
        )
        
        logger.info(f"LLM 피드백 생성 완료")
        
        # 7. 결과 저장 (피드백까지만)
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
            llm_feedback=llm_feedback,
            completed_at=datetime.utcnow()
        )
        
        db.add(result)
        video.status = "completed"
        db.commit()
        
        logger.info(f"✅ 분석 완료 (피드백): user_data_id={result.id}")
        
        # 8. 오버레이 백그라운드 실행 (캐시 경로 전달)
        logger.info(f"🎬 오버레이 백그라운드 실행 시작 (Tilt, Overstride)")
        
        # Tilt 오버레이
        create_tilt_overlay_task.apply_async(
            args=[result.id, video.file_path, str(cache_file)],
            countdown=1
        )
        
        # Overstride 오버레이
        create_overstride_overlay_task.apply_async(
            args=[result.id, video.file_path, str(cache_file)],
            countdown=2  # Tilt보다 1초 늦게 시작
        )
        
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
def create_tilt_overlay_task(user_data_id: str, video_path: str, keypoints_cache_path: str):
    """
    Tilt 오버레이 영상 생성 (백그라운드)
    
    Args:
        user_data_id: UserData ID
        video_path: 원본 영상 경로
        keypoints_cache_path: 캐싱된 keypoints 파일 경로 (.npz)
    """
    from ..core.database import SessionLocal
    from ..analysis.model import UserData
    from ..pose_analysis.tilt.tilt_analysis import (
        TiltAnalysisConfig,
        compute_tilt_from_numpy,
        detect_tilt_error_segments,
    )
    from ..pose_analysis.tilt.tilt_overlay import (
        make_overlay_video_from_numpy,
        TiltHardConfig
    )
    from pathlib import Path
    import numpy as np
    
    db = SessionLocal()
    
    try:
        logger.info(f"Tilt 오버레이 생성 시작: user_data_id={user_data_id}")
        
        # 1. UserData 조회
        user_data = db.query(UserData).filter(UserData.id == user_data_id).first()
        if not user_data:
            raise ValueError(f"UserData not found: {user_data_id}")
        
        # 2. 캐싱된 Keypoints 로드 (재추출 X)
        cache_path = Path(keypoints_cache_path)
        if not cache_path.exists():
            raise ValueError(f"Keypoints 캐시 파일이 없습니다: {cache_path}")
        
        cached_data = np.load(cache_path)
        frames = cached_data['frames']
        xyzv = cached_data['xyzv']
        heights_array = cached_data['pixel_heights']
        
        logger.info(f"✅ 캐싱된 Keypoints 로드 완료: {len(frames)} frames")
        
        # 3. Tilt 분석 (올바른 파이프라인)
        fps = 30  # TODO: 실제 FPS 가져오기
        cfg = TiltAnalysisConfig()
        
        # 3-1. Tilt DataFrame 계산
        tilt_df = compute_tilt_from_numpy(frames, xyzv, cfg)
        
        # 3-2. Tilt 각도 배열 추출
        tilt_deg = tilt_df["tilt_smooth"].to_numpy(dtype=float)
        
        # 3-3. Error segments 감지
        err_frame, segments, info = detect_tilt_error_segments(tilt_df, fps, cfg)
        
        logger.info(f"Tilt 에러 세그먼트 감지 완료: {len(segments)}개")
        
        # 4. Overlay 영상 생성
        overlay_filename = f"tilt_overlay_{user_data_id}.mp4"
        overlay_path = Path("/app/storage/overlays") / overlay_filename
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        
        overlay_cfg = TiltHardConfig(hard_hi=-72.0, hard_lo=-92.0)
        make_overlay_video_from_numpy(
            video_path=video_path,
            xyzv=xyzv,
            tilt_deg=tilt_deg,
            err_frame=err_frame,
            out_path=str(overlay_path),
            cfg=overlay_cfg
        )
        
        logger.info(f"Tilt 오버레이 생성 완료: {overlay_path}")
        
        # 5. DB 업데이트
        user_data.tilt_overlay_path = f"/storage/overlays/{overlay_filename}"
        db.commit()
        
        logger.info(f"✅ Tilt 오버레이 완료: user_data_id={user_data_id}")
        
        return {
            "status": "success",
            "user_data_id": user_data_id,
            "overlay_path": str(overlay_path)
        }
        
    except Exception as exc:
        logger.error(f"❌ Tilt 오버레이 실패: {exc}", exc_info=True)
        db.rollback()
        return {
            "status": "failed",
            "user_data_id": user_data_id,
            "error": str(exc)
        }
    finally:
        db.close()


@celery_app.task
def create_overstride_overlay_task(user_data_id: str, video_path: str, keypoints_cache_path: str):
    """
    Overstride 오버레이 영상 생성 (백그라운드)
    
    Args:
        user_data_id: UserData ID
        video_path: 원본 영상 경로
        keypoints_cache_path: 캐싱된 keypoints 파일 경로 (.npz)
    """
    from ..core.database import SessionLocal
    from ..analysis.model import UserData
    from ..pose_analysis.overstride.abk import detect_contacts_abk
    from ..pose_analysis.overstride.overstride import (
        xyzv_to_keypoints_df,
        compute_overstride_numpy,
        height_dict_to_df
    )
    from ..pose_analysis.overstride.overstride_overlay import (
        make_overstride_overlay_video_from_pipeline,
        OverstrideOverlayConfig
    )
    from pathlib import Path
    import numpy as np
    import pickle
    
    db = SessionLocal()
    
    try:
        logger.info(f"Overstride 오버레이 생성 시작: user_data_id={user_data_id}")
        
        # 1. UserData 조회
        user_data = db.query(UserData).filter(UserData.id == user_data_id).first()
        if not user_data:
            raise ValueError(f"UserData not found: {user_data_id}")
        
        # 2. 캐싱된 Keypoints 로드
        cache_path = Path(keypoints_cache_path)
        if not cache_path.exists():
            raise ValueError(f"Keypoints 캐시 파일이 없습니다: {cache_path}")
        
        cached_data = np.load(cache_path)
        frames = cached_data['frames']
        xyzv = cached_data['xyzv']
        
        # 3. Pixel heights dict 로드
        heights_dict_path = cache_path.parent / f"{cache_path.stem.replace('.npz', '')}_heights.pkl"
        if not heights_dict_path.exists():
            # fallback: array를 dict로 변환
            heights_array = cached_data['pixel_heights']
            pixel_heights = {int(frames[i]): float(heights_array[i]) 
                           if not np.isnan(heights_array[i]) else None
                           for i in range(len(frames))}
        else:
            with open(heights_dict_path, 'rb') as f:
                pixel_heights = pickle.load(f)
        
        logger.info(f"✅ 캐싱된 Keypoints 로드 완료: {len(frames)} frames")
        
        # 4. Contact detection
        keypoints_df = xyzv_to_keypoints_df(frames, xyzv)
        contact_L, contact_R, debug = detect_contacts_abk(keypoints_df)
        
        logger.info(f"Contact 감지 완료: L={contact_L.sum()}, R={contact_R.sum()}")
        
        # 5. Overstride 계산
        height_df = height_dict_to_df(pixel_heights)
        over_frames, over_values, mean_overstride = compute_overstride_numpy(
            keypoints_df=keypoints_df,
            contact_L=contact_L,
            contact_R=contact_R,
            height_df=height_df,
            frames=frames,
            point="toe"
        )
        
        logger.info(f"Overstride 계산 완료: {len(over_frames)}개 (평균: {mean_overstride:.4f})")
        
        # 6. Overlay 영상 생성
        overlay_filename = f"overstride_overlay_{user_data_id}.mp4"
        overlay_path = Path("/app/storage/overlays") / overlay_filename
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        
        cfg = OverstrideOverlayConfig(ratio_hi=0.18, ratio_lo=0.0)
        make_overstride_overlay_video_from_pipeline(
            video_path=video_path,
            xyzv=xyzv,
            frames=frames,
            contact_L=contact_L,
            contact_R=contact_R,
            over_frames=over_frames,
            over_values=over_values,
            out_path=str(overlay_path),
            cfg=cfg
        )
        
        logger.info(f"Overstride 오버레이 생성 완료: {overlay_path}")
        
        # 7. DB 업데이트
        user_data.overstride_overlay_path = f"/storage/overlays/{overlay_filename}"
        db.commit()
        
        logger.info(f"✅ Overstride 오버레이 완료: user_data_id={user_data_id}")
        
        return {
            "status": "success",
            "user_data_id": user_data_id,
            "overlay_path": str(overlay_path)
        }
        
    except Exception as exc:
        logger.error(f"❌ Overstride 오버레이 실패: {exc}", exc_info=True)
        db.rollback()
        return {
            "status": "failed",
            "user_data_id": user_data_id,
            "error": str(exc)
        }
    finally:
        db.close()


@celery_app.task
def health_check_task():
    """Health check task for Celery worker."""
    logger.info("Celery worker health check")
    return {"status": "healthy", "worker": "nikepoint"}
