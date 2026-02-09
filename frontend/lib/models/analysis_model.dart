/// Analysis metrics
class AnalysisMetrics {
  final double? overstride;
  final double? tilt;
  final double? vertical;

  AnalysisMetrics({
    this.overstride,
    this.tilt,
    this.vertical,
  });

  factory AnalysisMetrics.fromJson(Map<String, dynamic> json) {
    return AnalysisMetrics(
      overstride: json['overstride'] != null ? (json['overstride'] as num).toDouble() : null,
      tilt: json['tilt'] != null ? (json['tilt'] as num).toDouble() : null,
      vertical: json['vertical'] != null ? (json['vertical'] as num).toDouble() : null,
    );
  }
}

/// Overlay paths
class AnalysisOverlays {
  final String? overstride;
  final String? tilt;
  final String? vertical;

  AnalysisOverlays({
    this.overstride,
    this.tilt,
    this.vertical,
  });

  factory AnalysisOverlays.fromJson(Map<String, dynamic> json) {
    return AnalysisOverlays(
      overstride: json['overstride'] as String?,
      tilt: json['tilt'] as String?,
      vertical: json['vertical'] as String?,
    );
  }
}

/// Analysis result
class AnalysisResult {
  final String id;
  final String? userName;
  final String? videoPath;  // Keypoint video path (or original if keypoint not available)
  final String? originalVideoPath;
  final String? keypointVideoPath;
  final AnalysisMetrics metrics;
  final String? llmFeedback;
  final AnalysisOverlays overlays;
  final DateTime createdAt;
  final DateTime? completedAt;

  AnalysisResult({
    required this.id,
    this.userName,
    this.videoPath,
    this.originalVideoPath,
    this.keypointVideoPath,
    required this.metrics,
    this.llmFeedback,
    required this.overlays,
    required this.createdAt,
    this.completedAt,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      id: json['id'] as String,
      userName: json['user_name'] as String?,
      videoPath: json['video_path'] as String?,
      originalVideoPath: json['original_video_path'] as String?,
      keypointVideoPath: json['keypoint_video_path'] as String?,
      metrics: AnalysisMetrics.fromJson(json['metrics'] as Map<String, dynamic>),
      llmFeedback: json['llm_feedback'] as String?,
      overlays: AnalysisOverlays.fromJson(json['overlays'] as Map<String, dynamic>),
      createdAt: DateTime.parse(json['created_at'] as String),
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
    );
  }

  /// Get status text for overstride
  String get overstrideStatus {
    if (metrics.overstride == null) return '측정 불가';
    if (metrics.overstride! <= 0.18) return '정상';
    if (metrics.overstride! <= 0.25) return '주의';
    return '비정상';
  }

  /// Get status color for overstride
  bool get isOverstrideNormal => metrics.overstride != null && metrics.overstride! <= 0.18;

  /// Get status text for tilt
  String get tiltStatus {
    if (metrics.tilt == null) return '측정 불가';
    final absTilt = metrics.tilt!.abs();
    if (absTilt >= 72 && absTilt <= 92) return '정상';
    if (absTilt >= 65 && absTilt <= 100) return '주의';
    return '비정상';
  }

  /// Get status text for vertical
  String get verticalStatus {
    if (metrics.vertical == null) return '측정 불가';
    if (metrics.vertical! >= 0.01 && metrics.vertical! <= 0.08) return '정상';
    if (metrics.vertical! >= 0.005 && metrics.vertical! <= 0.10) return '주의';
    return '비정상';
  }
  
  /// Get status color for vertical
  bool get isVerticalNormal => metrics.vertical != null && metrics.vertical! >= 0.01 && metrics.vertical! <= 0.08;
}
