"""
웰니스 리트리트 뉴스레터 서비스 메인 애플리케이션
FastAPI 기반 백엔드 서버
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from app.core.config import settings, setup_logging
from app.core.database import create_tables, get_db
from app.api.newsletters import router as newsletters_router
from app.models.newsletter import NewsletterSource
from app.services.newsletter_collector import CollectionScheduler

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# Rate Limiter 설정
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 라이프사이클 관리
    시작시: 데이터베이스 테이블 생성, 기본 데이터 설정
    종료시: 정리 작업
    """
    # 시작시 작업
    logger.info("애플리케이션 시작 중...")
    
    # 데이터베이스 테이블 생성
    create_tables()
    logger.info("데이터베이스 테이블 생성 완료")
    
    # 기본 뉴스레터 소스 설정
    await setup_default_sources()
    
    # 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    logger.info("애플리케이션 시작 완료")
    
    yield
    
    # 종료시 작업
    logger.info("애플리케이션 종료 중...")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="웰니스 리트리트 뉴스레터 수집 및 제공 서비스",
    lifespan=lifespan
)

# Rate Limiter 설정
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

# API 라우터 등록
app.include_router(newsletters_router, prefix=settings.API_PREFIX)


@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def read_root(request: Request, db: Session = Depends(get_db)):
    """메인 페이지"""
    try:
        # 최신 뉴스레터 몇 개 가져오기
        from app.models.newsletter import Newsletter
        recent_newsletters = db.query(Newsletter).filter(
            Newsletter.is_active == True
        ).order_by(Newsletter.collected_date.desc()).limit(6).all()
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "newsletters": recent_newsletters,
                "app_name": settings.APP_NAME
            }
        )
    except Exception as e:
        logger.error(f"메인 페이지 오류: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "페이지를 불러올 수 없습니다"}
        )


@app.get("/newsletters")
async def newsletters_redirect():
    """뉴스레터 목록 페이지 -> 메인 페이지로 리다이렉트 (에이전트 회의 결과)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)


@app.get("/newsletter/{newsletter_id}")
async def newsletter_detail_redirect(newsletter_id: str):
    """뉴스레터 상세 페이지 -> 메인 페이지로 리다이렉트 (에이전트 회의 결과)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/admin")
async def admin_redirect():
    """관리자 페이지 -> 메인 페이지로 리다이렉트 (에이전트 회의 결과: 한 곳에서 모든 기능)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)


async def setup_default_sources():
    """
    기본 뉴스레터 소스 설정
    Writer가 제안한 우선 수집 대상 설정
    """
    default_sources = [
        {
            "name": "Well+Good",
            "url": "https://www.wellandgood.com/feed/",
            "type": "rss",
            "default_category": "mind_wellness",
            "description": "해외 유명 웰니스 플랫폼 Well+Good RSS 피드"
        },
        {
            "name": "Mindful Magazine",
            "url": "https://www.mindful.org/feed/",
            "type": "rss", 
            "default_category": "mind_wellness",
            "description": "명상 및 마인드풀니스 전문 매거진"
        },
        {
            "name": "Yoga Journal",
            "url": "https://www.yogajournal.com/feed/",
            "type": "rss",
            "default_category": "body_wellness", 
            "description": "요가 전문 매거진"
        },
        {
            "name": "Spa Magazine",
            "url": "https://www.spamagazine.com/feed/",
            "type": "rss",
            "default_category": "spa_therapy",
            "description": "스파 및 웰니스 트리트먼트 정보"
        }
    ]
    
    # 데이터베이스 세션 생성
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        for source_data in default_sources:
            # 이미 존재하는지 확인
            existing = db.query(NewsletterSource).filter(
                NewsletterSource.name == source_data["name"]
            ).first()
            
            if not existing:
                source = NewsletterSource(**source_data)
                db.add(source)
                logger.info(f"기본 소스 추가: {source_data['name']}")
        
        db.commit()
        logger.info("기본 뉴스레터 소스 설정 완료")
        
    except Exception as e:
        logger.error(f"기본 소스 설정 오류: {e}")
        db.rollback()
    finally:
        db.close()


# 전역 예외 처리
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 오류 처리"""
    if request.url.path.startswith("/api"):
        return {"error": "API 엔드포인트를 찾을 수 없습니다"}
    
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "app_name": settings.APP_NAME},
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """500 오류 처리"""
    logger.error(f"내부 서버 오류: {exc}")
    
    if request.url.path.startswith("/api"):
        return {"error": "내부 서버 오류가 발생했습니다"}
    
    return templates.TemplateResponse(
        "500.html",
        {"request": request, "app_name": settings.APP_NAME},
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )