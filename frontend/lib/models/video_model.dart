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

/// Video model
class VideoModel {
  final String id;
  final String userId;
  final VideoStatus status;
  final DateTime uploadedAt;
  final DateTime? processedAt;
  final String? errorMessage;

  VideoModel({
    required this.id,
    required this.userId,
    required this.status,
    required this.uploadedAt,
    this.processedAt,
    this.errorMessage,
  });

  factory VideoModel.fromJson(Map<String, dynamic> json) {
    return VideoModel(
      id: json['video_id'] ?? json['id'],
      userId: json['user_id'] ?? '',
      status: VideoStatus.fromString(json['status'] as String),
      uploadedAt: DateTime.parse(json['uploaded_at'] as String? ?? DateTime.now().toIso8601String()),
      processedAt: json['processed_at'] != null
          ? DateTime.parse(json['processed_at'] as String)
          : null,
      errorMessage: json['error_message'] as String?,
    );
  }
}
