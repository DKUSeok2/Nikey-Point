import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:provider/provider.dart';
import '../providers/video_provider.dart';
import '../models/video_model.dart';
import 'result_screen.dart';

/// Video analysis loading screen
class LoadingScreen extends StatefulWidget {
  final File videoFile;
  final String userId;
  final double height;

  const LoadingScreen({
    super.key,
    required this.videoFile,
    required this.userId,
    required this.height,
  });

  @override
  State<LoadingScreen> createState() => _LoadingScreenState();
}

class _LoadingScreenState extends State<LoadingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);

    // 배경: top=352.5px, height=92px, 범위=352.5~444.5px
    // 캐릭터: height=67.5px, 중심=33.75px
    // 중심이 배경 아래(444.5px)일 때: top = 444.5 - 33.75 = 410.75px
    // 중심이 배경 위(352.5px)일 때: top = 352.5 - 33.75 = 318.75px
    _animation = Tween<double>(begin: 400.75, end: 318.75).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeInOut,
      ),
    );

    // Start video upload and processing after build completes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _startProcessing();
    });
  }

  Future<void> _startProcessing() async {
    final videoProvider = context.read<VideoProvider>();
    
    await videoProvider.uploadVideo(
      userId: widget.userId,
      videoFile: widget.videoFile,
      height: widget.height,
    );

    // Navigate to result screen if completed
    if (mounted && videoProvider.state == UploadState.completed) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const ResultScreen(),
        ),
      );
    } else if (mounted && videoProvider.state == UploadState.error) {
      // Show error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(videoProvider.errorMessage ?? '오류가 발생했습니다'),
          backgroundColor: Colors.red,
        ),
      );
      Navigator.pop(context);
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
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
      backgroundColor: const Color(0xFF1C1C1E), // systemGray6
      body: Consumer<VideoProvider>(
        builder: (context, videoProvider, child) {
          return Stack(
        children: [
          // Fixed gradient bar - Figma: top 30 from component (305 + 30 = 335)
          // Rotation center at (screenWidth/2, 381): 335 + 92/2
          // Before rotation: 92w x 57h, left = center_x - 46, top = center_y - 28.5
          Positioned(
            left: (screenWidth / 2) - (46 * scaleX), // 92/2 = 46
            top: (381 - 28.5) * scaleY, // 352.5
            child: Transform.rotate(
              angle: 1.5708, // 90 degrees
              child: SvgPicture.asset(
                'assets/images/loading_arrow.svg',
                width: 92 * scaleX,
                height: 57 * scaleY,
              ),
            ),
          ),
          
          // Animated character - moves from bottom to top of background
          AnimatedBuilder(
            animation: _animation,
            builder: (context, child) {
              return Positioned(
                left: (screenWidth / 2) - (30 * scaleX), // 60/2 = 30
                top: _animation.value * scaleY,
                child: SvgPicture.asset(
                  'assets/images/loading_character.svg',
                  width: 60 * scaleX,
                  height: 67.5 * scaleY,
                ),
              );
            },
          ),
          
            // Loading text
            Positioned(
              left: 0,
              right: 0,
              top: 509 * scaleY,
              child: Text(
                _getLoadingText(videoProvider.state, videoProvider.currentVideo?.processingStep),
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16 * scaleY,
                  fontWeight: FontWeight.w400,
                  color: const Color(0xFFF3F4F5).withOpacity(0.7),
                  height: 1.3125, // 21/16
                ),
              ),
            ),
          ],
        );
        },
      ),
    );
  }

  String _getLoadingText(UploadState state, ProcessingStep? processingStep) {
    switch (state) {
      case UploadState.uploading:
        return '영상 업로드 중 ...';
      case UploadState.processing:
        return _getProcessingStepText(processingStep);
      case UploadState.completed:
        return '피드백 생성 완료';
      case UploadState.error:
        return '오류가 발생했어요';
      default:
        return '준비 중 ...';
    }
  }
  
  String _getProcessingStepText(ProcessingStep? step) {
    print('🔍 Loading screen: processingStep = $step');
    if (step == null) return '영상을 분석하고 있어요 ...';
    
    switch (step) {
      case ProcessingStep.extractingHeight:
        return '키 추출중 ...';
      case ProcessingStep.extractingKeypoints:
        return '키포인트 추출중 ...';
      case ProcessingStep.calculatingMetrics:
        return '지표값 계산중 ...';
      case ProcessingStep.generatingFeedback:
        return '피드백 생성 중 ...';
      case ProcessingStep.completed:
        return '피드백 생성 완료';
      default:
        return '영상을 분석하고 있어요 ...';
    }
  }
}
