"""
뉴스레터 API 스키마 정의
Pydantic 모델을 사용한 요청/응답 데이터 검증
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PrimaryCategoryEnum(str, Enum):
    """단순화된 3개 주요 카테고리 (에이전트 회의 결과)"""
    MIND_WELLNESS = "mind_wellness"      # 🧘 마음 웰니스: 명상, 마인드풀니스, 정신건강
    BODY_WELLNESS = "body_wellness"      # 💪 몸 웰니스: 요가, 운동, 영양 (기존 nutrition 포함)  
    SPA_THERAPY = "spa_therapy"          # 🌿 스파 & 힐링: 스파, 마사지, 자연치유 (기존 nature_healing 포함)


class DurationEnum(str, Enum):
    """프로그램 기간 분류"""
    SINGLE_DAY = "당일"
    ONE_NIGHT = "1박2일"
    TWO_THREE_DAYS = "2-3일"
    ONE_WEEK = "1주일"
    OVER_WEEK = "1주일이상"


class PriceRangeEnum(str, Enum):
    """가격대 분류"""
    LOW = "저가"
    MEDIUM = "중가"
    HIGH = "고가"
    LUXURY = "럭셔리"


class LocationTypeEnum(str, Enum):
    """위치 유형"""
    URBAN = "도심"
    SUBURBAN = "근교"
    OVERSEAS = "해외"
    NATURE = "자연"


# 기본 스키마들
class LocationBase(BaseModel):
    """위치 정보 기본 스키마"""
    country: Optional[str] = None
    region: Optional[str] = None
    specific: Optional[str] = None


class ProgramInfoBase(BaseModel):
    """프로그램 정보 기본 스키마"""
    duration: Optional[DurationEnum] = None
    price_range: Optional[PriceRangeEnum] = None
    difficulty: Optional[str] = None
    group_size: Optional[str] = None


# 뉴스레터 스키마들
class NewsletterBase(BaseModel):
    """뉴스레터 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=500, description="뉴스레터 제목")
    summary: Optional[str] = Field(None, max_length=300, description="요약 (300자 이내)")
    content: str = Field(..., min_length=10, description="뉴스레터 전체 내용")
    source: str = Field(..., min_length=1, max_length=100, description="소스명")
    source_url: Optional[str] = Field(None, max_length=500, description="원본 URL")
    
    primary_category: Optional[PrimaryCategoryEnum] = None
    secondary_category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(default_factory=list, description="태그 목록")
    
    location: Optional[LocationBase] = None
    program_info: Optional[ProgramInfoBase] = None
    
    published_date: Optional[datetime] = None

    @validator('title')
    def title_must_not_be_empty(cls, v):
        """제목 검증"""
        if not v.strip():
            raise ValueError('제목은 비어있을 수 없습니다')
        return v.strip()

    @validator('content')
    def content_must_have_substance(cls, v):
        """내용 검증"""
        if len(v.strip()) < 10:
            raise ValueError('내용은 최소 10자 이상이어야 합니다')
        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        """태그 검증"""
        if v is None:
            return []
        # 중복 제거 및 정리
        cleaned_tags = list(set([tag.strip() for tag in v if tag.strip()]))
        if len(cleaned_tags) > 10:
            raise ValueError('태그는 최대 10개까지 허용됩니다')
        return cleaned_tags


class NewsletterCreate(NewsletterBase):
    """뉴스레터 생성 스키마"""
    pass


class NewsletterUpdate(BaseModel):
    """뉴스레터 업데이트 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    summary: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = Field(None, min_length=10)
    primary_category: Optional[PrimaryCategoryEnum] = None
    secondary_category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    location: Optional[LocationBase] = None
    program_info: Optional[ProgramInfoBase] = None
    is_active: Optional[bool] = None


class NewsletterInDB(NewsletterBase):
    """데이터베이스 저장용 스키마"""
    id: str
    quality_score: float = 0.0
    is_active: bool = True
    views: int = 0
    content_hash: str
    collected_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NewsletterResponse(BaseModel):
    """API 응답용 뉴스레터 스키마"""
    id: str
    title: str
    summary: Optional[str]
    source: str
    source_url: Optional[str]
    primary_category: Optional[str]
    secondary_category: Optional[str]
    tags: List[str]
    location_display: str  # 프로퍼티로 생성된 값
    duration_display: str
    price_display: str
    quality_score: float
    views: int
    published_date: Optional[datetime]
    collected_date: datetime

    class Config:
        from_attributes = True


class NewsletterListResponse(BaseModel):
    """뉴스레터 목록 응답 스키마"""
    newsletters: List[NewsletterResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class NewsletterDetailResponse(NewsletterResponse):
    """뉴스레터 상세 정보 응답 스키마"""
    content: str  # 전체 내용 포함
    location: Optional[Dict[str, Any]]
    program_info: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# 검색 및 필터링 스키마들
class NewsletterSearchParams(BaseModel):
    """뉴스레터 검색 파라미터"""
    query: Optional[str] = Field(None, min_length=1, max_length=100, description="검색 키워드")
    category: Optional[PrimaryCategoryEnum] = None
    location_type: Optional[LocationTypeEnum] = None
    duration: Optional[DurationEnum] = None
    price_range: Optional[PriceRangeEnum] = None
    source: Optional[str] = None
    
    # 페이징
    page: int = Field(1, ge=1, description="페이지 번호")
    per_page: int = Field(20, ge=1, le=100, description="페이지당 항목 수")
    
    # 정렬
    sort_by: Optional[str] = Field("collected_date", description="정렬 기준")
    sort_order: Optional[str] = Field("desc", description="정렬 순서 (asc/desc)")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """정렬 기준 검증"""
        allowed_fields = [
            'title', 'collected_date', 'published_date', 
            'quality_score', 'views', 'source'
        ]
        if v not in allowed_fields:
            raise ValueError(f'정렬 기준은 {allowed_fields} 중 하나여야 합니다')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        """정렬 순서 검증"""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('정렬 순서는 asc 또는 desc여야 합니다')
        return v.lower()


# 뉴스레터 소스 스키마들
class NewsletterSourceBase(BaseModel):
    """뉴스레터 소스 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    type: str = Field(..., description="수집 방식: rss, web, api")
    default_category: Optional[PrimaryCategoryEnum] = None
    description: Optional[str] = None


class NewsletterSourceCreate(NewsletterSourceBase):
    """뉴스레터 소스 생성 스키마"""
    pass


class NewsletterSourceResponse(NewsletterSourceBase):
    """뉴스레터 소스 응답 스키마"""
    id: int
    is_active: bool
    collection_frequency: str
    last_collected: Optional[datetime]
    quality_weight: float
    created_at: datetime

    class Config:
        from_attributes = True


# 통계 및 대시보드 스키마들
class NewsletterStats(BaseModel):
    """뉴스레터 통계 정보"""
    total_newsletters: int
    active_newsletters: int
    total_sources: int
    active_sources: int
    avg_quality_score: float
    categories_distribution: Dict[str, int]
    recent_collection_count: int  # 최근 24시간 수집량


class QualityMetrics(BaseModel):
    """품질 지표"""
    newsletter_id: str
    has_location: bool
    has_duration: bool
    has_price: bool
    has_program_details: bool
    content_length_score: float
    keyword_relevance_score: float
    total_score: float