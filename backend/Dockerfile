# Multi-stage build for smaller image
FROM python:3.11-slim as builder

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 시스템 의존성 (MediaPipe, OpenCV, bcrypt, ffmpeg용)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglx-mesa0 \
    libgl1 \
    libgthread-2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 의존성 설치
COPY pyproject.toml ./
COPY src/ ./src/
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# 런타임 스테이지
FROM python:3.11-slim

# 시스템 의존성 설치 (runtime)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglx-mesa0 \
    libgl1 \
    libgthread-2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# builder에서 설치된 패키지 복사
COPY --from=builder /app/.venv /app/.venv

# 소스 코드 복사
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# 환경 변수
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health', timeout=2)" || exit 1

# 실행 (기본은 API 서버, docker-compose에서 override)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
