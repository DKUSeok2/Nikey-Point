/// Landmark point (x, y, z, visibility)
class LandmarkPoint {
  final double x;
  final double y;
  final double z;
  final double visibility;

  LandmarkPoint({
    required this.x,
    required this.y,
    required this.z,
    required this.visibility,
  });

  factory LandmarkPoint.fromJson(Map<String, dynamic> json) {
    return LandmarkPoint(
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
      z: (json['z'] as num).toDouble(),
      visibility: (json['visibility'] as num).toDouble(),
    );
  }
}

/// Keypoint frame (single frame with all landmarks)
class KeypointFrame {
  final int frameNumber;
  final double timestamp;
  final Map<String, LandmarkPoint> landmarks;
  final double confidence;

  KeypointFrame({
    required this.frameNumber,
    required this.timestamp,
    required this.landmarks,
    required this.confidence,
  });

  factory KeypointFrame.fromJson(Map<String, dynamic> json) {
    final landmarksJson = json['landmarks'] as Map<String, dynamic>;
    final landmarks = <String, LandmarkPoint>{};
    
    landmarksJson.forEach((key, value) {
      landmarks[key] = LandmarkPoint.fromJson(value as Map<String, dynamic>);
    });

    return KeypointFrame(
      frameNumber: json['frame_number'] as int,
      timestamp: (json['timestamp'] as num).toDouble(),
      landmarks: landmarks,
      confidence: (json['confidence'] as num).toDouble(),
    );
  }
}

/// Keypoint response (all frames)
class KeypointResponse {
  final String videoId;
  final int frameCount;
  final List<KeypointFrame> keypoints;

  KeypointResponse({
    required this.videoId,
    required this.frameCount,
    required this.keypoints,
  });

  factory KeypointResponse.fromJson(Map<String, dynamic> json) {
    final keypointsJson = json['keypoints'] as List<dynamic>;
    final keypoints = keypointsJson
        .map((k) => KeypointFrame.fromJson(k as Map<String, dynamic>))
        .toList();

    return KeypointResponse(
      videoId: json['video_id'] as String,
      frameCount: json['frame_count'] as int,
      keypoints: keypoints,
    );
  }
}
