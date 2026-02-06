import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:provider/provider.dart';
import '../providers/video_provider.dart';

/// Analysis result screen
class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

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
        statusBarBrightness: Brightness.light,
        statusBarIconBrightness: Brightness.dark,
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
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Video preview section
            Container(
              height: 272 * scaleY,
              margin: EdgeInsets.only(top: 59 * scaleY),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.4),
                image: const DecorationImage(
                  image: AssetImage('assets/images/running_result.jpg'),
                  fit: BoxFit.cover,
                ),
              ),
              child: Stack(
                children: [
                  // Gradient overlay
                  Positioned.fill(
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
                  
                  // Time stamp
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
                        '0:15',
                        style: TextStyle(
                          fontSize: 12 * scaleY,
                          fontWeight: FontWeight.w500,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  
                  // Center text
                  Center(
                    child: Text(
                      '영상에서 키포인트',
                      style: TextStyle(
                        fontSize: 24 * scaleY,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                        height: 21 / 24,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            // Results section
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20 * scaleX),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(height: 47 * scaleY),
                  
                  // Overstride section
                  Row(
                    children: [
                      Text(
                        '오버스트라이드',
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w400,
                          color: const Color(0xFFF3F4F5).withOpacity(0.7),
                        ),
                      ),
                      SizedBox(width: 8 * scaleX),
                      Text(
                        analysisResult.overstrideStatus,
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w700,
                          color: analysisResult.isOverstrideNormal
                              ? const Color(0xFF8FEDFA)
                              : const Color(0xFFFF6B6B),
                        ),
                      ),
                    ],
                  ),
                  
                  SizedBox(height: 22 * scaleY),
                  
                  // Progress bar with characters
                  SizedBox(
                    height: 60 * scaleY,
                    child: Stack(
                      children: [
                        _buildProgressBar(
                          scaleX, 
                          scaleY, 
                          (analysisResult.metrics.overstride * 100).toInt(),
                        ),
                        
                        // Pink character (left)
                        Positioned(
                          left: 100 * scaleX,
                          bottom: 0,
                          child: SvgPicture.asset(
                            'assets/images/character_pink.svg',
                            width: 36 * scaleX,
                            height: 40.5 * scaleY,
                          ),
                        ),
                        
                        // Cyan character (right)
                        Positioned(
                          left: 245 * scaleX,
                          bottom: 0,
                          child: SvgPicture.asset(
                            'assets/images/character_cyan.svg',
                            width: 36 * scaleX,
                            height: 40.5 * scaleY,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  SizedBox(height: 12 * scaleY),
                  
                  // LLM Feedback
                  if (analysisResult.llmFeedback != null)
                    Text(
                      analysisResult.llmFeedback!,
                      style: TextStyle(
                        fontSize: 14 * scaleY,
                        fontWeight: FontWeight.w400,
                        color: const Color(0xFFF3F4F5).withOpacity(0.7),
                        height: 1.4,
                      ),
                    ),
                  
                  SizedBox(height: 32 * scaleY),
                  
                  // Tilt section
                  Row(
                    children: [
                      Text(
                        '상체 기울기',
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w400,
                          color: const Color(0xFFF3F4F5).withOpacity(0.7),
                        ),
                      ),
                      SizedBox(width: 8 * scaleX),
                      Text(
                        analysisResult.tiltStatus,
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF8FEDFA),
                        ),
                      ),
                      SizedBox(width: 8 * scaleX),
                      Text(
                        '${analysisResult.metrics.tilt.toStringAsFixed(1)}°',
                        style: TextStyle(
                          fontSize: 14 * scaleY,
                          fontWeight: FontWeight.w400,
                          color: const Color(0xFFF3F4F5).withOpacity(0.5),
                        ),
                      ),
                    ],
                  ),
                  
                  SizedBox(height: 20 * scaleY),
                  
                  // Vertical section
                  Row(
                    children: [
                      Text(
                        '수직 진동',
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w400,
                          color: const Color(0xFFF3F4F5).withOpacity(0.7),
                        ),
                      ),
                      SizedBox(width: 8 * scaleX),
                      Text(
                        analysisResult.verticalStatus,
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFF8FEDFA),
                        ),
                      ),
                      SizedBox(width: 8 * scaleX),
                      Text(
                        analysisResult.metrics.vertical.toStringAsFixed(4),
                        style: TextStyle(
                          fontSize: 14 * scaleY,
                          fontWeight: FontWeight.w400,
                          color: const Color(0xFFF3F4F5).withOpacity(0.5),
                        ),
                      ),
                    ],
                  ),
                  
                  SizedBox(height: 40 * scaleY),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressBar(double scaleX, double scaleY, int value) {
    return Stack(
      children: [
        // Indicator line on top
        Positioned(
          top: -5 * scaleY,
          left: 0,
          right: 0,
          child: Container(
            height: 10 * scaleY,
            decoration: BoxDecoration(
              border: Border(
                top: BorderSide(
                  color: Colors.white.withOpacity(0.4),
                  width: 10 * scaleY,
                ),
              ),
            ),
          ),
        ),
        
        // Background bar
        Container(
          width: 320 * scaleX,
          height: 22 * scaleY,
          decoration: BoxDecoration(
            color: const Color(0xFF3A3A3C), // systemGray4
            borderRadius: BorderRadius.circular(10),
          ),
        ),
        
        // Value indicators
        Positioned(
          left: 0,
          bottom: -10 * scaleY,
          child: Text(
            '0',
            style: TextStyle(
              fontSize: 10 * scaleY,
              fontWeight: FontWeight.w300,
              color: Colors.white.withOpacity(0.54),
              letterSpacing: 0.4,
            ),
          ),
        ),
        
        Positioned(
          right: 0,
          bottom: -10 * scaleY,
          child: Text(
            '100',
            style: TextStyle(
              fontSize: 10 * scaleY,
              fontWeight: FontWeight.w300,
              color: Colors.white.withOpacity(0.54),
              letterSpacing: 0.4,
            ),
          ),
        ),
        
        // Current value indicator
        Positioned(
          left: (value / 100) * 320 * scaleX - 14 * scaleX,
          top: 32 * scaleY,
          child: Container(
            padding: EdgeInsets.symmetric(
              horizontal: 8 * scaleX,
              vertical: 2 * scaleY,
            ),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              value.toString(),
              style: TextStyle(
                fontSize: 10 * scaleY,
                fontWeight: FontWeight.w600,
                color: Colors.black,
                letterSpacing: 0.4,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
