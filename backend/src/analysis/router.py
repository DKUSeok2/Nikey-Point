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
        metrics: 3가지 지표 값
        created_at: 분석 생성 시간
    """
    result = db.query(UserData)\
        .filter(UserData.user_id == user_id)\
        .order_by(UserData.created_at.desc())\
        .first()
    
    if not result:
        raise HTTPException(404, "분석 결과가 없습니다")
    
    return {
        "id": result.id,
        "metrics": {
            "overstride": result.overstride_avg,
            "tilt": result.tilt_avg,
            "vertical": result.com_vertical_avg
        },
        "created_at": result.created_at,
        "completed_at": result.completed_at
    }


@router.get("/user/{user_id}/history")
def get_analysis_history(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    분석 결과 히스토리 조회
    
    - **user_id**: 사용자 ID
    - **limit**: 최대 조회 개수 (기본 10개)
    """
    results = db.query(UserData)\
        .filter(UserData.user_id == user_id)\
        .order_by(UserData.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "metrics": {
                "overstride": r.overstride_avg,
                "tilt": r.tilt_avg,
                "vertical": r.com_vertical_avg
            }
        }
        for r in results
    ]
