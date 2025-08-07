"""
애플리케이션 설정
환경변수 기반 설정 관리
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 기본 애플리케이션 설정
    APP_NAME: str = "웰니스 리트리트 뉴스레터"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./wellness_newsletter.db")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"
    
    # API 설정
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # 보안 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "wellness-newsletter-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 뉴스레터 수집 설정
    COLLECTION_ENABLED: bool = os.getenv("COLLECTION_ENABLED", "true").lower() == "true"
    COLLECTION_INTERVAL_HOURS: int = int(os.getenv("COLLECTION_INTERVAL_HOURS", "24"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))  # 50KB
    
    # 품질 관리 설정
    MIN_QUALITY_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", "0.3"))
    DEFAULT_QUALITY_WEIGHT: float = 1.0
    
    # 페이징 설정
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/wellness_newsletter.log")
    
    # 웹 크롤링 설정
    USER_AGENT: str = "WellnessNewsletterBot/1.0 (+https://wellness-newsletter.example.com/bot)"
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "1.0"))  # 요청 간격 (초)
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 요청 타임아웃 (초)
    
    # RSS 피드 설정
    RSS_TIMEOUT: int = int(os.getenv("RSS_TIMEOUT", "30"))
    RSS_USER_AGENT: str = "WellnessNewsletterRSSBot/1.0"
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# 전역 설정 인스턴스
settings = Settings()


# 개발 환경 설정
class DevelopmentSettings(Settings):
    """개발 환경 설정"""
    DEBUG: bool = True
    SQL_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"


# 프로덕션 환경 설정
class ProductionSettings(Settings):
    """프로덕션 환경 설정"""
    DEBUG: bool = False
    SQL_ECHO: bool = False
    LOG_LEVEL: str = "WARNING"


def get_settings() -> Settings:
    """
    환경에 따른 설정 반환
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


# 로깅 설정
import logging
import os

def setup_logging():
    """로깅 설정 초기화"""
    # 로그 디렉토리 생성
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로깅 포맷 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 기본 로거 설정
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        handlers=[
            logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)