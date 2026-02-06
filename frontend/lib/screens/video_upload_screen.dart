import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'dart:io';
import '../providers/user_provider.dart';
import '../widgets/cta_button.dart';
import 'loading_screen.dart';

/// Video upload selection screen
class VideoUploadScreen extends StatefulWidget {
  const VideoUploadScreen({super.key});

  @override
  State<VideoUploadScreen> createState() => _VideoUploadScreenState();
}

class _VideoUploadScreenState extends State<VideoUploadScreen> {
  final ImagePicker _picker = ImagePicker();

  /// Show video upload bottom sheet
  void _showVideoUploadSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: BoxDecoration(
          color: const Color(0xFF2C2C2E),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Title bar with close button
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '영상 업로드하기',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: Colors.white,
                      letterSpacing: -0.64,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: SizedBox(
                      width: 16,
                      height: 16,
                      child: SvgPicture.asset(
                        'assets/images/close_icon.svg',
                        fit: BoxFit.contain,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            // Option: 촬영하기
            _buildOption(
              iconPath: 'assets/images/camera_icon.svg',
              text: '촬영하기',
              onTap: () {
                Navigator.pop(context);
                _openCamera();
              },
            ),
            
            // Option: 갤러리
            _buildOption(
              iconPath: 'assets/images/gallery_icon.svg',
              text: '갤러리',
              onTap: () {
                Navigator.pop(context);
                _openGallery();
              },
            ),
            
            // Option: 구글 드라이브
            _buildOption(
              iconPath: 'assets/images/drive_icon.svg',
              text: '구글 드라이브',
              onTap: () {
                Navigator.pop(context);
                // TODO: Implement Google Drive integration
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('구글 드라이브 연동은 준비중입니다')),
                );
              },
            ),
            
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildOption({
    required String iconPath,
    required String text,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 13),
        height: 50,
        decoration: BoxDecoration(
          color: const Color(0xFF6C737A).withOpacity(0.3),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            SizedBox(
              width: 18,
              height: 18,
              child: SvgPicture.asset(
                iconPath,
                fit: BoxFit.contain,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              text,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w400,
                color: Colors.white,
                letterSpacing: -0.64,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Open camera to record video
  Future<void> _openCamera() async {
    try {
      final XFile? video = await _picker.pickVideo(
        source: ImageSource.camera,
        maxDuration: const Duration(seconds: 60),
      );
      
      if (video != null && mounted) {
        _navigateToLoading(File(video.path));
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
        _navigateToLoading(File(video.path));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('갤러리 오류: $e')),
        );
      }
    }
  }

  void _navigateToLoading(File videoFile) {
    final userProvider = context.read<UserProvider>();
    
    // Check if user info exists
    if (userProvider.userId == null || userProvider.userHeight == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('사용자 정보를 먼저 입력해주세요')),
      );
      return;
    }
    
    // Navigate to loading screen with user info
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => LoadingScreen(
          videoFile: videoFile,
          userId: userProvider.userId!,
          height: userProvider.userHeight!,
        ),
      ),
    );
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
          // Title - Figma: (20, 127)
          Positioned(
            left: 20 * scaleX,
            top: 127 * scaleY,
            child: Text(
              '원하는 영상을 선택해주세요',
              style: TextStyle(
                fontSize: 20 * scaleY,
                fontWeight: FontWeight.w600,
                color: Colors.white,
                letterSpacing: -0.8,
              ),
            ),
          ),
          
          // Description - Figma: (20, 165)
          Positioned(
            left: 20 * scaleX,
            top: 165 * scaleY,
            right: 20 * scaleX,
            child: Text(
              '영상을 선택하기 전, 모범 영상을 확인하고 업로드하면\n더 좋은 분석을 받을 수 있어요.',
              style: TextStyle(
                fontSize: 14 * scaleY,
                fontWeight: FontWeight.w400,
                color: Colors.white.withOpacity(0.6),
                height: 1.5,
              ),
            ),
          ),
          
          // "영상 선택하기" button
          Positioned(
            left: 20 * scaleX,
            top: 220 * scaleY,
            width: 200 * scaleX,
            child: SizedBox(
              height: 42 * scaleY,
              child: ElevatedButton(
                onPressed: _showVideoUploadSheet,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00DCFF),
                  foregroundColor: const Color(0xFF18191B),
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  alignment: Alignment.centerLeft,
                ),
                child: const Text(
                  '영상 선택하기',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
