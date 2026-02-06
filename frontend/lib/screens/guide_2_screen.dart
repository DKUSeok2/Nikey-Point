import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'guide_3_screen.dart';
import 'personal_info_screen.dart';
import '../widgets/cta_button.dart';

/// Guide screen 2 - Video length recommendation
class Guide2Screen extends StatefulWidget {
  const Guide2Screen({super.key});

  @override
  State<Guide2Screen> createState() => _Guide2ScreenState();
}

class _Guide2ScreenState extends State<Guide2Screen> {
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
          // Back button and SKIP - Figma: (0, 59)
          Positioned(
            left: 0,
            top: 59 * scaleY,
            width: 390 * scaleX,
            height: 54 * scaleY,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 20 * scaleX),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Back button
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: SizedBox(
                      width: 24 * scaleX,
                      height: 24 * scaleY,
                      child: SvgPicture.asset(
                        'assets/images/back_icon.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                  ),
                  // SKIP button
                  GestureDetector(
                    onTap: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const PersonalInfoScreen(),
                        ),
                      );
                    },
                    child: Text(
                      'SKIP',
                      style: TextStyle(
                        fontSize: 16 * scaleY,
                        fontWeight: FontWeight.w600,
                        color: Colors.white.withOpacity(0.6),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // Video length card - Figma: (0, 233)
          Positioned(
            left: 0,
            top: 233 * scaleY,
            width: 390 * scaleX,
            height: 260 * scaleY,
            child: Center(
              child: Container(
                width: 266.61 * scaleX,
                height: 195 * scaleY,
                decoration: BoxDecoration(
                  color: const Color(0xFF292929),
                  borderRadius: BorderRadius.circular(22 * scaleX),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.25),
                      blurRadius: 4,
                      offset: const Offset(0, 0),
                    ),
                  ],
                ),
                child: Stack(
                  children: [
                    // Character icon
                    Positioned(
                      left: 78 * scaleX,
                      top: 30 * scaleY,
                      width: 110.81 * scaleX,
                      height: 110.81 * scaleY,
                      child: SvgPicture.asset(
                        'assets/images/character_small.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                    // Play icon and text
                    Positioned(
                      left: 15 * scaleX,
                      bottom: 17 * scaleY,
                      child: Row(
                        children: [
                          SizedBox(
                            width: 37 * scaleX,
                            height: 37 * scaleY,
                            child: SvgPicture.asset(
                              'assets/images/play_icon.svg',
                              fit: BoxFit.contain,
                            ),
                          ),
                          SizedBox(width: 11 * scaleX),
                          Text(
                            '5s - 10s',
                            style: TextStyle(
                              fontSize: 16 * scaleY,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          
          // Description text - Figma: (66, 543)
          Positioned(
            left: 66 * scaleX,
            top: 543 * scaleY,
            width: 260 * scaleX,
            child: RichText(
              textAlign: TextAlign.center,
              text: TextSpan(
                style: TextStyle(
                  fontSize: 18 * scaleY,
                  color: Colors.white.withOpacity(0.6),
                  height: 1.4,
                ),
                children: [
                  TextSpan(
                    text: '영상 길이',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  TextSpan(text: '는 '),
                  TextSpan(
                    text: '5~10초 사이',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  TextSpan(text: '를\n가장 권장해요!'),
                ],
              ),
            ),
          ),
          
          // Page indicator - Figma: (164, 685)
          Positioned(
            left: 164 * scaleX,
            top: 685 * scaleY,
            child: Row(
              children: [
                // Active indicator (first page)
                Container(
                  width: 20 * scaleX,
                  height: 8 * scaleY,
                  decoration: BoxDecoration(
                    color: const Color(0xFF00DCFF),
                    borderRadius: BorderRadius.circular(4 * scaleX),
                  ),
                ),
                SizedBox(width: 6 * scaleX),
                // Inactive indicators
                for (int i = 0; i < 3; i++) ...[
                  Container(
                    width: 8 * scaleX,
                    height: 8 * scaleY,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.3),
                      shape: BoxShape.circle,
                    ),
                  ),
                  if (i < 2) SizedBox(width: 6 * scaleX),
                ],
              ],
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
                      builder: (context) => const Guide3Screen(),
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
