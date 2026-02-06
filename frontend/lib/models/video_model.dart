/// Video processing status
enum VideoStatus {
  uploaded,
  processing,
  completed,
  failed,
  unknown;

  static VideoStatus fromString(String status) {
    switch (status.toLowerCase()) {
      case 'uploaded':
        return VideoStatus.uploaded;
      case 'processing':
        return VideoStatus.processing;
      case 'completed':
        return VideoStatus.completed;
      case 'failed':
        return VideoStatus.failed;
      default:
        return VideoStatus.unknown;
    }
  }
}

/// Video processing step
enum ProcessingStep {
  extractingKeypoints,
  extractingHeight,
  calculatingMetrics,
  generatingFeedback,
  completed,
  unknown;

  static ProcessingStep fromString(String? step) {
    if (step == null) return ProcessingStep.unknown;
    switch (step.toLowerCase()) {
      case 'extracting_keypoints':
        return ProcessingStep.extractingKeypoints;
      case 'extracting_height':
        return ProcessingStep.extractingHeight;
      case 'calculating_metrics':
        return ProcessingStep.calculatingMetrics;
      case 'generating_feedback':
        return ProcessingStep.generatingFeedback;
      case 'completed':
        return ProcessingStep.completed;
      default:
        return ProcessingStep.unknown;
    }
  }
}

/// Video model
class VideoModel {
  final String id;
  final String userId;
  final VideoStatus status;
  final ProcessingStep? processingStep;
  final DateTime uploadedAt;
  final DateTime? processedAt;
  final String? errorMessage;

  VideoModel({
    required this.id,
    required this.userId,
    required this.status,
    this.processingStep,
    required this.uploadedAt,
    this.processedAt,
    this.errorMessage,
  });

  factory VideoModel.fromJson(Map<String, dynamic> json) {
    print('🔍 VideoModel.fromJson: processing_step = ${json['processing_step']}');
    return VideoModel(
      id: json['video_id'] ?? json['id'],
      userId: json['user_id'] ?? '',
      status: VideoStatus.fromString(json['status'] as String),
      processingStep: ProcessingStep.fromString(json['processing_step'] as String?),
      uploadedAt: DateTime.parse(json['uploaded_at'] as String? ?? DateTime.now().toIso8601String()),
      processedAt: json['processed_at'] != null
          ? DateTime.parse(json['processed_at'] as String)
          : null,
      errorMessage: json['error_message'] as String?,
    );
  }
}
