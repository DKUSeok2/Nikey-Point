import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'guide_2_screen.dart';
import '../widgets/cta_button.dart';
import '../widgets/app_drawer.dart';

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
      endDrawer: const AppDrawer(),
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
          
          // Gradient overlay - covers entire checkered floor
          Positioned(
            left: -120 * scaleX,
            top: 502.79 * scaleY,
            width: 626.765 * scaleX,
            height: 213.1 * scaleY,
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
          
          // Character image - Figma: left=99.28px (center - 95.716), top=326.78px (422-95.716)
          Positioned(
            left: (screenWidth / 2) - (191.432 * scaleX / 2),
            top: 326.78 * scaleY,
            width: 191.432 * scaleX,
            height: 191.432 * scaleY,
            child: SvgPicture.asset(
              'assets/images/character_main.svg',
              fit: BoxFit.contain,
            ),
          ),
          
          // Title "Nikeypoint" - Figma: center top, top: 202.5px
          Positioned(
            left: 0,
            right: 0,
            top: 202.5 * scaleY,
            child: Center(
              child: Text(
                'Nikeypoint',
                style: TextStyle(
                  fontSize: 36.582 * ((scaleX + scaleY) / 2),
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                  letterSpacing: -0.5,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
          
          // Top bar with menu icon - Figma: top: 68px
          Positioned(
            right: 20 * scaleX,
            top: 68 * scaleY,
            child: Builder(
              builder: (context) => GestureDetector(
                onTap: () {
                  Scaffold.of(context).openEndDrawer();
                },
                child: Container(
                  padding: const EdgeInsets.all(4),
                  child: SvgPicture.asset(
                    'assets/images/menu_icon.svg',
                    width: 24,
                    height: 24,
                    colorFilter: const ColorFilter.mode(
                      Colors.white,
                      BlendMode.srcIn,
                    ),
                  ),
                ),
              ),
            ),
          ),
          
          // CTA Button - Figma: (20, 730), size: 350x54
          Positioned(
            left: 20 * scaleX,
            top: 730 * scaleY,
            right: 20 * scaleX,
            child: CtaButton(
              text: '시작하기',
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
