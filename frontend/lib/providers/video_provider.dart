import 'dart:io';
import 'package:flutter/foundation.dart';
import '../models/video_model.dart';
import '../models/keypoint_model.dart';
import '../models/analysis_model.dart';
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
  AnalysisResult? _analysisResult;
  String? _errorMessage;
  double _progress = 0.0;
  File? _videoFile;
  String? _userId;
  String? _userName;

  UploadState get state => _state;
  VideoModel? get currentVideo => _currentVideo;
  KeypointResponse? get keypoints => _keypoints;
  AnalysisResult? get analysisResult => _analysisResult;
  String? get errorMessage => _errorMessage;
  double get progress => _progress;
  File? get videoFile => _videoFile;
  String? get userId => _userId;
  String? get userName => _userName;

  /// Set user name
  void setUserName(String name) {
    _userName = name;
    notifyListeners();
  }

  /// Set analysis result (for history navigation)
  void setAnalysisResult(AnalysisResult result) {
    _analysisResult = result;
    notifyListeners();
  }

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
      _videoFile = videoFile;
      _userId = userId;
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
          
          // Load keypoints and analysis result
          await loadKeypoints(videoId);
          if (_userId != null) {
            await loadAnalysisResult(_userId!);
          }
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

  /// Load analysis result for user
  Future<void> loadAnalysisResult(String userId) async {
    try {
      print('🔍 Loading analysis for user_id: $userId');
      _analysisResult = await _apiService.getLatestAnalysis(userId);
      print('✅ Analysis loaded: ${_analysisResult?.id}');
      print('📦 Overlays: overstride=${_analysisResult?.overlays.overstride}, tilt=${_analysisResult?.overlays.tilt}, vertical=${_analysisResult?.overlays.vertical}');
      notifyListeners();
    } catch (e) {
      print('❌ Failed to load analysis: $e');
      _errorMessage = 'Failed to load analysis result: $e';
      notifyListeners();
    }
  }

  /// Reset state
  void reset() {
    _state = UploadState.idle;
    _currentVideo = null;
    _keypoints = null;
    _analysisResult = null;
    _errorMessage = null;
    _progress = 0.0;
    _videoFile = null;
    _userId = null;
    _userName = null;
    notifyListeners();
  }
}
