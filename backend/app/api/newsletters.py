"""
뉴스레터 API 라우터
웰니스 리트리트 뉴스레터 관련 모든 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from app.core.database import get_db
from app.models.newsletter import Newsletter, NewsletterSource
from app.schemas.newsletter import (
    NewsletterResponse, NewsletterDetailResponse, NewsletterListResponse,
    NewsletterSearchParams, NewsletterStats, NewsletterSourceResponse,
    NewsletterCreate, NewsletterUpdate
)
from app.services.newsletter_collector import CollectionScheduler
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/newsletters", tags=["newsletters"])


@router.get("/", response_model=NewsletterListResponse)
async def get_newsletters(
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    query: Optional[str] = Query(None, min_length=1, max_length=100, description="검색 키워드"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    source: Optional[str] = Query(None, description="소스 필터"),
    sort_by: str = Query("collected_date", description="정렬 기준"),
    sort_order: str = Query("desc", description="정렬 순서 (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    뉴스레터 목록 조회
    검색, 필터링, 페이징, 정렬 지원
    """
    try:
        # 기본 쿼리
        base_query = db.query(Newsletter).filter(Newsletter.is_active == True)
        
        # 검색 조건 적용
        if query:
            base_query = base_query.filter(
                or_(
                    Newsletter.title.contains(query),
                    Newsletter.summary.contains(query),
                    Newsletter.content.contains(query)
                )
            )
        
        # 카테고리 필터
        if category:
            base_query = base_query.filter(Newsletter.primary_category == category)
        
        # 소스 필터
        if source:
            base_query = base_query.filter(Newsletter.source == source)
        
        # 정렬 적용
        sort_column = getattr(Newsletter, sort_by, Newsletter.collected_date)
        if sort_order.lower() == "desc":
            base_query = base_query.order_by(desc(sort_column))
        else:
            base_query = base_query.order_by(asc(sort_column))
        
        # 전체 개수 조회
        total = base_query.count()
        
        # 페이징 적용
        offset = (page - 1) * per_page
        newsletters = base_query.offset(offset).limit(per_page).all()
        
        # 응답 데이터 구성
        newsletter_responses = []
        for newsletter in newsletters:
            newsletter_response = NewsletterResponse(
                id=newsletter.id,
                title=newsletter.title,
                summary=newsletter.summary,
                source=newsletter.source,
                source_url=newsletter.source_url,
                primary_category=newsletter.primary_category,
                secondary_category=newsletter.secondary_category,
                tags=newsletter.tags or [],
                location_display=newsletter.location_display,
                duration_display=newsletter.duration_display,
                price_display=newsletter.price_display,
                quality_score=newsletter.quality_score,
                views=newsletter.views,
                published_date=newsletter.published_date,
                collected_date=newsletter.collected_date
            )
            newsletter_responses.append(newsletter_response)
        
        # 페이지 정보 계산
        total_pages = (total + per_page - 1) // per_page
        
        return NewsletterListResponse(
            newsletters=newsletter_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"뉴스레터 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스레터 목록을 조회할 수 없습니다")


