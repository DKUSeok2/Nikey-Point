"""
Tilt (upper-body posture) analysis package.

Public API:
- TiltAnalysisConfig
- compute_tilt_from_numpy
- detect_tilt_error_segments
- run_tilt_analysis
"""

from .tilt_analysis import (
    TiltAnalysisConfig,
    compute_tilt_from_numpy,
    detect_tilt_error_segments,
)

from .tilt_pipeline import run_tilt_analysis

__all__ = [
    "TiltAnalysisConfig",
    "compute_tilt_from_numpy",
    "detect_tilt_error_segments",
    "run_tilt_analysis",
]
