"""
뉴스레터 데이터 모델
Writer의 컨텐츠 스키마 요구사항을 반영한 SQLAlchemy 모델
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class Newsletter(Base):
    """웰니스 리트리트 뉴스레터 메인 모델"""
    __tablename__ = "newsletters"
    
    # 기본 식별자
    id = Column(String, primary_key=True, index=True)  # unique_identifier
    
    # 기본 정보
    title = Column(String(500), nullable=False, index=True)
    summary = Column(String(300))  # 150자 이내 요약 (여유분 포함)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)  # newsletter_name
    source_url = Column(String(500))  # 원본 링크
    
    # 분류 정보 (Writer 요구사항 반영)
    primary_category = Column(String(50), index=True)  # mind_wellness, body_wellness 등
    secondary_category = Column(String(100))  # 세부 카테고리
    tags = Column(JSON)  # ["태그1", "태그2"] 배열
    
    # 위치 정보 (JSON으로 구조화)
    location = Column(JSON)  # {"country": "국가", "region": "지역", "specific": "구체적 위치"}
    
    # 프로그램 정보 (JSON으로 구조화)
    program_info = Column(JSON)  # {"duration": "기간", "price_range": "가격대", ...}
    
    # 메타데이터
    published_date = Column(DateTime, index=True)  # 발행일
    collected_date = Column(DateTime, default=func.now(), index=True)  # 수집일
    quality_score = Column(Float, default=0.0, index=True)  # 품질 점수 (0.0-1.0)
    
    # 운영 정보
    is_active = Column(Boolean, default=True, index=True)  # 활성 상태
    views = Column(Integer, default=0)  # 조회수
    
    # 중복 검사용
    content_hash = Column(String(64), unique=True, index=True)  # 컨텐츠 해시
    
    # 자동 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Newsletter(id={self.id}, title={self.title[:50]}...)>"
    
    @property
    def location_display(self) -> str:
        """위치 정보를 사용자 친화적 문자열로 반환"""
        if not self.location:
            return "위치 미정"
        
        parts = []
        if self.location.get("country"):
            parts.append(self.location["country"])
        if self.location.get("region"):
            parts.append(self.location["region"])
        if self.location.get("specific"):
            parts.append(self.location["specific"])
            
        return " > ".join(parts) if parts else "위치 미정"
    
    @property
    def duration_display(self) -> str:
        """프로그램 기간을 사용자 친화적 문자열로 반환"""
        if not self.program_info or not self.program_info.get("duration"):
            return "기간 미정"
        return self.program_info["duration"]
    
    @property
    def price_display(self) -> str:
        """가격 정보를 사용자 친화적 문자열로 반환"""
        if not self.program_info or not self.program_info.get("price_range"):
            return "가격 미정"
        return self.program_info["price_range"]


class NewsletterSource(Base):
    """뉴스레터 소스 관리 모델"""
    __tablename__ = "newsletter_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 소스명
    url = Column(String(500), nullable=False)  # 소스 URL
    type = Column(String(20), nullable=False)  # 'rss', 'web', 'api'
    
    # 수집 설정
    is_active = Column(Boolean, default=True)
    collection_frequency = Column(String(50), default="daily")  # 'daily', 'weekly', 'hourly'
    last_collected = Column(DateTime)
    
    # 분류 힌트
    default_category = Column(String(50))  # 기본 카테고리
    quality_weight = Column(Float, default=1.0)  # 품질 가중치
    
    # 메타데이터
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NewsletterSource(name={self.name}, type={self.type})>"


class ContentQuality(Base):
    """컨텐츠 품질 평가 로그"""
    __tablename__ = "content_quality"
    
    id = Column(Integer, primary_key=True, index=True)
    newsletter_id = Column(String, nullable=False, index=True)
    
    # 품질 지표들
    has_location = Column(Boolean, default=False)
    has_duration = Column(Boolean, default=False)
    has_price = Column(Boolean, default=False)
    has_program_details = Column(Boolean, default=False)
    content_length_score = Column(Float, default=0.0)  # 컨텐츠 길이 점수
    keyword_relevance_score = Column(Float, default=0.0)  # 키워드 관련성 점수
    
    # 최종 품질 점수
    total_score = Column(Float, default=0.0)
    
    # 평가 시점
    evaluated_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ContentQuality(newsletter_id={self.newsletter_id}, score={self.total_score})>"