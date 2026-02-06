import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../widgets/cta_button.dart';
import 'guide_4_screen.dart';
import 'personal_info_screen.dart';

/// Guide screen 3 - Camera angle recommendation
class Guide3Screen extends StatefulWidget {
  const Guide3Screen({super.key});

  @override
  State<Guide3Screen> createState() => _Guide3ScreenState();
}

class _Guide3ScreenState extends State<Guide3Screen> {
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
          
          // Comparison section - Figma: (46, 266)
          Positioned(
            left: 46 * scaleX,
            top: 266 * scaleY,
            child: Row(
              children: [
                // Wrong example (front view)
                Column(
                  children: [
                    // X icon
                    SizedBox(
                      width: 45.42 * scaleX,
                      height: 45.42 * scaleY,
                      child: SvgPicture.asset(
                        'assets/images/x_icon.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                    SizedBox(height: 9.91 * scaleY),
                    // Front view character
                    SizedBox(
                      width: 129.68 * scaleX,
                      height: 145.89 * scaleY,
                      child: SvgPicture.asset(
                        'assets/images/character_front.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                  ],
                ),
                SizedBox(width: 39 * scaleX),
                // Correct example (side view)
                Column(
                  children: [
                    // Check icon
                    SizedBox(
                      width: 45.42 * scaleX,
                      height: 45.42 * scaleY,
                      child: SvgPicture.asset(
                        'assets/images/check_icon.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                    SizedBox(height: 9.91 * scaleY),
                    // Side view character
                    SizedBox(
                      width: 129.68 * scaleX,
                      height: 145.89 * scaleY,
                      child: SvgPicture.asset(
                        'assets/images/character_side.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                  ],
                ),
              ],
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
                  TextSpan(text: '촬영은 '),
                  TextSpan(
                    text: '측면',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  TextSpan(text: '으로,\n'),
                  TextSpan(
                    text: '한번에 한명만',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  TextSpan(text: ' 촬영해야해요!'),
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
                // Inactive indicator
                Container(
                  width: 8 * scaleX,
                  height: 8 * scaleY,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.3),
                    shape: BoxShape.circle,
                  ),
                ),
                SizedBox(width: 6 * scaleX),
                // Active indicator (second page)
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
                for (int i = 0; i < 2; i++) ...[
                  Container(
                    width: 8 * scaleX,
                    height: 8 * scaleY,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.3),
                      shape: BoxShape.circle,
                    ),
                  ),
                  if (i < 1) SizedBox(width: 6 * scaleX),
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
                      builder: (context) => const Guide4Screen(),
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
