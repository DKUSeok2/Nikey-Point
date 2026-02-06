import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/api_config.dart';
import '../models/video_model.dart';
import '../models/keypoint_model.dart';
import '../models/analysis_model.dart';

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

  /// Get latest analysis result for a user
  Future<AnalysisResult> getLatestAnalysis(String userId) async {
    try {
      // Add timestamp to bypass cache
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final url = '${ApiConfig.analysisLatest(userId)}?_t=$timestamp';
      print('🌐 Fetching analysis from: $url');
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      );

      print('📡 Response status: ${response.statusCode}');
      if (response.statusCode == 200) {
        print('📄 Raw response body length: ${response.body.length}');
        print('📄📄📄 FULL RAW RESPONSE BODY:');
        print(response.body);
        print('📄📄📄 END OF RAW RESPONSE');
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        print('🔑 JSON keys: ${json.keys.toList()}');
        print('🎬 Has overlays key: ${json.containsKey('overlays')}');
        if (json.containsKey('overlays')) {
          print('🎥 Overlays value: ${json['overlays']}');
        } else {
          print('❌ No overlays key in response!');
        }
        return AnalysisResult.fromJson(json);
      } else {
        throw Exception('Failed to get analysis: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Analysis error: $e');
    }
  }

  /// Get all analysis history (모든 사용자)
  Future<List<AnalysisResult>> getAllHistory({int limit = 30}) async {
    try {
      final response = await http.get(
        Uri.parse(ApiConfig.allHistory(limit)),
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      );

      if (response.statusCode == 200) {
        final jsonList = jsonDecode(response.body) as List<dynamic>;
        return jsonList
            .map((json) => AnalysisResult.fromJson(json as Map<String, dynamic>))
            .toList();
      } else {
        throw Exception('Failed to get history: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('History error: $e');
    }
  }

  /// Get analysis history for a user
  Future<List<AnalysisResult>> getAnalysisHistory(String userId, {int limit = 10}) async {
    try {
      final response = await http.get(
        Uri.parse(ApiConfig.analysisHistory(userId, limit)),
      );

      if (response.statusCode == 200) {
        final jsonList = jsonDecode(response.body) as List<dynamic>;
        return jsonList
            .map((json) => AnalysisResult.fromJson(json as Map<String, dynamic>))
            .toList();
      } else {
        throw Exception('Failed to get history: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('History error: $e');
    }
  }

  /// Create a new user
  Future<Map<String, dynamic>> createUser({
    required String userName,
    required double height,
  }) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConfig.userRegister),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_name': userName,
          'height': height,
        }),
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw Exception('Failed to create user: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('User creation error: $e');
    }
  }
}
