import 'package:flutter/material.dart';
import '../screens/history_screen.dart';

/// 앱 사이드 드로어 (오른쪽에서 슬라이드)
class AppDrawer extends StatelessWidget {
  const AppDrawer({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    final screenWidth = MediaQuery.of(context).size.width;

    final figmaHeight = 844.0;
    final figmaWidth = 390.0;

    final scaleY = screenHeight / figmaHeight;
    final scaleX = screenWidth / figmaWidth;

    // Drawer width from Figma: 240px
    final drawerWidth = 240.0 * scaleX;

    return Container(
      width: drawerWidth,
      height: screenHeight,
      color: const Color(0xFF303336),
      child: SafeArea(
        child: Padding(
          padding: EdgeInsets.symmetric(
            horizontal: 24 * scaleX,
            vertical: 100 * scaleY,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Close button (left arrow)
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  width: 30 * scaleX,
                  height: 30 * scaleY,
                  alignment: Alignment.center,
                  child: Icon(
                    Icons.arrow_back,
                    color: Colors.white,
                    size: 24 * scaleX,
                  ),
                ),
              ),

              SizedBox(height: 14 * scaleY),

              // Menu items
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildMenuItem(
                    context,
                    scaleX,
                    scaleY,
                    '히스토리',
                    () {
                      Navigator.pop(context); // Close drawer
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const HistoryScreen(),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMenuItem(
    BuildContext context,
    double scaleX,
    double scaleY,
    String title,
    VoidCallback onTap,
  ) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        height: 50 * scaleY,
        padding: EdgeInsets.symmetric(vertical: 10 * scaleY),
        child: Text(
          title,
          style: TextStyle(
            fontSize: 16 * scaleY,
            fontWeight: FontWeight.w400,
            fontFamily: 'Pretendard',
            color: Colors.white.withOpacity(0.6),
            letterSpacing: -0.32,
            height: 21 / 16,
          ),
        ),
      ),
    );
  }
}
