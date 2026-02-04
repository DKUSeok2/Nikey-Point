import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/theme_config.dart';
import 'providers/user_provider.dart';
import 'providers/video_provider.dart';
import 'screens/guide_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => UserProvider()),
        ChangeNotifierProvider(create: (_) => VideoProvider()),
      ],
      child: MaterialApp(
        title: 'NikePoint',
        theme: ThemeConfig.lightTheme,
        home: const GuideScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
