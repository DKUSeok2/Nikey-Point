/// API configuration for NikePoint backend
class ApiConfig {
  // Base URL - localhost works in iOS simulator
  static const String baseUrl = 'http://localhost:8000';
  
  // API Endpoints
  static const String authRegister = '$baseUrl/api/auth/register';
  static const String authLogin = '$baseUrl/api/auth/login';
  
  static String userInfo(String userId) => '$baseUrl/api/auth/user/$userId';
  
  static const String videoUpload = '$baseUrl/api/video/upload';
  static String videoStatus(String videoId) => '$baseUrl/api/video/$videoId/status';
  static String video(String videoId) => '$baseUrl/api/video/$videoId';
  
  static String videoKeypoints(String videoId) => '$baseUrl/api/pose/video/$videoId/keypoints';
  
  // Health check
  static const String healthCheck = '$baseUrl/api/health';
}
