import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/video_provider.dart';
import 'result_screen.dart';

/// Processing screen - Upload and wait for results
class ProcessingScreen extends StatefulWidget {
  final File videoFile;
  final String userId;
  final double height;

  const ProcessingScreen({
    super.key,
    required this.videoFile,
    required this.userId,
    required this.height,
  });

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {
  @override
  void initState() {
    super.initState();
    _startProcessing();
  }

  Future<void> _startProcessing() async {
    final videoProvider = context.read<VideoProvider>();
    
    await videoProvider.uploadVideo(
      userId: widget.userId,
      videoFile: widget.videoFile,
      height: widget.height,
    );

    // Navigate to result screen if completed
    if (mounted && videoProvider.state == UploadState.completed) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const ResultScreen(),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('분석 중'),
        automaticallyImplyLeading: false,
      ),
      body: Consumer<VideoProvider>(
        builder: (context, videoProvider, child) {
          if (videoProvider.state == UploadState.error) {
            return _buildErrorState(videoProvider.errorMessage ?? '알 수 없는 오류');
          }

          return _buildProcessingState(videoProvider);
        },
      ),
    );
  }

  Widget _buildProcessingState(VideoProvider videoProvider) {
    String statusText;
    String detailText;

    switch (videoProvider.state) {
      case UploadState.uploading:
        statusText = '업로드 중...';
        detailText = '영상을 서버에 업로드하고 있습니다';
        break;
      case UploadState.processing:
        statusText = '분석 중...';
        detailText = 'MediaPipe로 자세를 분석하고 있습니다\n잠시만 기다려주세요 (약 1-2분)';
        break;
      case UploadState.completed:
        statusText = '완료!';
        detailText = '분석이 완료되었습니다';
        break;
      default:
        statusText = '준비 중...';
        detailText = '처리를 시작합니다';
    }

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Icon
            Icon(
              videoProvider.state == UploadState.completed
                  ? Icons.check_circle
                  : Icons.psychology,
              size: 100,
              color: videoProvider.state == UploadState.completed
                  ? Colors.green
                  : Theme.of(context).primaryColor,
            ),
            const SizedBox(height: 24),
            
            // Status text
            Text(
              statusText,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            
            // Detail text
            Text(
              detailText,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 48),
            
            // Progress indicator
            if (videoProvider.state != UploadState.completed)
              Column(
                children: [
                  LinearProgressIndicator(
                    value: videoProvider.progress,
                    minHeight: 8,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '${(videoProvider.progress * 100).toStringAsFixed(0)}%',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            
            if (videoProvider.state == UploadState.completed)
              const Icon(
                Icons.done_all,
                size: 48,
                color: Colors.green,
              ),
            
            const SizedBox(height: 32),
            
            // Info card
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
                          '처리 과정',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    _buildStep('1. 영상 업로드', videoProvider.progress >= 0.3),
                    _buildStep('2. MediaPipe 자세 추출', videoProvider.progress >= 0.7),
                    _buildStep('3. 키포인트 저장', videoProvider.progress >= 1.0),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStep(String text, bool completed) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        children: [
          Icon(
            completed ? Icons.check_circle : Icons.radio_button_unchecked,
            size: 16,
            color: completed ? Colors.green : Colors.grey,
          ),
          const SizedBox(width: 8),
          Text(
            text,
            style: TextStyle(
              color: completed ? Colors.black : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String errorMessage) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Icon(
              Icons.error_outline,
              size: 100,
              color: Colors.red[400],
            ),
            const SizedBox(height: 24),
            
            Text(
              '오류가 발생했습니다',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.red[700],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            
            Card(
              color: Colors.red[50],
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Text(
                  errorMessage,
                  style: TextStyle(color: Colors.red[900]),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
            const SizedBox(height: 32),
            
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              icon: const Icon(Icons.home),
              label: const Text('처음으로'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.grey[700],
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
