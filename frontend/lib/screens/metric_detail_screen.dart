import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:video_player/video_player.dart';
import 'package:provider/provider.dart';
import '../providers/video_provider.dart';
import '../config/api_config.dart';

enum MetricType {
  overstride,
  tilt,
  vertical,
}

class MetricDetailScreen extends StatefulWidget {
  final MetricType metricType;

  const MetricDetailScreen({
    Key? key,
    required this.metricType,
  }) : super(key: key);

  @override
  State<MetricDetailScreen> createState() => _MetricDetailScreenState();
}

class _MetricDetailScreenState extends State<MetricDetailScreen> {
  VideoPlayerController? _overlayController;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initOverlayVideo();
    });
  }

  void _initOverlayVideo() {
    final analysisResult = context.read<VideoProvider>().analysisResult;
    if (analysisResult == null) {
      print('❌ analysisResult is null');
      return;
    }

    // API 우회: 분석 ID로 직접 오버레이 경로 생성
    final analysisId = analysisResult.id;
    String? overlayPath;
    
    switch (widget.metricType) {
      case MetricType.overstride:
        overlayPath = '/storage/overlays/overstride_overlay_$analysisId.mp4';
        print('🎬 Generated overstride overlay path: $overlayPath');
        break;
      case MetricType.tilt:
        overlayPath = '/storage/overlays/tilt_overlay_$analysisId.mp4';
        print('🎬 Generated tilt overlay path: $overlayPath');
        break;
      case MetricType.vertical:
        overlayPath = '/storage/overlays/vertical_overlay_$analysisId.mp4';
        print('🎬 Generated vertical overlay path: $overlayPath');
        break;
    }

    if (overlayPath != null) {
      final fullUrl = '${ApiConfig.baseUrl}$overlayPath';
      print('📺 Full overlay URL: $fullUrl');
      _overlayController = VideoPlayerController.networkUrl(Uri.parse(fullUrl))
        ..initialize().then((_) {
          print('✅ Overlay video initialized');
          setState(() {});
          _overlayController?.setLooping(true);
          _overlayController?.play();
        }).catchError((error) {
          print('❌ Overlay video error: $error');
        });
    } else {
      print('❌ Overlay path is null');
    }
  }

  @override
  void dispose() {
    _overlayController?.dispose();
    super.dispose();
  }

  String get _title {
    switch (widget.metricType) {
      case MetricType.overstride:
        return '오버스트라이드';
      case MetricType.tilt:
        return '상체 기울기';
      case MetricType.vertical:
        return '무게 중심 상하 움직임';
    }
  }

  @override
  Widget build(BuildContext context) {
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
      backgroundColor: const Color(0xFF1C1C1E),
      body: Stack(
        children: [
              // Overlay video - centered with proper size
              if (_overlayController != null && _overlayController!.value.isInitialized)
                Center(
                  child: Container(
                    constraints: BoxConstraints(
                      maxHeight: screenHeight * 0.7,
                      maxWidth: screenWidth * 0.9,
                    ),
                    child: AspectRatio(
                      aspectRatio: _overlayController!.value.aspectRatio,
                      child: VideoPlayer(_overlayController!),
                    ),
                  ),
                )
              else
                const Center(
                  child: CircularProgressIndicator(color: Colors.white),
                ),

          // Top bar
          Positioned(
            top: 59 * scaleY,
            left: 0,
            right: 0,
            height: 54 * scaleY,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 20 * scaleX),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Back button
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      width: 24 * scaleX,
                      height: 24 * scaleY,
                      alignment: Alignment.center,
                      child: Icon(
                        Icons.chevron_left,
                        color: Colors.white,
                        size: 28 * scaleX,
                      ),
                    ),
                  ),
                  
                  // Title
                  Text(
                    _title,
                    style: TextStyle(
                      fontSize: 18 * scaleY,
                      fontWeight: FontWeight.w500,
                      fontFamily: 'Pretendard',
                      color: Colors.white,
                    ),
                  ),
                  
                  // Spacer (invisible back button for centering)
                  SizedBox(
                    width: 24 * scaleX,
                    height: 24 * scaleY,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
