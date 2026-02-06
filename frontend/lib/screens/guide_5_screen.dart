import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../widgets/cta_button.dart';
import 'personal_info_screen.dart';

/// Guide screen 5 - Full body requirement
class Guide5Screen extends StatefulWidget {
  const Guide5Screen({super.key});

  @override
  State<Guide5Screen> createState() => _Guide5ScreenState();
}

class _Guide5ScreenState extends State<Guide5Screen> {
  bool _isButtonActive = false;

  @override
  void initState() {
    super.initState();
    // 3초 후 버튼 활성화
    Timer(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _isButtonActive = true;
        });
      }
    });
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
          // Back button - Figma: (20, 68)
          Positioned(
            left: 20 * scaleX,
            top: 68 * scaleY,
            child: GestureDetector(
              onTap: () => Navigator.pop(context),
              child: SizedBox(
                width: 24 * scaleX,
                height: 24 * scaleY,
                child: SvgPicture.asset(
                  'assets/images/left_arrow.svg',
                  fit: BoxFit.contain,
                ),
              ),
            ),
          ),
          
          // Main illustration - Figma: (0, 198.11)
          Positioned(
            left: 0,
            top: 198.11 * scaleY,
            width: 390 * scaleX,
            height: 321.61 * scaleY,
            child: Center(
              child: SvgPicture.asset(
                'assets/images/guide4_main_illustration.svg',
                width: 390 * scaleX,
                height: 321.61 * scaleY,
                fit: BoxFit.contain,
              ),
            ),
          ),
          
          // Description text - Figma: (54, 543.72)
          Positioned(
            left: 54 * scaleX,
            top: 543.72 * scaleY,
            width: 282 * scaleX,
            child: RichText(
              textAlign: TextAlign.center,
              text: TextSpan(
                style: TextStyle(
                  fontSize: 18 * scaleY,
                  fontWeight: FontWeight.w400,
                  color: Colors.white.withOpacity(0.6),
                  height: 1.56,
                ),
                children: [
                  TextSpan(text: '영상에는 '),
                  TextSpan(
                    text: '전신',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                  TextSpan(text: '이\n'),
                  TextSpan(
                    text: '모두',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                  TextSpan(text: ' 나와야해요'),
                ],
              ),
            ),
          ),
          
          // Page indicator - Figma: (164, 685)
          Positioned(
            left: 164 * scaleX,
            top: 685 * scaleY,
            child: SvgPicture.asset(
              'assets/images/page_indicator.svg',
              width: 62 * scaleX,
              height: 8 * scaleY,
              fit: BoxFit.contain,
            ),
          ),
          
          // Next button - Figma: (20, 730)
          Positioned(
            left: 20 * scaleX,
            top: 730 * scaleY,
            right: 20 * scaleX,
            child: CtaButton(
              text: '다음으로',
              variant: _isButtonActive ? CtaButtonVariant.active : CtaButtonVariant.disabled,
              onPressed: () {
                if (_isButtonActive) {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const PersonalInfoScreen(),
                    ),
                  );
                }
              },
            ),
          ),
        ],
      ),
    );
  }
}
