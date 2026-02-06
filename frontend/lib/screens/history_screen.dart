import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../providers/video_provider.dart';
import '../services/api_service.dart';
import '../models/analysis_model.dart';
import 'result_screen.dart';

/// 히스토리 화면 - 과거 분석 결과 목록
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({Key? key}) : super(key: key);

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _apiService = ApiService();
  List<AnalysisResult>? _historyList;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      // 모든 사용자의 히스토리 가져오기
      final history = await _apiService.getAllHistory(limit: 30);

      setState(() {
        _historyList = history;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = '히스토리를 불러오는 데 실패했습니다: $e';
        _isLoading = false;
      });
    }
  }

  void _openAnalysis(AnalysisResult result) {
    // 선택한 분석 결과를 VideoProvider에 설정
    context.read<VideoProvider>().setAnalysisResult(result);
    
    // 결과 화면으로 이동
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const ResultScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarBrightness: Brightness.dark,
        statusBarIconBrightness: Brightness.light,
      ),
    );

    final screenHeight = MediaQuery.of(context).size.height;
    final screenWidth = MediaQuery.of(context).size.width;

    final figmaHeight = 844.0;
    final figmaWidth = 390.0;

    final scaleY = screenHeight / figmaHeight;
    final scaleX = screenWidth / figmaWidth;

    return Scaffold(
      backgroundColor: const Color(0xFF1C1C1E),
      body: Stack(
        children: [
          // Main content
          Column(
            children: [
              // Top bar - Figma: y=59, height=50
              Container(
                height: (59 + 50) * scaleY,
                padding: EdgeInsets.only(
                  left: 20 * scaleX,
                  right: 20 * scaleX,
                  top: 59 * scaleY,
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Back button
                    GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        width: 24 * scaleX,
                        height: 24 * scaleY,
                        alignment: Alignment.center,
                        child: Icon(
                          Icons.chevron_left,
                          color: Colors.white,
                          size: 28 * scaleX,
                        ),
                      ),
                    ),

                    // Title
                    Text(
                      '히스토리',
                      style: TextStyle(
                        fontSize: 16 * scaleY,
                        fontWeight: FontWeight.w500,
                        fontFamily: 'Pretendard',
                        color: Colors.white,
                      ),
                    ),

                    // Spacer (invisible back button for centering)
                    SizedBox(
                      width: 24 * scaleX,
                      height: 24 * scaleY,
                    ),
                  ],
                ),
              ),

              // History list
              Expanded(
                child: _isLoading
                    ? const Center(
                        child: CircularProgressIndicator(color: Color(0xFF00DCFF)),
                      )
                    : _error != null
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  _error!,
                                  style: TextStyle(
                                    fontSize: 16 * scaleY,
                                    color: Colors.white.withOpacity(0.6),
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                                SizedBox(height: 20 * scaleY),
                                ElevatedButton(
                                  onPressed: _loadHistory,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF00DCFF),
                                  ),
                                  child: const Text('다시 시도'),
                                ),
                              ],
                            ),
                          )
                        : _historyList == null || _historyList!.isEmpty
                            ? Center(
                                child: Text(
                                  '분석 기록이 없습니다',
                                  style: TextStyle(
                                    fontSize: 16 * scaleY,
                                    color: Colors.white.withOpacity(0.6),
                                  ),
                                ),
                              )
                            : ListView.builder(
                                itemCount: _historyList!.length,
                                itemBuilder: (context, index) {
                                  final item = _historyList![index];
                                  return _buildHistoryItem(
                                    scaleX,
                                    scaleY,
                                    item,
                                    index,
                                  );
                                },
                              ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(
    double scaleX,
    double scaleY,
    AnalysisResult result,
    int index,
  ) {
    // Format date: 2025.02.05
    final date = result.createdAt;
    final dateStr = '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}';
    final timeStr = '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';

    // Get user name from AnalysisResult
    final userName = result.userName ?? '사용자';

    return GestureDetector(
      onTap: () => _openAnalysis(result),
      child: Container(
        padding: EdgeInsets.symmetric(
          horizontal: 20 * scaleX,
          vertical: 14 * scaleY,
        ),
        decoration: BoxDecoration(
          color: const Color(0xFF303336).withOpacity(0.2),
          border: Border(
            bottom: BorderSide(
              color: Colors.white.withOpacity(0.3),
              width: 0.5,
            ),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Left: Name and datetime
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  userName,
                  style: TextStyle(
                    fontSize: 16 * scaleY,
                    fontWeight: FontWeight.w500,
                    fontFamily: 'Pretendard',
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 5 * scaleY),
                Row(
                  children: [
                    Text(
                      dateStr,
                      style: TextStyle(
                        fontSize: 14 * scaleY,
                        fontWeight: FontWeight.w400,
                        fontFamily: 'Pretendard',
                        color: Colors.white.withOpacity(0.6),
                      ),
                    ),
                    SizedBox(width: 11 * scaleX),
                    Text(
                      timeStr,
                      style: TextStyle(
                        fontSize: 14 * scaleY,
                        fontWeight: FontWeight.w400,
                        fontFamily: 'Pretendard',
                        color: Colors.white.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ],
            ),

            // Right arrow
            Icon(
              Icons.chevron_right,
              color: Colors.white,
              size: 24 * scaleX,
            ),
          ],
        ),
      ),
    );
  }
}
