import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/cta_button.dart';
import 'video_upload_screen.dart';

/// Personal information input screen (Name and Height)
class PersonalInfoScreen extends StatefulWidget {
  const PersonalInfoScreen({super.key});

  @override
  State<PersonalInfoScreen> createState() => _PersonalInfoScreenState();
}

class _PersonalInfoScreenState extends State<PersonalInfoScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _heightController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _heightController.dispose();
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
          // Title - Figma: (20, 127)
          Positioned(
            left: 20 * scaleX,
            top: 127 * scaleY,
            child: Text(
              '분석을 위한\n개인정보를 입력해주세요',
              style: TextStyle(
                fontSize: 20 * scaleY,
                fontWeight: FontWeight.w600,
                color: Colors.white,
                height: 1.4,
                letterSpacing: -0.8,
              ),
            ),
          ),
          
          // Name label - Figma: (20, 228)
          Positioned(
            left: 20 * scaleX,
            top: 228 * scaleY,
            child: Text(
              '이름',
              style: TextStyle(
                fontSize: 16 * scaleY,
                fontWeight: FontWeight.w500,
                color: Colors.white.withOpacity(0.7),
              ),
            ),
          ),
          
          // Name input field - Figma: (20, 256), width: 160
          Positioned(
            left: 20 * scaleX,
            top: 256 * scaleY,
            width: 160 * scaleX,
            child: Container(
              height: 38 * scaleY,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                border: Border.all(
                  color: Colors.white.withOpacity(0.1),
                  width: 1,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: TextField(
                controller: _nameController,
                style: TextStyle(
                  fontSize: 14 * scaleY,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
                decoration: InputDecoration(
                  hintText: '이름',
                  hintStyle: TextStyle(
                    fontSize: 14 * scaleY,
                    fontWeight: FontWeight.w500,
                    color: Colors.white.withOpacity(0.2),
                  ),
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 12 * scaleX,
                    vertical: 10 * scaleY,
                  ),
                  border: InputBorder.none,
                ),
              ),
            ),
          ),
          
          // Height label - Figma: (195, 228)
          Positioned(
            left: 195 * scaleX,
            top: 228 * scaleY,
            child: Text(
              '키',
              style: TextStyle(
                fontSize: 16 * scaleY,
                fontWeight: FontWeight.w500,
                color: Colors.white.withOpacity(0.7),
              ),
            ),
          ),
          
          // Height input field - Figma: (195, 256), width: 120
          Positioned(
            left: 195 * scaleX,
            top: 256 * scaleY,
            width: 120 * scaleX,
            child: Container(
              height: 38 * scaleY,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                border: Border.all(
                  color: Colors.white.withOpacity(0.1),
                  width: 1,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: TextField(
                controller: _heightController,
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                ],
                style: TextStyle(
                  fontSize: 14 * scaleY,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
                decoration: InputDecoration(
                  hintText: '이름',
                  hintStyle: TextStyle(
                    fontSize: 14 * scaleY,
                    fontWeight: FontWeight.w500,
                    color: Colors.white.withOpacity(0.2),
                  ),
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 12 * scaleX,
                    vertical: 10 * scaleY,
                  ),
                  border: InputBorder.none,
                ),
              ),
            ),
          ),
          
          // CM label - Figma: (329, 266)
          Positioned(
            left: 329 * scaleX,
            top: 266 * scaleY,
            child: Text(
              'CM',
              style: TextStyle(
                fontSize: 16 * scaleY,
                fontWeight: FontWeight.w500,
                color: Colors.white.withOpacity(0.8),
              ),
            ),
          ),
          
          // Next button - Figma: (20, 730)
          Positioned(
            left: 20 * scaleX,
            top: 730 * scaleY,
            right: 20 * scaleX,
            child: CtaButton(
              text: '다음으로',
              variant: CtaButtonVariant.active,
              onPressed: () {
                // Validate inputs and proceed
                if (_nameController.text.isNotEmpty && 
                    _heightController.text.isNotEmpty) {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const VideoUploadScreen(),
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
