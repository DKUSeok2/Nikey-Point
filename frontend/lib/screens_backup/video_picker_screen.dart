import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/user_provider.dart';
import 'loading_screen.dart';

/// Video picker screen - Gallery selection
class VideoPickerScreen extends StatefulWidget {
  const VideoPickerScreen({super.key});

  @override
  State<VideoPickerScreen> createState() => _VideoPickerScreenState();
}

class _VideoPickerScreenState extends State<VideoPickerScreen> {
  final ImagePicker _picker = ImagePicker();
  File? _selectedVideo;
  bool _isLoading = false;

  Future<void> _pickVideoFromGallery() async {
    setState(() => _isLoading = true);
    
    try {
      final XFile? video = await _picker.pickVideo(
        source: ImageSource.gallery,
      );

      if (video != null) {
        setState(() {
          _selectedVideo = File(video.path);
        });
        
        if (mounted) {
          final userProvider = context.read<UserProvider>();
          
          // Check if user info exists
          if (userProvider.userId == null || userProvider.userHeight == null) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('사용자 정보를 먼저 입력해주세요')),
            );
            return;
          }
          
          // Navigate to loading screen with user info
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => LoadingScreen(
                videoFile: _selectedVideo!,
                userId: userProvider.userId!,
                height: userProvider.userHeight!,
              ),
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('영상 선택 실패: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('영상 선택'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                Icons.video_library,
                size: 100,
                color: Theme.of(context).primaryColor,
              ),
              const SizedBox(height: 24),
              
              Text(
                '러닝 영상을 선택하세요',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              
              // Gallery button
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _pickVideoFromGallery,
                icon: const Icon(Icons.photo_library),
                label: const Text('갤러리에서 선택'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
              
              if (_isLoading)
                const Padding(
                  padding: EdgeInsets.only(top: 24.0),
                  child: Center(
                    child: CircularProgressIndicator(),
                  ),
                ),
              
              const SizedBox(height: 32),
              
              // Info
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.info_outline,
                            color: Theme.of(context).primaryColor,
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            '팁',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        '• 전신이 잘 보이는 영상을 선택하세요\n'
                        '• 영상 길이는 3-30초가 적당합니다\n'
                        '• 측면에서 촬영한 영상이 가장 좋습니다\n'
                        '• 최대 파일 크기: 100MB',
                        style: TextStyle(height: 1.5),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
