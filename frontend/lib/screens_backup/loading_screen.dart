import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:provider/provider.dart';
import '../providers/video_provider.dart';
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

    _animation = Tween<double>(begin: -10, end: 10).animate(
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
          // Character - Figma: bottom -0.5 from component (305 + 161 - 67.5 + 0.5 = 399)
          Positioned(
            left: (screenWidth / 2) - (30 * scaleX),
            top: 399 * scaleY,
            child: SvgPicture.asset(
              'assets/images/loading_character.svg',
              width: 60 * scaleX,
              height: 67.5 * scaleY,
            ),
          ),
          
          // Animated gradient bar - Figma: top 30 from component (305 + 30 = 335)
          // After rotation: 57w x 92h
          AnimatedBuilder(
            animation: _animation,
            builder: (context, child) {
              return Positioned(
                left: (screenWidth / 2) - (28.5 * scaleX), // 57/2 = 28.5
                top: 335 * scaleY + _animation.value,
                child: Transform.rotate(
                  angle: 1.5708, // 90 degrees
                  child: SvgPicture.asset(
                    'assets/images/loading_arrow.svg',
                    width: 92 * scaleX,
                    height: 57 * scaleY,
                  ),
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
                _getLoadingText(videoProvider.state),
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16 * scaleY,
                  fontWeight: FontWeight.w400,
                  color: const Color(0xFFF3F4F5).withOpacity(0.7),
                  height: 1.3125, // 21/16
                ),
              ),
            ),
            
            // Progress indicator
            if (videoProvider.state != UploadState.idle)
              Positioned(
                left: 0,
                right: 0,
                top: 550 * scaleY,
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: 60 * scaleX),
                  child: LinearProgressIndicator(
                    value: videoProvider.progress,
                    backgroundColor: Colors.white.withOpacity(0.2),
                    valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF8FEDFA)),
                  ),
                ),
              ),
          ],
        );
        },
      ),
    );
  }

  String _getLoadingText(UploadState state) {
    switch (state) {
      case UploadState.uploading:
        return '영상을 업로드하고 있어요 ...';
      case UploadState.processing:
        return '영상을 분석하고 있어요 ...';
      case UploadState.completed:
        return '분석이 완료되었어요!';
      default:
        return '준비 중 ...';
    }
  }
}
