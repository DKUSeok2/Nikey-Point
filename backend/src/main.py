"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from .core.config import settings
from .core.database import engine, Base
from .user.router import router as user_router
from .video.router import router as video_router
from .analysis.router import router as analysis_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting NikePoint API...")
    
    # Create database tables
    # NOTE: Alembic을 사용하여 마이그레이션 관리
    # try:
    #     Base.metadata.create_all(bind=engine)
    #     logger.info("Database tables created/verified")
    # except Exception as e:
    #     logger.error(f"Failed to create database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NikePoint API...")


# Create FastAPI application
app = FastAPI(
    title="NikePoint API",
    description="AI 기반 러닝 자세 피드백 시스템",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(user_router)
app.include_router(video_router)
app.include_router(analysis_router)

# Mount static files for overlays
overlays_dir = Path("/app/storage/overlays")
overlays_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage/overlays", StaticFiles(directory=str(overlays_dir)), name="overlays")

# Mount static files for keypoint videos
keypoints_dir = Path("/app/storage/keypoints")
keypoints_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage/keypoints", StaticFiles(directory=str(keypoints_dir)), name="keypoints")


# Health check endpoints
@app.get("/", tags=["health"])
def root():
    """Root endpoint."""
    return {
        "service": "NikePoint API",
        "version": "0.1.0",
        "status": "running",
        "description": "AI 기반 러닝 자세 피드백 시스템",
    }


@app.get("/api/health", tags=["health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "nikepoint-api",
        "database": "connected",
    }


@app.get("/api/info", tags=["info"])
def api_info():
    """API information and available endpoints."""
    return {
        "service": "NikePoint API",
        "version": "0.1.0",
        "endpoints": {
            "user": "/api/user",
            "video": "/api/video",
            "analysis": "/api/analysis",
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
