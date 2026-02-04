import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'result_screen.dart';

/// Video analysis loading screen
class LoadingScreen extends StatefulWidget {
  const LoadingScreen({super.key});

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

    // Navigate to result screen after 5 seconds
    Future.delayed(const Duration(seconds: 5), () {
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const ResultScreen(),
          ),
        );
      }
    });
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
      body: Stack(
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
              '영상을 분석하고 있어요 ...',
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
      ),
    );
  }
}
