"""분석 결과 조회 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from .model import UserData

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/user/{user_id}/latest")
def get_latest_result(user_id: str, db: Session = Depends(get_db)):
    """
    최신 분석 결과 조회
    
    - **user_id**: 사용자 ID
    
    Returns:
        - **metrics**: 3가지 지표 값 (overstride, tilt, vertical)
        - **llm_feedback**: AI가 생성한 러닝 피드백
        - **overlays**: 오버레이 영상 경로
            - overstride: 과보폭 오버레이 (null이면 생성 중)
            - tilt: 상체 기울기 오버레이 (null이면 생성 중)
            - vertical: 수직 진동 오버레이 (null이면 생성 중)
        - **created_at**: 분석 시작 시간
        - **completed_at**: 분석 완료 시간
        
    Note:
        오버레이는 피드백 완료 후 백그라운드에서 생성됩니다.
        처음 조회 시 null일 수 있으며, 30~60초 후 재조회하면 확인 가능합니다.
    """
    result = db.query(UserData)\
        .filter(UserData.user_id == user_id)\
        .order_by(UserData.created_at.desc())\
        .first()
    
    if not result:
        raise HTTPException(404, "분석 결과가 없습니다")
    
    import math
    
    # NaN 값을 None으로 변환 (JSON 호환)
    def safe_float(value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return value
    
    return {
        "id": result.id,
        "video_path": result.keypoint_video_path or result.original_video_path,  # Keypoint 영상 우선
        "original_video_path": result.original_video_path,
        "keypoint_video_path": result.keypoint_video_path,
        "metrics": {
            "overstride": safe_float(result.overstride_avg),
            "tilt": safe_float(result.tilt_avg),
            "vertical": safe_float(result.com_vertical_avg)
        },
        "llm_feedback": result.llm_feedback,
        "overlays": {
            "overstride": result.overstride_overlay_path,
            "tilt": result.tilt_overlay_path,
            "vertical": result.com_vertical_overlay_path
        },
        "created_at": result.created_at,
        "completed_at": result.completed_at
    }


@router.get("/history")
def get_all_history(
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """
    전체 분석 결과 히스토리 조회 (모든 사용자)
    
    - **limit**: 최대 조회 개수 (기본 30개)
    
    Returns:
        - **user_name**: 사용자 이름
        - **metrics**: 3가지 지표 값
        - **llm_feedback**: AI 피드백
        - **overlays**: 오버레이 영상 경로
        - **created_at**: 분석 시작 시간
    """
    import math
    
    def safe_float(value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return value
    
    results = db.query(UserData)\
        .order_by(UserData.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": r.id,
            "user_name": r.user.user_name if r.user else "사용자",
            "created_at": r.created_at,
            "video_path": r.keypoint_video_path or r.original_video_path,
            "original_video_path": r.original_video_path,
            "keypoint_video_path": r.keypoint_video_path,
            "metrics": {
                "overstride": safe_float(r.overstride_avg),
                "tilt": safe_float(r.tilt_avg),
                "vertical": safe_float(r.com_vertical_avg)
            },
            "llm_feedback": r.llm_feedback,
            "overlays": {
                "overstride": r.overstride_overlay_path,
                "tilt": r.tilt_overlay_path,
                "vertical": r.com_vertical_overlay_path
            }
        }
        for r in results
    ]


@router.get("/user/{user_id}/history")
def get_analysis_history(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 분석 결과 히스토리 조회
    
    - **user_id**: 사용자 ID
    - **limit**: 최대 조회 개수 (기본 10개)
    
    Returns:
        - **metrics**: 3가지 지표 값
        - **llm_feedback**: AI 피드백
        - **overlays**: 오버레이 영상 경로
        - **created_at**: 분석 시작 시간
    """
    import math
    
    def safe_float(value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return value
    
    results = db.query(UserData)\
        .filter(UserData.user_id == user_id)\
        .order_by(UserData.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": r.id,
            "user_name": r.user.user_name if r.user else "사용자",
            "created_at": r.created_at,
            "video_path": r.keypoint_video_path or r.original_video_path,
            "original_video_path": r.original_video_path,
            "keypoint_video_path": r.keypoint_video_path,
            "metrics": {
                "overstride": safe_float(r.overstride_avg),
                "tilt": safe_float(r.tilt_avg),
                "vertical": safe_float(r.com_vertical_avg)
            },
            "llm_feedback": r.llm_feedback,
            "overlays": {
                "overstride": r.overstride_overlay_path,
                "tilt": r.tilt_overlay_path,
                "vertical": r.com_vertical_overlay_path
            }
        }
        for r in results
    ]
