# NikePoint Flutter App

AI 기반 러닝 자세 분석 iOS 앱

## 🎯 기능

- ✅ 갤러리에서 영상 선택
- ✅ 키(신장) 입력
- ✅ 백엔드 API 업로드
- ✅ 실시간 처리 상태 확인
- ✅ 33개 신체 키포인트 시각화
- ✅ 프레임별 애니메이션 재생

## 🚀 실행 방법

### 사전 준비

1. Flutter 설치 확인:
```bash
flutter --version
```

2. 백엔드 서버 실행 (필수):
```bash
cd ../backend
docker-compose up -d
```

### iOS 시뮬레이터로 실행

```bash
# 시뮬레이터 열기
open -a Simulator

# 앱 실행
flutter run
```

### 실제 기기로 실행 (카메라 테스트용)

```bash
# 연결된 기기 확인
flutter devices

# 기기에서 실행
flutter run -d <device-id>
```

**주의**: 실제 기기에서는 `lib/config/api_config.dart`의 `baseUrl`을 맥북 IP로 변경해야 합니다:

```dart
// 맥북 IP 확인: ifconfig | grep "inet "
static const String baseUrl = 'http://192.168.0.10:8000'; // 맥북 IP
```

## 📱 화면 구성

### 1. Home Screen
- 앱 소개
- 사용 방법 안내
- 시작 버튼

### 2. Video Picker Screen
- 갤러리에서 영상 선택
- 파일 검증 (100MB 제한)

### 3. Height Input Screen
- 키 입력 (슬라이더 + 텍스트 필드)
- 100-250cm 범위

### 4. Processing Screen
- 업로드 진행률 표시
- 상태 폴링 (2초 간격)
- 처리 단계 표시

### 5. Result Screen
- 키포인트 시각화
- 프레임별 애니메이션
- 통계 정보

## 🏗️ 프로젝트 구조

```
lib/
├── config/
│   ├── api_config.dart          # API 엔드포인트
│   └── theme_config.dart        # 앱 테마
├── models/
│   ├── user_model.dart
│   ├── video_model.dart
│   └── keypoint_model.dart
├── services/
│   └── api_service.dart         # HTTP 클라이언트
├── providers/
│   ├── user_provider.dart       # 사용자 상태
│   └── video_provider.dart      # 영상 상태
├── screens/
│   ├── home_screen.dart
│   ├── video_picker_screen.dart
│   ├── height_input_screen.dart
│   ├── processing_screen.dart
│   └── result_screen.dart
├── widgets/
│   └── keypoint_display_widget.dart
└── main.dart
```

## 🔧 주요 기술

- **State Management**: Provider
- **HTTP Client**: http
- **Image Picker**: image_picker
- **Video Player**: video_player

## 📊 API 연동

### 1. 영상 업로드
```dart
POST /api/video/upload
Content-Type: multipart/form-data
- user_id: String
- file: File
```

### 2. 상태 확인
```dart
GET /api/video/{video_id}/status
Response: { status: "uploaded" | "processing" | "completed" | "failed" }
```

### 3. 키포인트 조회
```dart
GET /api/pose/video/{video_id}/keypoints
Response: { video_id, frame_count, keypoints: [...] }
```

## 🎨 키포인트 시각화

- 33개 MediaPipe 포인트
- 자동 연결선 표시
- 가시성(visibility) 기반 필터링
- 정규화된 좌표 (0-1 범위)

## 🐛 문제 해결

### 앱이 실행되지 않을 때

```bash
# 의존성 재설치
flutter pub get

# 클린 빌드
flutter clean
flutter pub get
flutter run
```

### 백엔드 연결 실패

1. 백엔드 서버 실행 확인:
```bash
curl http://localhost:8000/api/health
```

2. iOS 시뮬레이터에서는 `localhost` 사용
3. 실제 기기에서는 맥북 IP 사용

### 영상 선택 실패

- Info.plist 권한 확인
- iOS 설정에서 앱 권한 확인

## 📝 개발 노트

### 시뮬레이터 제한사항

- ⚠️ 카메라 촬영 기능 미지원
- ✅ 갤러리 선택은 정상 작동
- ✅ 나머지 모든 기능 정상

### 실제 기기 테스트 필요

카메라 촬영 기능을 테스트하려면 실제 아이폰이 필요합니다.

## 🚀 다음 단계 (Phase 2)

1. **카메라 촬영 기능** (camera 패키지)
2. **로그인 시스템** (JWT 인증)
3. **Apple Login** 연동
4. **히스토리 기능** (과거 분석 결과)
5. **프로그레스 트래킹** (진척도 그래프)
6. **AI 피드백 표시** (LLM 생성 텍스트)

## 📄 라이선스

MIT License

---

**NikePoint** - AI 러닝 자세 분석 시스템
