import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:image_picker/image_picker.dart';
import 'loading_screen.dart';

/// Video upload selection screen with bottom sheet
class VideoUploadScreen extends StatefulWidget {
  const VideoUploadScreen({super.key});

  @override
  State<VideoUploadScreen> createState() => _VideoUploadScreenState();
}

class _VideoUploadScreenState extends State<VideoUploadScreen> {
  final ImagePicker _picker = ImagePicker();

  /// Open camera to record video
  Future<void> _openCamera() async {
    try {
      final XFile? video = await _picker.pickVideo(
        source: ImageSource.camera,
        maxDuration: const Duration(seconds: 60), // 최대 60초
      );
      
      if (video != null && mounted) {
        // Navigate to loading screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const LoadingScreen(),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('카메라 오류: $e')),
        );
      }
    }
  }

  /// Open gallery to select video
  Future<void> _openGallery() async {
    try {
      final XFile? video = await _picker.pickVideo(
        source: ImageSource.gallery,
      );
      
      if (video != null && mounted) {
        // Navigate to loading screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const LoadingScreen(),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('갤러리 오류: $e')),
        );
      }
    }
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
          // Title text - Figma: (20, 127)
          Positioned(
            left: 20 * scaleX,
            top: 127 * scaleY,
            child: Text(
              '원하는 영상을 선택해주세요',
              style: TextStyle(
                fontSize: 20 * scaleY,
                fontWeight: FontWeight.w600,
                color: Colors.white,
                height: 1.4,
                letterSpacing: -0.8,
              ),
            ),
          ),
          
          // Bottom sheet
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              width: screenWidth,
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                ),
                border: Border(
                  top: BorderSide(
                    color: Color(0xFFF3F4F5),
                    width: 1,
                  ),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Color.fromRGBO(0, 0, 0, 0.25),
                    blurRadius: 30,
                    offset: Offset(0, 0),
                  ),
                ],
              ),
              padding: EdgeInsets.only(
                left: 16 * scaleX,
                right: 16 * scaleX,
                top: 25 * scaleY,
                bottom: 60 * scaleY,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Header with title and close button
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '영상 업로드하기',
                        style: TextStyle(
                          fontSize: 16 * scaleY,
                          fontWeight: FontWeight.w500,
                          color: const Color(0xFF18191B), // Grey/900
                          letterSpacing: -0.64,
                        ),
                      ),
                      GestureDetector(
                        onTap: () => Navigator.pop(context),
                        child: Icon(
                          Icons.close,
                          size: 16 * scaleY,
                          color: const Color(0xFF18191B), // Grey/900
                        ),
                      ),
                    ],
                  ),
                  
                  SizedBox(height: 30 * scaleY),
                  
                  // Options
                  Column(
                    children: [
                      // 촬영하기 (Camera)
                      _buildOptionButton(
                        icon: 'assets/images/camera_icon.svg',
                        label: '촬영하기',
                        onTap: _openCamera,
                        scaleX: scaleX,
                        scaleY: scaleY,
                        isRotated: true,
                      ),
                      
                      SizedBox(height: 10 * scaleY),
                      
                      // 갤러리
                      _buildOptionButton(
                        icon: 'assets/images/gallery_icon.svg',
                        label: '갤러리',
                        onTap: _openGallery,
                        scaleX: scaleX,
                        scaleY: scaleY,
                      ),
                      
                      SizedBox(height: 10 * scaleY),
                      
                      // 구글 드라이브
                      _buildOptionButton(
                        icon: 'assets/images/gallery_icon.svg',
                        label: '구글 드라이브',
                        onTap: () {
                          // TODO: Open Google Drive
                        },
                        scaleX: scaleX,
                        scaleY: scaleY,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOptionButton({
    required String icon,
    required String label,
    required VoidCallback onTap,
    required double scaleX,
    required double scaleY,
    bool isRotated = false,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 358 * scaleX,
        height: 50 * scaleY,
        padding: EdgeInsets.symmetric(
          horizontal: 15 * scaleX,
          vertical: 13 * scaleY,
        ),
        decoration: BoxDecoration(
          color: const Color(0xFFF3F4F5), // Grey/100
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Transform.rotate(
              angle: isRotated ? 3.14159 : 0, // 180 degrees for camera icon
              child: SvgPicture.asset(
                icon,
                width: 20 * scaleX,
                height: 20 * scaleY,
              ),
            ),
            SizedBox(width: 8 * scaleX),
            Text(
              label,
              style: TextStyle(
                fontSize: 16 * scaleY,
                fontWeight: FontWeight.w400,
                color: const Color(0xFF18191B), // Grey/900
                letterSpacing: -0.64,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
