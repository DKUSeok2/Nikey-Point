# NikePoint Backend

FastAPI 기반 러닝 자세 분석 백엔드 서버

## 🏗️ 아키텍처

이 프로젝트는 **klid-aicb** 디자인 패턴을 따릅니다:
- 기능별 모듈화 (Feature-based modules)
- 각 모듈마다 독립적인 `container.py`, `service.py`, `model.py`, `schema.py`, `router.py`

### 모듈 구조

```
src/
├── core/              # 공통 설정 및 데이터베이스
├── user/              # 사용자 인증 모듈
├── video/             # 영상 업로드/관리 모듈
├── pose_detection/    # MediaPipe 키포인트 추출 모듈
├── pose_analysis/     # 자세 분석 모듈 (Phase 2)
├── feedback/          # AI 피드백 생성 모듈 (Phase 2)
└── workers/           # Celery 백그라운드 작업
```

## 🚀 시작하기

### Docker Compose로 실행 (권장)

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
docker-compose logs -f worker

# 서비스 재시작
docker-compose restart api

# 정리
docker-compose down -v
```

### uv로 로컬 개발

```bash
# 가상 환경 생성 및 활성화
uv venv
source .venv/bin/activate

# 의존성 설치
uv sync

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn src.main:app --reload

# Celery 워커 실행 (별도 터미널)
celery -A src.workers.tasks worker --loglevel=info
```

## 📦 의존성 관리

```bash
# 새 패키지 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>

# 의존성 업데이트
uv lock

# Docker 이미지 재빌드
docker-compose build
```

## 🗄️ 데이터베이스

### 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 되돌리기
alembic downgrade -1

# 마이그레이션 히스토리
alembic history
```

### 직접 접속

```bash
# Docker 컨테이너 내부
docker exec -it nikepoint_db psql -U nikepoint -d nikepoint

# 로컬
psql -h localhost -U nikepoint -d nikepoint
```

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 특정 모듈 테스트
pytest tests/test_user/

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트 함수만
pytest tests/test_user/test_service.py::test_create_user -v
```

## 📊 모니터링

### Celery 모니터링

```bash
# Celery 작업 상태 확인
celery -A src.workers.tasks inspect active

# Celery 워커 상태
celery -A src.workers.tasks inspect stats

# Flower (웹 UI) 실행
celery -A src.workers.tasks flower --port=5555
```

### 로그 확인

```bash
# API 로그
docker-compose logs -f api

# 워커 로그
docker-compose logs -f worker

# 모든 로그
docker-compose logs -f
```

## 🔍 디버깅

### Python 디버거 (pdb)

```python
# 코드에 브레이크포인트 추가
import pdb; pdb.set_trace()
```

### Docker 내부 접속

```bash
# API 컨테이너
docker exec -it nikepoint_api bash

# 워커 컨테이너
docker exec -it nikepoint_worker bash

# DB 컨테이너
docker exec -it nikepoint_db bash
```

## 📝 코드 스타일

```bash
# Ruff로 린팅
ruff check src/

# 자동 수정
ruff check --fix src/

# 포맷팅
ruff format src/
```

## 🌳 Git 워크플로우

```bash
# 기능 브랜치 생성
git checkout -b feature/new-feature

# 커밋 컨벤션
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update readme"
git commit -m "test: add tests"
git commit -m "refactor: improve code"
```

## 📚 API 문서

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

#### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/auth/user/{user_id}` - 사용자 정보

#### 영상
- `POST /api/video/upload` - 영상 업로드
- `GET /api/video/{video_id}/status` - 처리 상태
- `GET /api/video/{video_id}` - 영상 정보
- `GET /api/video/user/{user_id}/videos` - 사용자 영상 목록

#### 자세 분석
- `GET /api/pose/video/{video_id}/keypoints` - 키포인트 조회
- `GET /api/pose/video/{video_id}/frame/{frame_number}` - 특정 프레임

## 🐛 문제 해결

### 일반적인 문제

#### 1. 데이터베이스 연결 실패
```bash
# 컨테이너 상태 확인
docker-compose ps

# DB 헬스체크
docker-compose logs db
```

#### 2. Celery 작업 실패
```bash
# 워커 로그 확인
docker-compose logs worker

# Redis 연결 확인
docker exec -it nikepoint_redis redis-cli ping
```

#### 3. MediaPipe 오류
```bash
# OpenCV 의존성 확인
docker exec -it nikepoint_worker python -c "import cv2; import mediapipe"
```

#### 4. 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8000
lsof -i :5432

# Docker 컨테이너 정리
docker-compose down
```

## 🔐 보안

Phase 1에서는 간단한 인증만 구현되어 있습니다.

**Phase 2에서 추가될 보안 기능:**
- JWT 토큰 인증
- HTTPS/TLS
- 요청 속도 제한 (Rate limiting)
- CORS 정책 강화

## 📈 성능 최적화

### 데이터베이스
- 인덱스 활용 (email, user_id, video_id)
- JSONB 타입으로 효율적인 키포인트 저장
- 배치 insert로 성능 향상

### Celery
- 동시성 설정: `--concurrency=2`
- 작업 시간 제한: 3600초
- 재시도 정책: 최대 3회

### Docker
- Multi-stage 빌드로 이미지 크기 최소화
- 볼륨 마운트로 빠른 개발

## 📞 지원

문제가 발생하면 이슈를 등록해주세요!

---

**Made with FastAPI, MediaPipe, and ❤️**
