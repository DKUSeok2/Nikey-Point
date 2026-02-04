import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'guide_2_screen.dart';
import '../widgets/cta_button.dart';

/// Guide screen with character and start button
class GuideScreen extends StatelessWidget {
  const GuideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Set status bar style to light for dark background
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
          
          // Checkered floor - Figma: (-120, 502.79), size: 626.765x213.1
          Positioned(
            left: -120 * scaleX,
            top: 502.79 * scaleY,
            width: 626.765 * scaleX,
            height: 213.1 * scaleY,
            child: SvgPicture.asset(
              'assets/images/checkered_floor_new.svg',
              fit: BoxFit.cover,
            ),
          ),
          
          // Gradient overlay - Figma: (-27.78, 538.62), size: 435.768x132.667
          Positioned(
            left: -27.78 * scaleX,
            top: 538.62 * scaleY,
            width: 435.768 * scaleX,
            height: 132.667 * scaleY,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    const Color(0xFF2C2C2C).withOpacity(0.8),
                    const Color(0xFF2C2C2C).withOpacity(0.0),
                  ],
                ),
              ),
            ),
          ),
          
          // Character image - Figma: center, size: 191.432x191.432
          Positioned(
            left: (screenWidth / 2) - (191.432 * scaleX / 2),
            top: (screenHeight / 2) + (32.63 * scaleY) - (191.432 * scaleY / 2),
            width: 191.432 * scaleX,
            height: 191.432 * scaleY,
            child: SvgPicture.asset(
              'assets/images/character_main.svg',
              fit: BoxFit.contain,
            ),
          ),
          
          // CTA Button - Figma: (20, 730), size: 350x54
          Positioned(
            left: 20 * scaleX,
            top: 730 * scaleY,
            right: 20 * scaleX,
            child: CtaButton(
              text: '다음으로',
              variant: CtaButtonVariant.active,
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const Guide2Screen(),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
