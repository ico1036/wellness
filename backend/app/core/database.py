"""
데이터베이스 설정 및 연결 관리
SQLAlchemy를 사용한 데이터베이스 설정
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator

# 환경변수에서 데이터베이스 URL 가져오기 (기본값: SQLite)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./wellness_newsletter.db"
)

# SQLite 사용 시 특별 설정
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"  # 개발시 SQL 로그
    )
else:
    # PostgreSQL 등 다른 DB 사용 시
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 모델 (models에서 import해서 사용)
Base = declarative_base()


def get_db() -> Generator:
    """
    데이터베이스 세션 의존성
    FastAPI dependency로 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    모든 테이블 생성
    애플리케이션 시작 시 호출
    """
    from app.models.newsletter import Base as NewsletterBase
    NewsletterBase.metadata.create_all(bind=engine)


def drop_tables():
    """
    모든 테이블 삭제
    테스트나 재설정 시 사용
    """
    from app.models.newsletter import Base as NewsletterBase
    NewsletterBase.metadata.drop_all(bind=engine)