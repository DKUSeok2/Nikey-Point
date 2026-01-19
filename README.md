# NikePoint

**AI 기반 러닝 자세 피드백 시스템**

사용자의 러닝 영상을 분석하여 MediaPipe를 통해 자세를 추출하고, AI 기반 피드백을 제공하는 시스템입니다.

## 🎯 프로젝트 개요

- **프론트엔드**: Flutter (iOS - iPhone 15 Pro)
- **백엔드**: FastAPI + PostgreSQL + Celery
- **CV 엔진**: Google MediaPipe Pose
- **패턴**: klid-aicb (기능별 모듈화)

## 📁 프로젝트 구조

```
NikePoint/
├── backend/              # FastAPI 백엔드
│   ├── src/
│   │   ├── core/        # 공통 설정
│   │   ├── user/        # 사용자 인증
│   │   ├── video/       # 영상 업로드/관리
│   │   ├── pose_detection/  # MediaPipe 키포인트 추출
│   │   ├── workers/     # Celery 백그라운드 작업
│   │   └── main.py      # FastAPI 앱
│   ├── tests/           # 테스트
│   ├── alembic/         # 데이터베이스 마이그레이션
│   └── storage/         # 로컬 파일 저장소
│
├── frontend/            # Flutter 앱 ✅ 완성!
│   ├── lib/
│   │   ├── config/      # API & 테마 설정
│   │   ├── models/      # 데이터 모델
│   │   ├── services/    # API 서비스
│   │   ├── providers/   # 상태 관리
│   │   ├── screens/     # 화면 UI
│   │   └── widgets/     # 재사용 위젯
│   └── ios/            # iOS 설정
└── README.md
```

## 🚀 빠른 시작 (Docker)

### 1. 사전 준비

- Docker & Docker Compose 설치
- Git

### 2. 프로젝트 클론

```bash
git clone <repository-url>
cd NikePoint
```

### 3. Docker Compose로 실행

```bash
cd backend
docker-compose up -d
```

이 명령으로 다음 서비스가 시작됩니다:
- PostgreSQL (포트 5432)
- Redis (포트 6379)
- FastAPI 서버 (포트 8000)
- Celery 워커

### 4. API 접속

- **API 문서 (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## 💻 로컬 개발 (uv 사용)

### 1. 사전 준비

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# PostgreSQL & Redis 설치 (또는 Docker로 실행)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev_password postgres:15
docker run -d -p 6379:6379 redis:7
```

### 2. 의존성 설치

```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv sync
```

### 3. 데이터베이스 마이그레이션

```bash
# 마이그레이션 적용
alembic upgrade head
```

### 4. 서버 실행

```bash
# FastAPI 서버
uvicorn src.main:app --reload --port 8000

# Celery 워커 (별도 터미널)
celery -A src.workers.tasks worker --loglevel=info
```

## 📊 데이터베이스 구조

```
User (사용자)
  - id, email, password_hash
  - height (키), weight, age
  
Video (영상)
  - id, user_id
  - file_path, status
  - uploaded_at, processed_at
  
Keypoint (키포인트)
  - id, video_id
  - frame_number, timestamp
  - landmarks (JSONB - 33개 포인트)
```

## 🔌 API 엔드포인트

### 인증

```bash
# 회원가입
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "height": 175.5
}

# 로그인
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 영상 처리

```bash
# 영상 업로드
POST /api/video/upload
Content-Type: multipart/form-data
  - user_id: <user_id>
  - file: <video_file>

# 처리 상태 확인
GET /api/video/{video_id}/status

# 키포인트 조회
GET /api/pose/video/{video_id}/keypoints
```

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 특정 테스트만 실행
pytest tests/test_user/

# 커버리지 포함
pytest --cov=src tests/
```

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **SQLAlchemy**: ORM
- **Alembic**: 데이터베이스 마이그레이션
- **Celery**: 비동기 작업 큐
- **Redis**: 메시지 브로커
- **PostgreSQL**: 데이터베이스
- **MediaPipe**: 자세 추출
- **OpenCV**: 영상 처리

### Development
- **uv**: 빠른 Python 패키지 관리자
- **Docker**: 컨테이너화
- **pytest**: 테스트 프레임워크

## 📈 완료된 기능

### Backend (Phase 1) ✅
- ✅ 사용자 인증 (회원가입/로그인)
- ✅ 영상 업로드 및 저장
- ✅ MediaPipe를 이용한 키포인트 추출
- ✅ Celery 비동기 처리
- ✅ RESTful API
- ✅ Docker 배포 환경
- ✅ 테스트 코드

### Frontend (Flutter) ✅
- ✅ 갤러리에서 영상 선택
- ✅ 키(신장) 입력 UI
- ✅ 백엔드 API 연동
- ✅ 실시간 처리 상태 표시
- ✅ 33개 키포인트 시각화
- ✅ 프레임별 애니메이션
- ✅ Provider 상태 관리

## 🚀 Flutter 앱 실행

### iOS 시뮬레이터

```bash
cd frontend
open -a Simulator
flutter run
```

### 실제 기기 (카메라 테스트용)

```bash
cd frontend
flutter devices
flutter run -d <device-id>
```

**주의**: 실제 기기에서는 `lib/config/api_config.dart`에서 맥북 IP로 변경 필요

## 🚧 Phase 2 계획

1. **카메라 촬영 기능** (camera 패키지)
   - 실시간 촬영
   - 프리뷰 화면

2. **자세 분석 알고리즘**
   - 보폭, 착지각도, 케이던스 계산
   - 수직 진동, 접지 시간 측정

3. **LLM 피드백 생성**
   - OpenAI GPT-4 또는 Claude 통합
   - 자연어 피드백 생성
   - 개선 제안 제공

4. **히스토리 & 통계**
   - 과거 분석 결과 조회
   - 진척도 그래프
   - 개선 추이 표시

5. **인증 강화**
   - JWT 토큰 인증
   - Apple Login 연동

6. **인프라 개선**
   - AWS S3 스토리지
   - CI/CD 파이프라인
   - 프로덕션 배포

## 📝 환경 변수

`.env` 파일 생성 (`.env.example` 참고):

```bash
DATABASE_URL=postgresql://nikepoint:dev_password@localhost:5432/nikepoint
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=./storage/videos
MEDIAPIPE_MODEL_COMPLEXITY=2
```

## 🤝 개발 워크플로우

1. **기능 개발**
   ```bash
   git checkout -b feature/new-feature
   # 코드 작성
   pytest  # 테스트 실행
   git commit -m "feat: add new feature"
   ```

2. **로컬 테스트**
   ```bash
   docker-compose up -d
   # API 테스트
   curl http://localhost:8000/api/health
   ```

3. **배포**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## 📄 라이선스

MIT License

## 👥 기여

이슈와 PR을 환영합니다!

---

**NikePoint** - AI 기반 러닝 자세 분석 시스템
