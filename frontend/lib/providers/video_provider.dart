import 'dart:io';
import 'package:flutter/foundation.dart';
import '../models/video_model.dart';
import '../models/keypoint_model.dart';
import '../services/api_service.dart';

enum UploadState {
  idle,
  uploading,
  processing,
  completed,
  error,
}

/// Video provider for managing video upload and processing
class VideoProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  UploadState _state = UploadState.idle;
  VideoModel? _currentVideo;
  KeypointResponse? _keypoints;
  String? _errorMessage;
  double _progress = 0.0;
  File? _videoFile;

  UploadState get state => _state;
  VideoModel? get currentVideo => _currentVideo;
  KeypointResponse? get keypoints => _keypoints;
  String? get errorMessage => _errorMessage;
  double get progress => _progress;
  File? get videoFile => _videoFile;

  /// Upload video and start processing
  Future<void> uploadVideo({
    required String userId,
    required File videoFile,
    required double height,
  }) async {
    try {
      _state = UploadState.uploading;
      _errorMessage = null;
      _progress = 0.0;
      _videoFile = videoFile; // Store video file
      notifyListeners();

      // Upload video
      _currentVideo = await _apiService.uploadVideo(
        userId: userId,
        videoFile: videoFile,
        height: height,
      );

      _progress = 0.3;
      _state = UploadState.processing;
      notifyListeners();

      // Poll for status
      await _pollVideoStatus(_currentVideo!.id);

    } catch (e) {
      _state = UploadState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  /// Poll video status until completed or failed
  Future<void> _pollVideoStatus(String videoId) async {
    const maxAttempts = 60; // 60 attempts × 2 seconds = 2 minutes max
    int attempts = 0;

    while (attempts < maxAttempts) {
      try {
        await Future.delayed(const Duration(seconds: 2));
        
        final status = await _apiService.getVideoStatus(videoId);
        _currentVideo = status;
        
        // Update progress
        _progress = 0.3 + (attempts / maxAttempts) * 0.4;
        notifyListeners();

        if (status.status == VideoStatus.completed) {
          _state = UploadState.completed;
          _progress = 1.0;
          
          // Load keypoints
          await loadKeypoints(videoId);
          notifyListeners();
          return;
        } else if (status.status == VideoStatus.failed) {
          _state = UploadState.error;
          _errorMessage = status.errorMessage ?? 'Processing failed';
          notifyListeners();
          return;
        }

        attempts++;
      } catch (e) {
        _state = UploadState.error;
        _errorMessage = 'Status check failed: $e';
        notifyListeners();
        return;
      }
    }

    // Timeout
    _state = UploadState.error;
    _errorMessage = 'Processing timeout';
    notifyListeners();
  }

  /// Load keypoints for completed video
  Future<void> loadKeypoints(String videoId) async {
    try {
      _keypoints = await _apiService.getKeypoints(videoId);
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load keypoints: $e';
      notifyListeners();
    }
  }

  /// Reset state
  void reset() {
    _state = UploadState.idle;
    _currentVideo = null;
    _keypoints = null;
    _errorMessage = null;
    _progress = 0.0;
    _videoFile = null;
    notifyListeners();
  }
}
