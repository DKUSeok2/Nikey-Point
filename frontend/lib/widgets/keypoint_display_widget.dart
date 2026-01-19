import 'package:flutter/material.dart';
import '../models/keypoint_model.dart';

/// Widget to display keypoints visualization
class KeypointDisplayWidget extends StatefulWidget {
  final KeypointResponse keypoints;

  const KeypointDisplayWidget({
    super.key,
    required this.keypoints,
  });

  @override
  State<KeypointDisplayWidget> createState() => _KeypointDisplayWidgetState();
}

class _KeypointDisplayWidgetState extends State<KeypointDisplayWidget> {
  int _currentFrameIndex = 0;
  bool _isPlaying = false;

  @override
  void dispose() {
    super.dispose();
  }

  void _playAnimation() {
    if (_isPlaying) return;
    
    setState(() => _isPlaying = true);
    
    _animateFrames();
  }

  void _animateFrames() async {
    while (_isPlaying && _currentFrameIndex < widget.keypoints.keypoints.length - 1) {
      await Future.delayed(const Duration(milliseconds: 50));
      if (!mounted) return;
      setState(() {
        _currentFrameIndex++;
      });
    }
    
    setState(() => _isPlaying = false);
  }

  void _stopAnimation() {
    setState(() => _isPlaying = false);
  }

  void _resetAnimation() {
    setState(() {
      _currentFrameIndex = 0;
      _isPlaying = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final currentFrame = widget.keypoints.keypoints[_currentFrameIndex];

    return Column(
      children: [
        // Frame info
        Text(
          'Frame ${_currentFrameIndex + 1} / ${widget.keypoints.keypoints.length}',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Text(
          'Time: ${currentFrame.timestamp.toStringAsFixed(2)}s | '
          'Confidence: ${(currentFrame.confidence * 100).toStringAsFixed(1)}%',
          style: TextStyle(color: Colors.grey[600]),
        ),
        const SizedBox(height: 16),
        
        // Keypoint canvas
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(8),
            ),
            child: CustomPaint(
              painter: KeypointPainter(currentFrame),
              child: Container(),
            ),
          ),
        ),
        const SizedBox(height: 16),
        
        // Frame slider
        Row(
          children: [
            Expanded(
              child: Slider(
                value: _currentFrameIndex.toDouble(),
                min: 0,
                max: (widget.keypoints.keypoints.length - 1).toDouble(),
                divisions: widget.keypoints.keypoints.length - 1,
                label: '${_currentFrameIndex + 1}',
                onChanged: (value) {
                  setState(() {
                    _currentFrameIndex = value.toInt();
                  });
                },
              ),
            ),
          ],
        ),
        
        // Controls
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            IconButton(
              onPressed: _resetAnimation,
              icon: const Icon(Icons.skip_previous),
            ),
            IconButton(
              onPressed: _isPlaying ? _stopAnimation : _playAnimation,
              icon: Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
              iconSize: 36,
            ),
          ],
        ),
      ],
    );
  }
}

/// Custom painter for keypoints
class KeypointPainter extends CustomPainter {
  final KeypointFrame frame;

  KeypointPainter(this.frame);

  // MediaPipe pose connections
  static const List<List<String>> connections = [
    // Face
    ['nose', 'left_eye_inner'],
    ['left_eye_inner', 'left_eye'],
    ['left_eye', 'left_eye_outer'],
    ['nose', 'right_eye_inner'],
    ['right_eye_inner', 'right_eye'],
    ['right_eye', 'right_eye_outer'],
    ['left_eye_outer', 'left_ear'],
    ['right_eye_outer', 'right_ear'],
    ['mouth_left', 'mouth_right'],
    
    // Upper body
    ['left_shoulder', 'right_shoulder'],
    ['left_shoulder', 'left_elbow'],
    ['left_elbow', 'left_wrist'],
    ['right_shoulder', 'right_elbow'],
    ['right_elbow', 'right_wrist'],
    ['left_shoulder', 'left_hip'],
    ['right_shoulder', 'right_hip'],
    
    // Lower body
    ['left_hip', 'right_hip'],
    ['left_hip', 'left_knee'],
    ['left_knee', 'left_ankle'],
    ['right_hip', 'right_knee'],
    ['right_knee', 'right_ankle'],
    
    // Feet
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
      ..color = Colors.blue
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final pointPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.fill;

    // Draw connections
    for (final connection in connections) {
      final start = frame.landmarks[connection[0]];
      final end = frame.landmarks[connection[1]];
      
      if (start != null && end != null) {
        // Only draw if both points are visible
        if (start.visibility > 0.5 && end.visibility > 0.5) {
          canvas.drawLine(
            Offset(start.x * size.width, start.y * size.height),
            Offset(end.x * size.width, end.y * size.height),
            paint,
          );
        }
      }
    }

    // Draw points
    frame.landmarks.forEach((name, point) {
      if (point.visibility > 0.5) {
        canvas.drawCircle(
          Offset(point.x * size.width, point.y * size.height),
          4,
          pointPaint,
        );
      }
    });
  }

  @override
  bool shouldRepaint(KeypointPainter oldDelegate) {
    return oldDelegate.frame != frame;
  }
}
