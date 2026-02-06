import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../providers/user_provider.dart';
import 'loading_screen.dart';

/// Height input screen
class HeightInputScreen extends StatefulWidget {
  final File videoFile;

  const HeightInputScreen({
    super.key,
    required this.videoFile,
  });

  @override
  State<HeightInputScreen> createState() => _HeightInputScreenState();
}

class _HeightInputScreenState extends State<HeightInputScreen> {
  final TextEditingController _heightController = TextEditingController();
  double _height = 170.0; // Default height in cm

  @override
  void initState() {
    super.initState();
    _heightController.text = _height.toStringAsFixed(1);
  }

  @override
  void dispose() {
    _heightController.dispose();
    super.dispose();
  }

  void _onSliderChanged(double value) {
    setState(() {
      _height = value;
      _heightController.text = value.toStringAsFixed(1);
    });
  }

  void _onTextChanged(String value) {
    final height = double.tryParse(value);
    if (height != null && height >= 100 && height <= 250) {
      setState(() {
        _height = height;
      });
    }
  }

  Future<void> _submit() async {
    if (_height < 100 || _height > 250) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('키는 100-250cm 사이여야 합니다')),
      );
      return;
    }

    final userProvider = context.read<UserProvider>();
    
    // Using test user created in backend
    final userId = '5118c0cc-8deb-4338-be5f-8448ef0a0a24';
    userProvider.setUserInfo(userId, _height);

    // Navigate to loading screen
    if (mounted) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => LoadingScreen(
            videoFile: widget.videoFile,
            userId: userId,
            height: _height,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('키 입력'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                Icons.height,
                size: 100,
                color: Theme.of(context).primaryColor,
              ),
              const SizedBox(height: 24),
              
              Text(
                '키를 입력하세요',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                '정확한 자세 분석을 위해 필요합니다',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              
              // Height display
              Center(
                child: Column(
                  children: [
                    Text(
                      '${_height.toStringAsFixed(1)} cm',
                      style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '약 ${(_height / 30.48).toStringAsFixed(1)} ft',
                      style: TextStyle(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              
              // Slider
              Slider(
                value: _height,
                min: 100,
                max: 250,
                divisions: 150,
                label: _height.toStringAsFixed(1),
                onChanged: _onSliderChanged,
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('100cm', style: TextStyle(color: Colors.grey[600])),
                  Text('250cm', style: TextStyle(color: Colors.grey[600])),
                ],
              ),
              const SizedBox(height: 32),
              
              // Text input
              TextField(
                controller: _heightController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,1}')),
                ],
                decoration: const InputDecoration(
                  labelText: '키 (cm)',
                  hintText: '170.0',
                  suffixText: 'cm',
                ),
                onChanged: _onTextChanged,
              ),
              const SizedBox(height: 48),
              
              // Submit button
              ElevatedButton(
                onPressed: _submit,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('업로드 시작'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
