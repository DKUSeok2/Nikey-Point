import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';
import 'dart:async';
import '../providers/video_provider.dart';
import '../models/keypoint_model.dart';

/// Result screen with video player and analysis details
class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> with SingleTickerProviderStateMixin {
  VideoPlayerController? _controller;
  int _currentFrameIndex = 0;
  Timer? _frameUpdateTimer;
  bool _isInitialized = false;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    final videoProvider = context.read<VideoProvider>();
    
    if (videoProvider.videoFile == null) {
      setState(() {
        _isInitialized = false;
      });
      return;
    }

    _controller = VideoPlayerController.file(videoProvider.videoFile!);
    
    try {
      await _controller!.initialize();
      setState(() {
        _isInitialized = true;
      });
      
      _startFrameUpdateTimer();
      _controller!.play();
      _controller!.setLooping(true);
    } catch (e) {
      debugPrint('Error initializing video: $e');
    }
  }

  void _startFrameUpdateTimer() {
    _frameUpdateTimer = Timer.periodic(const Duration(milliseconds: 33), (_) {
      if (_controller != null && _controller!.value.isPlaying) {
        final videoProvider = context.read<VideoProvider>();
        if (videoProvider.keypoints == null) return;

        final position = _controller!.value.position;
        final duration = _controller!.value.duration;
        
        if (duration.inMilliseconds > 0) {
          final progress = position.inMilliseconds / duration.inMilliseconds;
          final frameCount = videoProvider.keypoints!.keypoints.length;
          final newFrameIndex = (progress * frameCount).floor().clamp(0, frameCount - 1);
          
          if (newFrameIndex != _currentFrameIndex) {
            setState(() {
              _currentFrameIndex = newFrameIndex;
            });
          }
        }
      }
    });
  }

  @override
  void dispose() {
    _frameUpdateTimer?.cancel();
    _controller?.dispose();
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('분석 결과'),
        leading: IconButton(
          icon: const Icon(Icons.home),
          onPressed: () {
            Navigator.of(context).popUntil((route) => route.isFirst);
          },
        ),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.video_library), text: '영상'),
            Tab(icon: Icon(Icons.analytics), text: '분석'),
          ],
        ),
      ),
      body: Consumer<VideoProvider>(
        builder: (context, videoProvider, child) {
          if (videoProvider.keypoints == null) {
            return const Center(
              child: Text('키포인트 데이터가 없습니다'),
            );
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildVideoTab(videoProvider),
              _buildAnalysisTab(videoProvider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildVideoTab(VideoProvider videoProvider) {
    if (!_isInitialized || _controller == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final keypoints = videoProvider.keypoints!;
    final currentFrame = keypoints.keypoints[_currentFrameIndex];

    return SafeArea(
      child: Column(
        children: [
          // Video player with keypoint overlay
          Expanded(
            child: Container(
              color: Colors.black,
              child: Center(
                child: AspectRatio(
                  aspectRatio: _controller!.value.aspectRatio,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      VideoPlayer(_controller!),
                      CustomPaint(
                        painter: KeypointOverlayPainter(
                          frame: currentFrame,
                          videoSize: _controller!.value.size,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          
          // Controls
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Frame ${_currentFrameIndex + 1} / ${keypoints.keypoints.length}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      'Confidence: ${(currentFrame.confidence * 100).toStringAsFixed(1)}%',
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                VideoProgressIndicator(
                  _controller!,
                  allowScrubbing: true,
                  colors: VideoProgressColors(
                    playedColor: Theme.of(context).primaryColor,
                    backgroundColor: Colors.grey[300]!,
                    bufferedColor: Colors.grey[200]!,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.skip_previous),
                      onPressed: () => _controller!.seekTo(Duration.zero),
                    ),
                    IconButton(
                      icon: Icon(_controller!.value.isPlaying ? Icons.pause : Icons.play_arrow),
                      iconSize: 48,
                      onPressed: () {
                        setState(() {
                          _controller!.value.isPlaying ? _controller!.pause() : _controller!.play();
                        });
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.skip_next),
                      onPressed: () => _controller!.seekTo(_controller!.value.duration),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisTab(VideoProvider videoProvider) {
    final keypoints = videoProvider.keypoints!;
    final avgConfidence = keypoints.keypoints
        .map((k) => k.confidence)
        .reduce((a, b) => a + b) / keypoints.keypoints.length;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Summary card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.analytics, color: Theme.of(context).primaryColor),
                      const SizedBox(width: 8),
                      const Text('분석 완료', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildInfoRow('총 프레임', '${keypoints.frameCount}개'),
                  _buildInfoRow('평균 신뢰도', '${(avgConfidence * 100).toStringAsFixed(1)}%'),
                  _buildInfoRow('감지된 포인트', '33개 신체 랜드마크'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // Analysis placeholder (Phase 2)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.directions_run, color: Theme.of(context).primaryColor),
                      const SizedBox(width: 8),
                      const Text('러닝 분석', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    '다음 분석 항목이 곧 제공됩니다:',
                    style: TextStyle(color: Colors.grey, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  _buildAnalysisItem(Icons.straighten, '평균 보폭', '계산 예정', Colors.blue),
                  _buildAnalysisItem(Icons.trending_down, '착지 각도', '계산 예정', Colors.green),
                  _buildAnalysisItem(Icons.speed, '케이던스 (분당 스텝)', '계산 예정', Colors.orange),
                  _buildAnalysisItem(Icons.swap_vert, '수직 진폭', '계산 예정', Colors.purple),
                  _buildAnalysisItem(Icons.timer, '지면 접촉 시간', '계산 예정', Colors.red),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // Keypoint details
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('키포인트 상세', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  const Text('MediaPipe Pose 모델이 감지한 33개의 신체 랜드마크:'),
                  const SizedBox(height: 12),
                  const Text('• 얼굴: 코, 눈, 귀\n'
                      '• 상체: 어깨, 팔꿈치, 손목, 손\n'
                      '• 하체: 엉덩이, 무릎, 발목, 발'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 32),
          
          // Actions
          ElevatedButton.icon(
            onPressed: () {
              Navigator.of(context).popUntil((route) => route.isFirst);
            },
            icon: const Icon(Icons.home),
            label: const Text('처음으로'),
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(double.infinity, 48),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600])),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildAnalysisItem(IconData icon, String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
                Text(value, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Custom painter for keypoint overlay
class KeypointOverlayPainter extends CustomPainter {
  final KeypointFrame frame;
  final Size videoSize;

  KeypointOverlayPainter({required this.frame, required this.videoSize});

  static const List<List<String>> connections = [
    ['left_shoulder', 'right_shoulder'],
    ['left_shoulder', 'left_elbow'],
    ['left_elbow', 'left_wrist'],
    ['right_shoulder', 'right_elbow'],
    ['right_elbow', 'right_wrist'],
    ['left_shoulder', 'left_hip'],
    ['right_shoulder', 'right_hip'],
    ['left_hip', 'right_hip'],
    ['left_hip', 'left_knee'],
    ['left_knee', 'left_ankle'],
    ['right_hip', 'right_knee'],
    ['right_knee', 'right_ankle'],
    ['left_ankle', 'left_heel'],
    ['left_heel', 'left_foot_index'],
    ['left_ankle', 'left_foot_index'],
    ['right_ankle', 'right_heel'],
    ['right_heel', 'right_foot_index'],
    ['right_ankle', 'right_foot_index'],
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue.withOpacity(0.8)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final pointPaint = Paint()
      ..color = Colors.red.withOpacity(0.8)
      ..style = PaintingStyle.fill;

    final scaleX = size.width / videoSize.width;
    final scaleY = size.height / videoSize.height;

    for (final connection in connections) {
      final start = frame.landmarks[connection[0]];
      final end = frame.landmarks[connection[1]];
      
      if (start != null && end != null && start.visibility > 0.5 && end.visibility > 0.5) {
        canvas.drawLine(
          Offset(start.x * videoSize.width * scaleX, start.y * videoSize.height * scaleY),
          Offset(end.x * videoSize.width * scaleX, end.y * videoSize.height * scaleY),
          paint,
        );
      }
    }

    frame.landmarks.forEach((name, point) {
      if (point.visibility > 0.5) {
        canvas.drawCircle(
          Offset(point.x * videoSize.width * scaleX, point.y * videoSize.height * scaleY),
          5,
          pointPaint,
        );
      }
    });
  }

  @override
  bool shouldRepaint(KeypointOverlayPainter oldDelegate) => oldDelegate.frame != frame;
}
