"""분석 서비스 - 3가지 지표 계산"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """3가지 러닝 지표 계산"""
    
    def calculate_metrics(
        self,
        frames: np.ndarray,
        xyzv: np.ndarray,
        pixel_heights: dict,
        fps: float
    ) -> dict:
        """
        3가지 지표 계산
        
        Args:
            frames: 프레임 번호 배열 (T,)
            xyzv: 키포인트 배열 (T, 33, 4)
            pixel_heights: 프레임별 픽셀 높이 {frame: height}
            fps: 영상 FPS
            
        Returns:
            {'overstride': 0.15, 'tilt': -82.5, 'vertical': 0.05}
        """
        return {
            'overstride': self._overstride(frames, xyzv, pixel_heights),
            'tilt': self._tilt(frames, xyzv, fps),
            'vertical': self._vertical(xyzv, pixel_heights)
        }
    
    def _overstride(self, frames, xyzv, pixel_heights) -> float:
        """과보폭 계산"""
        from ..pose_analysis.overstride.overstride import (
            xyzv_to_keypoints_df,
            height_dict_to_df,
            compute_overstride_numpy
        )
        from ..pose_analysis.overstride.abk import detect_contacts_abk
        
        df = xyzv_to_keypoints_df(frames, xyzv)
        height_df = height_dict_to_df(pixel_heights)
        contact_L, contact_R, _ = detect_contacts_abk(df)
        
        _, _, mean = compute_overstride_numpy(
            keypoints_df=df,
            contact_L=contact_L,
            contact_R=contact_R,
            height_df=height_df,
            point="toe"
        )
        
        return float(mean)
    
    def _tilt(self, frames, xyzv, fps) -> float:
        """상체 기울기 계산"""
        from ..pose_analysis.tilt.tilt_pipeline import run_tilt_analysis
        
        mean = run_tilt_analysis(
            frames=frames,
            xyzv=xyzv,
            fps=fps,
            generate_overlay_video=False
        )
        
        return float(mean)
    
    def _vertical(self, xyzv, pixel_heights) -> float:
        """수직 진동 계산"""
        from ..pose_analysis.vertical.com_vertical import calculate_vertical_oscillation
        
        mean = calculate_vertical_oscillation(xyzv, pixel_heights)
        
        return float(mean)