@router.get("/{newsletter_id}", response_model=NewsletterDetailResponse)
async def get_newsletter_detail(
    newsletter_id: str = Path(..., description="뉴스레터 ID"),
    db: Session = Depends(get_db)
):
    """
    뉴스레터 상세 정보 조회
    조회수 증가 포함
    """
    try:
        newsletter = db.query(Newsletter).filter(
            and_(Newsletter.id == newsletter_id, Newsletter.is_active == True)
        ).first()
        
        if not newsletter:
            raise HTTPException(status_code=404, detail="뉴스레터를 찾을 수 없습니다")
        
        # 조회수 증가
        newsletter.views += 1
        db.commit()
        
        return NewsletterDetailResponse(
            id=newsletter.id,
            title=newsletter.title,
            summary=newsletter.summary,
            content=newsletter.content,
            source=newsletter.source,
            source_url=newsletter.source_url,
            primary_category=newsletter.primary_category,
            secondary_category=newsletter.secondary_category,
            tags=newsletter.tags or [],
            location=newsletter.location,
            program_info=newsletter.program_info,
            location_display=newsletter.location_display,
            duration_display=newsletter.duration_display,
            price_display=newsletter.price_display,
            quality_score=newsletter.quality_score,
            views=newsletter.views,
            published_date=newsletter.published_date,
            collected_date=newsletter.collected_date,
            created_at=newsletter.created_at,
            updated_at=newsletter.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스레터 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스레터를 조회할 수 없습니다")


@router.get("/categories/", response_model=List[dict])
async def get_categories(db: Session = Depends(get_db)):
    """
    사용 가능한 카테고리 목록 조회
    카테고리별 뉴스레터 개수 포함
    """
    try:
        from sqlalchemy import func
        
        categories = db.query(
            Newsletter.primary_category,
            func.count(Newsletter.id).label('count')
        ).filter(
            and_(Newsletter.is_active == True, Newsletter.primary_category.isnot(None))
        ).group_by(Newsletter.primary_category).all()
        
        return [
            {
                "category": category.primary_category,
                "count": category.count,
                "display_name": category.primary_category.replace('_', ' ').title()
            }
            for category in categories
        ]
        
    except Exception as e:
        logger.error(f"카테고리 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="카테고리를 조회할 수 없습니다")


@router.get("/sources/", response_model=List[dict])
async def get_sources(db: Session = Depends(get_db)):
    """
    뉴스레터 소스 목록 조회
    소스별 뉴스레터 개수 포함
    """
    try:
        from sqlalchemy import func
        
        sources = db.query(
            Newsletter.source,
            func.count(Newsletter.id).label('count')
        ).filter(Newsletter.is_active == True).group_by(Newsletter.source).all()
        
        return [
            {
                "source": source.source,
                "count": source.count
            }
            for source in sources
        ]
        
    except Exception as e:
        logger.error(f"소스 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="소스를 조회할 수 없습니다")


@router.get("/popular/", response_model=List[NewsletterResponse])
async def get_popular_newsletters(
    limit: int = Query(10, ge=1, le=50, description="조회할 인기 뉴스레터 개수"),
    db: Session = Depends(get_db)
):
    """
    인기 뉴스레터 조회 (조회수 기준)
    """
    try:
        newsletters = db.query(Newsletter).filter(
            Newsletter.is_active == True
        ).order_by(desc(Newsletter.views)).limit(limit).all()
        
        return [
            NewsletterResponse(
                id=newsletter.id,
                title=newsletter.title,
                summary=newsletter.summary,
                source=newsletter.source,
                source_url=newsletter.source_url,
                primary_category=newsletter.primary_category,
                secondary_category=newsletter.secondary_category,
                tags=newsletter.tags or [],
                location_display=newsletter.location_display,
                duration_display=newsletter.duration_display,
                price_display=newsletter.price_display,
                quality_score=newsletter.quality_score,
                views=newsletter.views,
                published_date=newsletter.published_date,
                collected_date=newsletter.collected_date
            )
            for newsletter in newsletters
        ]
        
    except Exception as e:
        logger.error(f"인기 뉴스레터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="인기 뉴스레터를 조회할 수 없습니다")


@router.get("/recent/", response_model=List[NewsletterResponse])
async def get_recent_newsletters(
    limit: int = Query(10, ge=1, le=50, description="조회할 최신 뉴스레터 개수"),
    db: Session = Depends(get_db)
):
    """
    최신 뉴스레터 조회 (수집일 기준)
    """
    try:
        newsletters = db.query(Newsletter).filter(
            Newsletter.is_active == True
        ).order_by(desc(Newsletter.collected_date)).limit(limit).all()
        
        return [
            NewsletterResponse(
                id=newsletter.id,
                title=newsletter.title,
                summary=newsletter.summary,
                source=newsletter.source,
                source_url=newsletter.source_url,
                primary_category=newsletter.primary_category,
                secondary_category=newsletter.secondary_category,
                tags=newsletter.tags or [],
                location_display=newsletter.location_display,
                duration_display=newsletter.duration_display,
                price_display=newsletter.price_display,
                quality_score=newsletter.quality_score,
                views=newsletter.views,
                published_date=newsletter.published_date,
                collected_date=newsletter.collected_date
            )
            for newsletter in newsletters
        ]
        
    except Exception as e:
        logger.error(f"최신 뉴스레터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="최신 뉴스레터를 조회할 수 없습니다")


@router.get("/stats/", response_model=NewsletterStats)
async def get_newsletter_stats(db: Session = Depends(get_db)):
    """
    뉴스레터 통계 정보 조회
    """
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # 기본 통계
        total_newsletters = db.query(func.count(Newsletter.id)).scalar()
        active_newsletters = db.query(func.count(Newsletter.id)).filter(
            Newsletter.is_active == True
        ).scalar()
        
        # 소스 통계
        total_sources = db.query(func.count(NewsletterSource.id)).scalar()
        active_sources = db.query(func.count(NewsletterSource.id)).filter(
            NewsletterSource.is_active == True
        ).scalar()
        
        # 평균 품질 점수
        avg_quality = db.query(func.avg(Newsletter.quality_score)).filter(
            Newsletter.is_active == True
        ).scalar() or 0.0
        
        # 카테고리별 분포
        categories = db.query(
            Newsletter.primary_category,
            func.count(Newsletter.id).label('count')
        ).filter(
            and_(Newsletter.is_active == True, Newsletter.primary_category.isnot(None))
        ).group_by(Newsletter.primary_category).all()
        
        categories_distribution = {
            category.primary_category: category.count
            for category in categories
        }
        
        # 최근 24시간 수집량
        yesterday = datetime.now() - timedelta(days=1)
        recent_count = db.query(func.count(Newsletter.id)).filter(
            Newsletter.collected_date >= yesterday
        ).scalar()
        
        return NewsletterStats(
            total_newsletters=total_newsletters or 0,
            active_newsletters=active_newsletters or 0,
            total_sources=total_sources or 0,
            active_sources=active_sources or 0,
            avg_quality_score=float(avg_quality),
            categories_distribution=categories_distribution,
            recent_collection_count=recent_count or 0
        )
        
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="통계를 조회할 수 없습니다")


# 관리자용 API들
@router.post("/collect/")
async def trigger_collection(db: Session = Depends(get_db)):
    """
    수동 뉴스레터 수집 실행 (관리자용)
    """
    try:
        scheduler = CollectionScheduler(db)
        result = await scheduler.run_collection()
        
        return {
            "message": "뉴스레터 수집이 완료되었습니다",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"수집 실행 오류: {e}")
        raise HTTPException(status_code=500, detail="수집을 실행할 수 없습니다")


@router.put("/{newsletter_id}", response_model=NewsletterDetailResponse)
async def update_newsletter(
    newsletter_id: str,
    newsletter_update: NewsletterUpdate,
    db: Session = Depends(get_db)
):
    """
    뉴스레터 정보 업데이트 (관리자용)
    """
    try:
        newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
        
        if not newsletter:
            raise HTTPException(status_code=404, detail="뉴스레터를 찾을 수 없습니다")
        
        # 업데이트할 필드들 적용
        update_data = newsletter_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(newsletter, field, value)
        
        db.commit()
        db.refresh(newsletter)
        
        return NewsletterDetailResponse.from_orm(newsletter)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스레터 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스레터를 업데이트할 수 없습니다")


@router.delete("/{newsletter_id}")
async def delete_newsletter(
    newsletter_id: str,
    db: Session = Depends(get_db)
):
    """
    뉴스레터 삭제 (관리자용)
    실제로는 is_active를 False로 설정
    """
    try:
        newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
        
        if not newsletter:
            raise HTTPException(status_code=404, detail="뉴스레터를 찾을 수 없습니다")
        
        newsletter.is_active = False
        db.commit()
        
        return {"message": "뉴스레터가 삭제되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스레터 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스레터를 삭제할 수 없습니다")