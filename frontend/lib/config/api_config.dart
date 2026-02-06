import 'dart:io';

/// API configuration for NikePoint backend
class ApiConfig {
  // Base URL - 플랫폼별로 자동 설정
  static String get baseUrl {
    if (Platform.isAndroid) {
      // Android 에뮬레이터는 10.0.2.2를 사용하여 호스트 머신에 접근
      return 'http://10.0.2.2:8000';
    } else if (Platform.isIOS) {
      // iOS 실제 기기는 Mac의 Wi-Fi IP 사용 (시뮬레이터도 동일)
      return 'http://192.168.219.212:8000';
    } else {
      // 기타 플랫폼 (웹 등)
      return 'http://192.168.219.212:8000';
    }
  }
  
  // API Endpoints
  static String get authRegister => '$baseUrl/api/auth/register';
  static String get authLogin => '$baseUrl/api/auth/login';
  
  static String userInfo(String userId) => '$baseUrl/api/auth/user/$userId';
  
  // User endpoints
  static String get userRegister => '$baseUrl/api/user/register';
  
  static String get videoUpload => '$baseUrl/api/video/upload';
  static String videoStatus(String videoId) => '$baseUrl/api/video/$videoId/status';
  static String video(String videoId) => '$baseUrl/api/video/$videoId';
  
  static String videoKeypoints(String videoId) => '$baseUrl/api/pose/video/$videoId/keypoints';
  
  // Analysis endpoints
  static String analysisLatest(String userId) => '$baseUrl/api/analysis/user/$userId/latest';
  static String analysisHistory(String userId, int limit) => '$baseUrl/api/analysis/user/$userId/history?limit=$limit';
  static String allHistory(int limit) => '$baseUrl/api/analysis/history?limit=$limit';
  
  // Health check
  static String get healthCheck => '$baseUrl/api/health';
}
