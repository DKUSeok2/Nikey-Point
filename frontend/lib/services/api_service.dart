import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/api_config.dart';
import '../models/video_model.dart';
import '../models/keypoint_model.dart';

/// API Service for backend communication
class ApiService {
  /// Upload video file with user info
  Future<VideoModel> uploadVideo({
    required String userId,
    required File videoFile,
    required double height,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse(ApiConfig.videoUpload),
      );

      // Add fields
      request.fields['user_id'] = userId;

      // Add file
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          videoFile.path,
        ),
      );

      // Send request
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 201 || response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return VideoModel.fromJson(json);
      } else {
        throw Exception('Upload failed: ${response.statusCode} ${response.body}');
      }
    } catch (e) {
      throw Exception('Upload error: $e');
    }
  }

  /// Get video processing status
  Future<VideoModel> getVideoStatus(String videoId) async {
    try {
      final response = await http.get(
        Uri.parse(ApiConfig.videoStatus(videoId)),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return VideoModel.fromJson(json);
      } else {
        throw Exception('Failed to get status: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Status check error: $e');
    }
  }

  /// Get keypoints for a video
  Future<KeypointResponse> getKeypoints(String videoId) async {
    try {
      final response = await http.get(
        Uri.parse(ApiConfig.videoKeypoints(videoId)),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return KeypointResponse.fromJson(json);
      } else {
        throw Exception('Failed to get keypoints: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Keypoints error: $e');
    }
  }

  /// Health check
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse(ApiConfig.healthCheck),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
