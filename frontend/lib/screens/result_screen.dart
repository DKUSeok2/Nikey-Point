import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';
import '../models/analysis_model.dart';
import '../providers/video_provider.dart';
import '../widgets/cta_button.dart';
import '../config/api_config.dart';
import 'metric_detail_screen.dart';

/// Analysis result screen
class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  VideoPlayerController? _videoController;

  @override
  void initState() {
    super.initState();
    _initVideoPlayer();
  }

  void _initVideoPlayer() {
    final videoProvider = context.read<VideoProvider>();
    final analysisResult = videoProvider.analysisResult;
    
    // Keypoint 영상 경로 사용 (없으면 원본 로컬 파일 사용)
    if (analysisResult?.keypointVideoPath != null) {
      // 네트워크 URL로 keypoint 영상 로드 (오버레이와 같은 방식)
      final keypointPath = analysisResult!.keypointVideoPath!;
      // /app/storage/keypoints/xxx.mp4 -> /storage/keypoints/xxx.mp4
      final networkPath = keypointPath.replaceFirst('/app', '');
      final fullUrl = '${ApiConfig.baseUrl}$networkPath';
      
      print('🎬 Loading keypoint video from URL: $fullUrl');
      
      _videoController = VideoPlayerController.networkUrl(Uri.parse(fullUrl))
        ..initialize().then((_) {
          print('✅ Keypoint video initialized');
          setState(() {});
          _videoController?.setLooping(true);
          _videoController?.play();
          _videoController?.addListener(() {
            if (mounted) {
              setState(() {});
            }
          });
        }).catchError((error) {
          print('❌ Keypoint video failed to load: $error');
          // Fallback to original video
          if (videoProvider.videoFile != null) {
            print('↩️ Falling back to original video');
            _videoController = VideoPlayerController.file(videoProvider.videoFile!)
              ..initialize().then((_) {
                setState(() {});
                _videoController?.setLooping(true);
                _videoController?.play();
                _videoController?.addListener(() {
                  if (mounted) {
                    setState(() {});
                  }
                });
              });
          }
        });
    } else if (videoProvider.videoFile != null) {
      // Fallback: 로컬 원본 영상 사용
      print('ℹ️ No keypoint video, using original video');
      _videoController = VideoPlayerController.file(videoProvider.videoFile!)
        ..initialize().then((_) {
          setState(() {});
          _videoController?.setLooping(true);
          _videoController?.play();
          _videoController?.addListener(() {
            if (mounted) {
              setState(() {});
            }
          });
        });
    }
  }

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  void _showFullscreenVideo(BuildContext context) {
    if (_videoController == null || !_videoController!.value.isInitialized) {
      return;
    }
    
    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.9),
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: EdgeInsets.zero,
        child: Stack(
          children: [
            // Full video player
            Center(
              child: AspectRatio(
                aspectRatio: _videoController!.value.aspectRatio,
                child: VideoPlayer(_videoController!),
              ),
            ),
            // Close button
            Positioned(
              top: 50,
              right: 20,
              child: GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.5),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.close,
                    color: Colors.white,
                    size: 24,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final videoProvider = context.watch<VideoProvider>();
    final analysisResult = videoProvider.analysisResult;

    // Show loading if no result yet
    if (analysisResult == null) {
      return Scaffold(
        backgroundColor: const Color(0xFF1C1C1E),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    // Set status bar style
    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarBrightness: Brightness.dark,
        statusBarIconBrightness: Brightness.light,
      ),
    );

    final screenHeight = MediaQuery.of(context).size.height;
    final screenWidth = MediaQuery.of(context).size.width;
    
    // Figma design: 390x844
    final figmaHeight = 844.0;
    final figmaWidth = 390.0;
    
    // Scale factors
    final scaleY = screenHeight / figmaHeight;
    final scaleX = screenWidth / figmaWidth;

    return Scaffold(
      backgroundColor: const Color(0xFF1C1C1E), // systemGray6
      body: Stack(
        children: [
          // Scrollable content
          SingleChildScrollView(
            child: Column(
              children: [
                SizedBox(height: 59 * scaleY), // Status bar height
                
                // Video preview section - reduced height
                _buildVideoSection(scaleX, scaleY, screenWidth),
                
                SizedBox(height: 10 * scaleY),
                
                // Metric cards - Figma: (16, 351)
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16 * scaleX),
                  child: Column(
                    children: [
                      _buildOverstrideCard(scaleX, scaleY, analysisResult),
                      SizedBox(height: 10 * scaleY),
                      _buildTiltCard(scaleX, scaleY, analysisResult),
                      SizedBox(height: 10 * scaleY),
                      _buildVerticalCard(scaleX, scaleY, analysisResult),
                    ],
                  ),
                ),
                
                SizedBox(height: 20 * scaleY),
                
                // Feedback text - Figma: (20, 746)
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20 * scaleX),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      MarkdownBody(
                        data: '# **사용자를 위한 러닝 자세 피드백**\n\n${analysisResult.llmFeedback ?? '분석 결과가 생성되었습니다.'}',
                        styleSheet: MarkdownStyleSheet(
                          p: TextStyle(
                            fontSize: 14 * scaleY,
                            fontWeight: FontWeight.w400,
                            color: Colors.white.withOpacity(0.7),
                            height: 1.4,
                          ),
                          h1: TextStyle(
                            fontSize: 18 * scaleY,
                            fontWeight: FontWeight.w500,
                            color: Colors.white.withOpacity(0.9),
                            height: 21 / 18,
                          ),
                          h2: TextStyle(
                            fontSize: 16 * scaleY,
                            fontWeight: FontWeight.w500,
                            color: Colors.white.withOpacity(0.9),
                            height: 1.3,
                          ),
                          h3: TextStyle(
                            fontSize: 15 * scaleY,
                            fontWeight: FontWeight.w500,
                            color: Colors.white.withOpacity(0.9),
                            height: 1.3,
                          ),
                          strong: TextStyle(
                            fontWeight: FontWeight.w700,
                            color: Colors.white.withOpacity(0.9),
                          ),
                          em: TextStyle(
                            fontStyle: FontStyle.italic,
                            color: Colors.white.withOpacity(0.8),
                          ),
                          listBullet: TextStyle(
                            fontSize: 14 * scaleY,
                            color: Colors.white.withOpacity(0.7),
                          ),
                          blockSpacing: 10 * scaleY,
                          listIndent: 20 * scaleX,
                        ),
                      ),
                    ],
                  ),
                ),
                
                SizedBox(height: 40 * scaleY),
                
                // Bottom button - placed in scrollable content
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20 * scaleX),
                  child: SizedBox(
                    width: double.infinity,
                    child: CtaButton(
                      text: '확인완료',
                      variant: CtaButtonVariant.active,
                      onPressed: () {
                        // 첫 번째 페이지(시작 화면)로 이동
                        Navigator.popUntil(context, (route) => route.isFirst);
                      },
                    ),
                  ),
                ),
                
                SizedBox(height: 50 * scaleY), // Bottom spacing
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVideoSection(double scaleX, double scaleY, double screenWidth) {
    return Container(
      width: 390 * scaleX,
      height: 300 * scaleY, // 컨테이너 높이 300px
      color: const Color(0xFF1C1C1E), // 검은 배경
      child: Stack(
        children: [
          // Video player - 위쪽을 잘라내고 중간 부분 표시
          if (_videoController != null && _videoController!.value.isInitialized)
            Positioned(
              top: -100 * scaleY, // 위쪽 100px 잘라내기
              left: 0,
              right: 0,
              height: 600 * scaleY, // 영상을 600px 높이로 표시
              child: ClipRect(
                child: FittedBox(
                  fit: BoxFit.cover,
                  alignment: Alignment.center,
                  child: SizedBox(
                    width: _videoController!.value.size.width,
                    height: _videoController!.value.size.height,
                    child: VideoPlayer(_videoController!),
                  ),
                ),
              ),
            )
          else
            Positioned(
              top: -100 * scaleY, // 위쪽 100px 잘라내기
              left: 0,
              right: 0,
              height: 600 * scaleY,
              child: Container(
                color: Colors.grey[800],
                child: const Center(
                  child: Icon(Icons.video_library, size: 50, color: Colors.white54),
                ),
              ),
            ),
          
          // Gradient overlay - 영상 영역에만 적용
          Positioned(
            top: -100 * scaleY, // 영상과 동일하게 위치
            left: 0,
            right: 0,
            height: 600 * scaleY,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  stops: const [0.56295, 1.0],
                  colors: [
                    Colors.transparent,
                    Colors.black.withOpacity(0.6),
                  ],
                ),
              ),
            ),
          ),
          
          // Time stamp - Figma: (10, 10)
          Positioned(
            left: 10 * scaleX,
            top: 10 * scaleY,
            child: Container(
              padding: EdgeInsets.symmetric(
                horizontal: 10 * scaleX,
                vertical: 6 * scaleY,
              ),
              decoration: BoxDecoration(
                color: const Color(0xFF18191B).withOpacity(0.5),
                borderRadius: BorderRadius.circular(40),
              ),
              child: Text(
                _videoController != null && _videoController!.value.isInitialized
                    ? _formatDuration(_videoController!.value.duration)
                    : '0:15',
                style: TextStyle(
                  fontSize: 12 * scaleY,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          
          // Fullscreen button - top right
          Positioned(
            right: 10 * scaleX,
            top: 10 * scaleY,
            child: GestureDetector(
              onTap: () => _showFullscreenVideo(context),
              child: Container(
                padding: EdgeInsets.all(8 * scaleX),
                decoration: BoxDecoration(
                  color: const Color(0xFF18191B).withOpacity(0.5),
                  borderRadius: BorderRadius.circular(40),
                ),
                child: Icon(
                  Icons.fullscreen,
                  color: Colors.white,
                  size: 20 * scaleX,
                ),
              ),
            ),
          ),
          
          // Video progress bar at bottom
          if (_videoController != null && _videoController!.value.isInitialized)
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: _buildVideoProgressBar(scaleX, scaleY),
            ),
        ],
      ),
    );
  }
  
  Widget _buildVideoProgressBar(double scaleX, double scaleY) {
    final duration = _videoController!.value.duration.inMilliseconds;
    final position = _videoController!.value.position.inMilliseconds;
    final progress = duration > 0 ? position / duration : 0.0;
    
    return Container(
      height: 4 * scaleY,
      child: Stack(
        children: [
          // Background bar
          Container(
            width: 390 * scaleX,
            height: 4 * scaleY,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [
                  Colors.white.withOpacity(0.24),
                  Colors.white.withOpacity(0.24),
                ],
              ),
            ),
          ),
          
          // Progress bar
          Container(
            width: 390 * scaleX * progress,
            height: 4 * scaleY,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [
                  Color(0xFF4876FF), // #4876FF
                  Color(0xFF4876FF),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds.remainder(60);
    return '$minutes:${twoDigits(seconds)}';
  }

  // Overstride card: 정상 범위 중심으로 조정 (정상: 0~0.18)
  Widget _buildOverstrideCard(double scaleX, double scaleY, AnalysisResult result) {
    final value = result.metrics.overstride;
    final normalMin = 0.0;
    final normalMax = 0.18;
    final normalRange = normalMax - normalMin;
    final padding = normalRange * 0.7; // 정상 범위의 70%를 양쪽 여유로
    final minRange = (normalMin - padding).clamp(0.0, double.infinity);
    final maxRange = normalMax + padding;
    
    // Calculate position (0~326px)
    final position = ((value - minRange) / (maxRange - minRange) * 326).clamp(0.0, 326.0);
    
    // Calculate normal range positions
    final normalRangeStart = ((normalMin - minRange) / (maxRange - minRange) * 326);
    final normalRangeEnd = ((normalMax - minRange) / (maxRange - minRange) * 326);
    
    // Score out of 100
    final score = ((value / normalMax) * 100).clamp(0.0, 100.0).round();
    
    return _buildMetricCard(
      scaleX: scaleX,
      scaleY: scaleY,
      title: '오버스트라이드',
      status: result.overstrideStatus,
      value: value,
      valueText: value.toStringAsFixed(2),
      position: position,
      score: score,
      normalRangeStart: normalRangeStart,
      normalRangeEnd: normalRangeEnd,
      minLabel: normalMin.toStringAsFixed(2), // 정상 범위 시작
      maxLabel: normalMax.toStringAsFixed(2), // 정상 범위 끝
      isNormal: result.isOverstrideNormal,
      onVideoPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const MetricDetailScreen(
              metricType: MetricType.overstride,
            ),
          ),
        );
      },
    );
  }
  
  // Tilt card: 정상 범위 중심으로 조정 (절댓값 기준, 정상: 72~88)
  Widget _buildTiltCard(double scaleX, double scaleY, AnalysisResult result) {
    final value = result.metrics.tilt;
    final absValue = value.abs(); // 절댓값 (표시용)
    
    // 음수 범위로 계산 (더 음수 = 왼쪽)
    final normalMin = -88.0;
    final normalMax = -72.0;
    final normalRange = normalMax - normalMin; // 16
    final padding = normalRange * 1.5; // 24
    final minRange = normalMin - padding; // -112 (더 음수, 왼쪽)
    final maxRange = normalMax + padding; // -48 (덜 음수, 오른쪽)
    
    // Calculate position (0~326px) - 음수 값 그대로 사용
    final position = ((value - minRange) / (maxRange - minRange) * 326).clamp(0.0, 326.0);
    
    // Calculate normal range positions
    final normalRangeStart = ((normalMin - minRange) / (maxRange - minRange) * 326);
    final normalRangeEnd = ((normalMax - minRange) / (maxRange - minRange) * 326);
    
    // Check if in normal range (절댓값으로 비교)
    final isNormal = absValue >= 72 && absValue <= 88;
    
    // Score: distance from ideal (-80°)
    final ideal = -80.0;
    final distanceFromIdeal = (value - ideal).abs();
    final maxDistance = 10.0;
    final score = (100 - (distanceFromIdeal / maxDistance * 100)).clamp(0.0, 100.0).round();
    
    return _buildMetricCard(
      scaleX: scaleX,
      scaleY: scaleY,
      title: '상체 기울기',
      status: result.tiltStatus,
      value: value,
      valueText: '${value.toStringAsFixed(1)}°', // 음수 그대로 표시
      position: position,
      score: score,
      normalRangeStart: normalRangeStart,
      normalRangeEnd: normalRangeEnd,
      minLabel: '-88°', // 정상 범위 시작
      maxLabel: '-72°', // 정상 범위 끝
      isNormal: isNormal,
      onVideoPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const MetricDetailScreen(
              metricType: MetricType.tilt,
            ),
          ),
        );
      },
    );
  }
  
  // Vertical card: 정상 범위 중심으로 조정 (정상: 0.10~0.41)
  Widget _buildVerticalCard(double scaleX, double scaleY, AnalysisResult result) {
    final value = result.metrics.vertical;
    final normalMin = 0.01;
    final normalMax = 0.08;
    final normalRange = normalMax - normalMin;
    final padding = normalRange * 0.7; // 정상 범위의 70%를 양쪽 여유로
    final minRange = (normalMin - padding).clamp(0.0, double.infinity);
    final maxRange = normalMax + padding;
    
    // Calculate position (0~326px)
    final position = ((value - minRange) / (maxRange - minRange) * 326).clamp(0.0, 326.0);
    
    // Calculate normal range positions
    final normalRangeStart = ((normalMin - minRange) / (maxRange - minRange) * 326);
    final normalRangeEnd = ((normalMax - minRange) / (maxRange - minRange) * 326);
    
    // Check if in normal range (analysis_model의 로직 사용)
    final isNormal = result.isVerticalNormal;
    
    // Score: within range = 100, outside = decrease
    final score = isNormal 
        ? 100 
        : (value < normalMin 
            ? ((value / normalMin) * 100).clamp(0.0, 100.0).round()
            : (100 - ((value - normalMax) / (maxRange - normalMax) * 100)).clamp(0.0, 100.0).round());
    
    return _buildMetricCard(
      scaleX: scaleX,
      scaleY: scaleY,
      title: '무게 중심 상하 움직임',
      status: result.verticalStatus,
      value: value,
      valueText: value.toStringAsFixed(2),
      position: position,
      score: score,
      normalRangeStart: normalRangeStart,
      normalRangeEnd: normalRangeEnd,
      minLabel: normalMin.toStringAsFixed(2), // 정상 범위 시작
      maxLabel: normalMax.toStringAsFixed(2), // 정상 범위 끝
      isNormal: isNormal,
      onVideoPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const MetricDetailScreen(
              metricType: MetricType.vertical,
            ),
          ),
        );
      },
    );
  }

  Widget _buildMetricCard({
    required double scaleX,
    required double scaleY,
    required String title,
    required String status,
    required double value,
    required String valueText,
    required double position,
    required int score,
    required double normalRangeStart,
    required double normalRangeEnd,
    required String minLabel,
    required String maxLabel,
    required bool isNormal,
    VoidCallback? onVideoPressed,
  }) {
    return Container(
      width: 358 * scaleX,
      padding: EdgeInsets.only(
        top: 12 * scaleY,
        bottom: 30 * scaleY,
        left: 16 * scaleX,
        right: 16 * scaleX,
      ),
      decoration: BoxDecoration(
        color: const Color(0xFF131313),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Title and status
              Row(
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 16 * scaleY,
                      fontWeight: FontWeight.w500,
                      color: Colors.white.withOpacity(0.9),
                      height: 21 / 16,
                    ),
                  ),
                  SizedBox(width: 10 * scaleX),
                  Text(
                    status,
                    style: TextStyle(
                      fontSize: 14 * scaleY,
                      fontWeight: FontWeight.w700,
                      color: isNormal ? const Color(0xFF8FEDFA) : const Color(0xFFFF6B6B),
                      height: 21 / 14,
                    ),
                  ),
                ],
              ),
              
              // Video button
              GestureDetector(
                onTap: onVideoPressed,
                child: Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: 8 * scaleX,
                    vertical: 2 * scaleY,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFF3A3A3C),
                    borderRadius: BorderRadius.circular(50),
                  ),
                  child: Row(
                    children: [
                      SvgPicture.asset(
                        'assets/images/video_icon.svg',
                        width: 14 * scaleX,
                        height: 14 * scaleY,
                      ),
                      SizedBox(width: 4 * scaleX),
                      Text(
                        '영상보기',
                        style: TextStyle(
                          fontSize: 12 * scaleY,
                          fontWeight: FontWeight.w500,
                          color: Colors.white,
                          height: 21 / 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          
          SizedBox(height: 14 * scaleY),
          
          // Progress bar
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                height: 40 * scaleY, // 높이 증가
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    // Scale labels - moved above the bar
                    Positioned(
                      top: 0,
                      child: SizedBox(
                        width: 326 * scaleX,
                        height: 14 * scaleY,
                        child: Stack(
                          children: [
                            // Min label at normal range start
                            Positioned(
                              left: normalRangeStart * scaleX,
                              child: Text(
                                minLabel,
                                style: TextStyle(
                                  fontSize: 10 * scaleY,
                                  fontWeight: FontWeight.w400,
                                  color: const Color(0xFF616161), // Grey/700
                                  height: 1.4,
                                  letterSpacing: 0.4,
                                ),
                              ),
                            ),
                            // Max label at normal range end
                            Positioned(
                              right: (326 - normalRangeEnd) * scaleX,
                              child: Text(
                                maxLabel,
                                style: TextStyle(
                                  fontSize: 10 * scaleY,
                                  fontWeight: FontWeight.w400,
                                  color: const Color(0xFF616161), // Grey/700
                                  height: 1.4,
                                  letterSpacing: 0.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    // Background bar - moved down
                    Positioned(
                      top: 18 * scaleY,
                      child: Container(
                        width: 326 * scaleX,
                        height: 16 * scaleY,
                        decoration: BoxDecoration(
                          color: const Color(0xFF303336).withOpacity(0.5),
                          borderRadius: BorderRadius.circular(40),
                        ),
                      ),
                    ),
                    
                    // Normal range filled bar - moved down
                    Positioned(
                      top: 18 * scaleY,
                      left: normalRangeStart * scaleX,
                      child: Container(
                        width: (normalRangeEnd - normalRangeStart) * scaleX,
                        height: 16 * scaleY,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(10),
                          gradient: const LinearGradient(
                            colors: [
                              Color(0xFF00DCFF),
                              Color(0xFF00DCFF),
                            ],
                          ),
                        ),
                      ),
                    ),
                    
                    // Character icon - position based on actual value
                    Positioned(
                      left: (position * scaleX - 14 * scaleX).clamp(0, 326 * scaleX - 28 * scaleX),
                      top: 12 * scaleY, // 바와 같은 높이로 조정
                      child: Column(
                        children: [
                          SvgPicture.asset(
                            isNormal ? 'assets/images/character_blue.svg' : 'assets/images/character_red.svg',
                            width: 28 * scaleX,
                            height: 28 * scaleY,
                          ),
                          SizedBox(height: 4 * scaleY),
                          Container(
                            padding: EdgeInsets.symmetric(
                              horizontal: 6 * scaleX,
                              vertical: 2 * scaleY,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.baseline,
                              textBaseline: TextBaseline.alphabetic,
                              children: [
                                Text(
                                  '나',
                                  style: TextStyle(
                                    fontSize: 10 * scaleY,
                                    fontWeight: FontWeight.w400,
                                    color: Colors.white.withOpacity(0.8),
                                    height: 1.4,
                                    letterSpacing: 0.4,
                                  ),
                                ),
                                SizedBox(width: 4 * scaleX),
                                Text(
                                  valueText,
                                  style: TextStyle(
                                    fontSize: 12 * scaleY,
                                    fontWeight: FontWeight.w500,
                                    color: Colors.white.withOpacity(0.8),
                                    height: 1.4,
                                    letterSpacing: 0.48,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
