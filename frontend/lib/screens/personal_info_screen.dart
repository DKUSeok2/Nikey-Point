import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../widgets/cta_button.dart';
import '../providers/user_provider.dart';
import '../providers/video_provider.dart';
import '../services/api_service.dart';
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
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  bool _isButtonEnabled = false;

  @override
  void initState() {
    super.initState();
    // Listen to text changes to enable/disable button
    _nameController.addListener(_updateButtonState);
    _heightController.addListener(_updateButtonState);
  }

  void _updateButtonState() {
    final hasName = _nameController.text.trim().isNotEmpty;
    final hasHeight = _heightController.text.trim().isNotEmpty;
    setState(() {
      _isButtonEnabled = hasName && hasHeight;
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _heightController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    // Validate inputs
    if (_nameController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('이름을 입력해주세요')),
      );
      return;
    }

    if (_heightController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('키를 입력해주세요')),
      );
      return;
    }

    final height = double.tryParse(_heightController.text);
    if (height == null || height < 100 || height > 250) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('키는 100~250cm 사이로 입력해주세요')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Create user in backend
      final response = await _apiService.createUser(
        userName: _nameController.text,
        height: height,
      );

      if (mounted) {
        // Save user info to provider
        final userProvider = context.read<UserProvider>();
        userProvider.setUserInfo(response['id'], height);
        
        // Save user name to VideoProvider (for history display)
        final videoProvider = context.read<VideoProvider>();
        videoProvider.setUserName(_nameController.text);

        // Navigate to video upload screen
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const VideoUploadScreen(),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('오류: $e')),
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
                color: Colors.white.withOpacity(0.1),
                border: Border.all(
                  color: Colors.white.withOpacity(
                    _nameController.text.trim().isNotEmpty ? 0.6 : 0.2,
                  ),
                  width: 1,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: TextField(
                controller: _nameController,
                textAlignVertical: TextAlignVertical.center,
                style: TextStyle(
                  fontSize: 14 * scaleY,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
                decoration: InputDecoration(
                  hintText: '이름을 입력해주세요',
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
                  filled: true,
                  fillColor: Colors.transparent,
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
          
          // Height input field - Figma: (195, 256), width: 130
          Positioned(
            left: 195 * scaleX,
            top: 256 * scaleY,
            width: 130 * scaleX,
            child: Container(
              height: 38 * scaleY,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                border: Border.all(
                  color: Colors.white.withOpacity(
                    _heightController.text.trim().isNotEmpty ? 0.6 : 0.2,
                  ),
                  width: 1,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: TextField(
                controller: _heightController,
                textAlignVertical: TextAlignVertical.center,
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
                  hintText: '키를 입력해주세요',
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
                  filled: true,
                  fillColor: Colors.transparent,
                ),
              ),
            ),
          ),
          
          // CM label - Figma: (339, 266)
          Positioned(
            left: 339 * scaleX,
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
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : CtaButton(
                    text: '다음으로',
                    variant: _isButtonEnabled ? CtaButtonVariant.active : CtaButtonVariant.disabled,
                    onPressed: _isButtonEnabled ? _handleSubmit : null,
                  ),
          ),
        ],
      ),
    );
  }
}
