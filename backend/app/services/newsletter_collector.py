"""
뉴스레터 수집 서비스
RSS 피드 및 웹 크롤링을 통한 웰니스 리트리트 뉴스레터 수집
"""
import asyncio
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import aiofiles
import feedparser
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.newsletter import Newsletter, NewsletterSource, ContentQuality
from app.schemas.newsletter import NewsletterCreate, PrimaryCategoryEnum

logger = logging.getLogger(__name__)


class NewsletterCollector:
    """뉴스레터 수집 메인 클래스"""
    
    def __init__(self):
        self.session = None
        self.client = None
        self.collected_count = 0
        self.error_count = 0
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            headers={
                "User-Agent": settings.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.client:
            await self.client.aclose()
    
    def check_robots_txt(self, base_url: str) -> bool:
        """
        robots.txt 확인
        윤리적 크롤링을 위한 robots.txt 준수
        """
        try:
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            rp.read()
            return rp.can_fetch(settings.USER_AGENT, base_url)
        except Exception as e:
            logger.warning(f"robots.txt 확인 실패: {base_url} - {e}")
            return True  # 확인 실패 시 허용으로 처리
    
    async def collect_from_rss(self, source: NewsletterSource, db: Session) -> List[Newsletter]:
        """
        RSS 피드에서 뉴스레터 수집
        """
        collected_newsletters = []
        
        try:
            logger.info(f"RSS 수집 시작: {source.name} ({source.url})")
            
            # RSS 피드 파싱
            feed = feedparser.parse(source.url)
            
            if feed.bozo:
                logger.warning(f"RSS 피드 파싱 오류: {source.name} - {feed.bozo_exception}")
            
            for entry in feed.entries:
                try:
                    # 기본 정보 추출
                    title = entry.get('title', '').strip()
                    summary = entry.get('summary', entry.get('description', '')).strip()
                    content = entry.get('content', [{'value': summary}])[0].get('value', summary)
                    link = entry.get('link', '')
                    
                    # 발행일 처리
                    published_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_date = datetime(*entry.updated_parsed[:6])
                    
                    # 웰니스 리트리트 관련성 검사
                    if not self._is_wellness_retreat_related(title, content):
                        continue
                    
                    # 뉴스레터 객체 생성
                    newsletter_data = NewsletterCreate(
                        title=title,
                        summary=summary[:300] if summary else None,
                        content=content,
                        source=source.name,
                        source_url=link,
                        primary_category=source.default_category,
                        published_date=published_date
                    )
                    
                    newsletter = await self._create_newsletter(newsletter_data, db)
                    if newsletter:
                        collected_newsletters.append(newsletter)
                        self.collected_count += 1
                    
                    # 요청 간격 준수
                    await asyncio.sleep(settings.REQUEST_DELAY)
                    
                except Exception as e:
                    logger.error(f"RSS 항목 처리 오류: {source.name} - {e}")
                    self.error_count += 1
                    continue
            
            # 마지막 수집 시간 업데이트
            source.last_collected = datetime.now()
            db.commit()
            
        except Exception as e:
            logger.error(f"RSS 수집 실패: {source.name} - {e}")
            self.error_count += 1
        
        logger.info(f"RSS 수집 완료: {source.name} - {len(collected_newsletters)}개 수집")
        return collected_newsletters
    
    async def collect_from_web(self, source: NewsletterSource, db: Session) -> List[Newsletter]:
        """
        웹 크롤링을 통한 뉴스레터 수집
        """
        collected_newsletters = []
        
        try:
            # robots.txt 확인
            base_url = f"{urlparse(source.url).scheme}://{urlparse(source.url).netloc}"
            if not self.check_robots_txt(base_url):
                logger.warning(f"robots.txt 거부: {source.name}")
                return collected_newsletters
            
            logger.info(f"웹 크롤링 시작: {source.name} ({source.url})")
            
            # 웹 페이지 요청
            response = await self.client.get(source.url)
            response.raise_for_status()
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스레터 항목 추출 (일반적인 패턴들)
            newsletter_items = self._extract_newsletter_items(soup, source.url)
            
            for item in newsletter_items:
                try:
                    # 웰니스 리트리트 관련성 검사
                    if not self._is_wellness_retreat_related(item['title'], item['content']):
                        continue
                    
                    newsletter_data = NewsletterCreate(
                        title=item['title'],
                        summary=item['summary'],
                        content=item['content'],
                        source=source.name,
                        source_url=item['url'],
                        primary_category=source.default_category,
                        published_date=item.get('published_date')
                    )
                    
                    newsletter = await self._create_newsletter(newsletter_data, db)
                    if newsletter:
                        collected_newsletters.append(newsletter)
                        self.collected_count += 1
                    
                    # 요청 간격 준수
                    await asyncio.sleep(settings.REQUEST_DELAY)
                    
                except Exception as e:
                    logger.error(f"웹 크롤링 항목 처리 오류: {source.name} - {e}")
                    self.error_count += 1
                    continue
            
            # 마지막 수집 시간 업데이트
            source.last_collected = datetime.now()
            db.commit()
            
        except Exception as e:
            logger.error(f"웹 크롤링 실패: {source.name} - {e}")
            self.error_count += 1
        
        logger.info(f"웹 크롤링 완료: {source.name} - {len(collected_newsletters)}개 수집")
        return collected_newsletters
    
    def _extract_newsletter_items(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        웹 페이지에서 뉴스레터 항목 추출
        다양한 사이트 구조에 대응하는 일반적인 추출 로직
        """
        items = []
        
        # 일반적인 뉴스레터/블로그 포스트 셀렉터들
        selectors = [
            'article',
            '.post', '.blog-post', '.news-item',
            '.entry', '.story', '.content-item',
            'h2, h3'  # 제목만 있는 경우
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 1:  # 충분한 항목이 있는 셀렉터 선택
                for element in elements[:10]:  # 최대 10개까지만
                    item = self._extract_item_from_element(element, base_url)
                    if item and len(item['title']) > 10:  # 유효한 제목이 있는 경우만
                        items.append(item)
                break
        
        return items
    
    def _extract_item_from_element(self, element, base_url: str) -> Optional[Dict[str, Any]]:
        """HTML 요소에서 뉴스레터 정보 추출"""
        try:
            # 제목 추출
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)[:100]
            
            if not title:
                return None
            
            # 링크 추출
            link_elem = element.find('a', href=True)
            url = ''
            if link_elem:
                href = link_elem['href']
                url = urljoin(base_url, href) if not href.startswith('http') else href
            
            # 내용 추출
            content = element.get_text(strip=True)
            
            # 요약 생성 (첫 300자)
            summary = content[:300] + '...' if len(content) > 300 else content
            
            return {
                'title': title,
                'content': content,
                'summary': summary,
                'url': url,
                'published_date': None  # 추후 개선 가능
            }
            
        except Exception as e:
            logger.error(f"항목 추출 오류: {e}")
            return None
    
    def _is_wellness_retreat_related(self, title: str, content: str) -> bool:
        """
        웰니스 리트리트 관련성 검사
        Writer가 정의한 키워드를 기반으로 관련성 판단
        """
        # 웰니스 리트리트 관련 키워드들
        wellness_keywords = [
            # 한국어 키워드
            '웰니스', '리트리트', '힐링', '명상', '요가', '스파', '디톡스',
            '마음수련', '심신', '치유', '휴양', '건강여행', '템플스테이',
            '산림욕', '자연치유', '아로마', '마사지', '필라테스',
            
            # 영어 키워드  
            'wellness', 'retreat', 'healing', 'meditation', 'yoga', 'spa', 'detox',
            'mindfulness', 'holistic', 'therapeutic', 'rejuvenation', 'restoration',
            'ayurveda', 'aromatherapy', 'pilates', 'fitness retreat'
        ]
        
        text = f"{title} {content}".lower()
        
        # 키워드 매칭 점수 계산
        keyword_count = sum(1 for keyword in wellness_keywords if keyword.lower() in text)
        
        # 최소 1개 이상의 키워드가 있어야 함
        return keyword_count > 0
    
    async def _create_newsletter(self, newsletter_data: NewsletterCreate, db: Session) -> Optional[Newsletter]:
        """
        뉴스레터 생성 및 중복 검사
        """
        try:
            # 컨텐츠 해시 생성 (중복 검사용)
            content_hash = hashlib.sha256(
                f"{newsletter_data.title}{newsletter_data.content}".encode('utf-8')
            ).hexdigest()
            
            # 중복 검사 (최근 30일 내에서만 체크)
            cutoff_date = datetime.now() - timedelta(days=30)
            existing = db.query(Newsletter).filter(
                Newsletter.content_hash == content_hash,
                Newsletter.collected_date >= cutoff_date
            ).first()
            if existing:
                logger.debug(f"중복 뉴스레터 스킵 (30일 내): {newsletter_data.title[:50]}")
                return None
            
            # 고유 ID 생성
            newsletter_id = f"nl_{int(time.time())}_{hash(newsletter_data.title) % 10000}"
            
            # 카테고리 자동 분류
            category = self._classify_category(newsletter_data.title, newsletter_data.content)
            
            # 위치 정보 추출
            location = self._extract_location(newsletter_data.title, newsletter_data.content)
            
            # 프로그램 정보 추출
            program_info = self._extract_program_info(newsletter_data.title, newsletter_data.content)
            
            # Newsletter 객체 생성
            newsletter = Newsletter(
                id=newsletter_id,
                title=newsletter_data.title,
                summary=newsletter_data.summary,
                content=newsletter_data.content,
                source=newsletter_data.source,
                source_url=newsletter_data.source_url,
                primary_category=category or newsletter_data.primary_category,
                tags=newsletter_data.tags or [],
                location=location,
                program_info=program_info,
                published_date=newsletter_data.published_date,
                content_hash=content_hash,
                quality_score=0.0  # 추후 품질 평가에서 설정
            )
            
            db.add(newsletter)
            
            # 품질 평가 실행
            quality_score = await self._evaluate_quality(newsletter)
            newsletter.quality_score = quality_score
            
            db.commit()
            
            logger.info(f"뉴스레터 생성: {newsletter.title[:50]} (품질: {quality_score:.2f})")
            return newsletter
            
        except Exception as e:
            logger.error(f"뉴스레터 생성 오류: {e}")
            db.rollback()
            return None
    
    def _classify_category(self, title: str, content: str) -> Optional[PrimaryCategoryEnum]:
        """
        단순화된 3개 카테고리 자동 분류 (에이전트 회의 결과)
        """
        text = f"{title} {content}".lower()
        
        # 단순화된 3개 카테고리 키워드 매핑
        category_keywords = {
            PrimaryCategoryEnum.MIND_WELLNESS: [
                # 🧘 마음 웰니스: 명상, 마인드풀니스, 정신건강
                'meditation', 'mindfulness', 'mental', 'mind', 'stress', 'therapy', 'spiritual',
                '명상', '마음', '정신', '스트레스', '심리', '치유', '마인드풀니스'
            ],
            PrimaryCategoryEnum.BODY_WELLNESS: [
                # 💪 몸 웰니스: 요가, 운동, 영양 (기존 nutrition 포함)
                'yoga', 'fitness', 'pilates', 'exercise', 'health', 'nutrition', 'diet', 'detox',
                '요가', '운동', '필라테스', '건강', '영양', '다이어트', '피트니스', '디톡스', '건강식'
            ],
            PrimaryCategoryEnum.SPA_THERAPY: [
                # 🌿 스파 & 힐링: 스파, 마사지, 자연치유 (기존 nature_healing 포함)
                'spa', 'massage', 'aromatherapy', 'healing', 'hot tub', 'relaxation', 'nature', 'forest',
                '스파', '마사지', '아로마', '힐링', '온천', '휴식', '테라피', '자연', '산림욕', '자연치유'
            ]
        }
        
        # 각 카테고리별 점수 계산
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        # 가장 높은 점수의 카테고리 반환
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        # 기본값: mind_wellness
        return PrimaryCategoryEnum.MIND_WELLNESS
    
    def _extract_location(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """컨텐츠에서 위치 정보 추출"""
        # 간단한 위치 추출 로직 (추후 NLP로 개선 가능)
        text = f"{title} {content}".lower()
        
        # 국가 키워드
        countries = {
            '한국': ['한국', '국내', '서울', '부산', '제주'],
            '태국': ['태국', 'thailand', '방콕', '푸켓'],
            '인도네시아': ['발리', 'bali', '인도네시아'],
            '인도': ['인도', 'india', '리시케시'],
            '일본': ['일본', 'japan', '도쿄', '오키나와']
        }
        
        for country, keywords in countries.items():
            if any(keyword in text for keyword in keywords):
                return {
                    'country': country,
                    'region': None,
                    'specific': None
                }
        
        return None
    
    def _extract_program_info(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """프로그램 정보 추출"""
        text = f"{title} {content}".lower()
        program_info = {}
        
        # 기간 추출
        if any(word in text for word in ['당일', '1일', 'day trip']):
            program_info['duration'] = '당일'
        elif any(word in text for word in ['1박', '2일', '1night']):
            program_info['duration'] = '1박2일'
        elif any(word in text for word in ['2박', '3일']):
            program_info['duration'] = '2-3일'
        elif any(word in text for word in ['1주', 'week', '7일']):
            program_info['duration'] = '1주일'
        
        # 가격대 추출 (매우 간단한 로직)
        if any(word in text for word in ['저렴', '합리적', 'affordable']):
            program_info['price_range'] = '저가'
        elif any(word in text for word in ['럭셔리', 'luxury', '프리미엄']):
            program_info['price_range'] = '럭셔리'
        elif any(word in text for word in ['고급', '고가', 'expensive']):
            program_info['price_range'] = '고가'
        
        return program_info if program_info else None
    
    async def _evaluate_quality(self, newsletter: Newsletter) -> float:
        """
        뉴스레터 품질 평가
        Writer가 정의한 품질 기준 적용
        """
        score = 0.0
        max_score = 5.0
        
        # 1. 위치 정보 존재 (1점)
        if newsletter.location:
            score += 1.0
        
        # 2. 프로그램 정보 존재 (1점)
        if newsletter.program_info:
            score += 1.0
        
        # 3. 컨텐츠 길이 (1점)
        content_length = len(newsletter.content)
        if content_length > 1000:
            score += 1.0
        elif content_length > 500:
            score += 0.5
        
        # 4. 제목 품질 (1점)
        if len(newsletter.title) > 10 and any(keyword in newsletter.title.lower() 
                                             for keyword in ['웰니스', 'wellness', '리트리트', 'retreat']):
            score += 1.0
        
        # 5. 요약 존재 (1점)
        if newsletter.summary and len(newsletter.summary) > 50:
            score += 1.0
        
        return min(score / max_score, 1.0)  # 0.0 ~ 1.0 범위로 정규화


class CollectionScheduler:
    """뉴스레터 수집 스케줄러"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def run_collection(self) -> Dict[str, Any]:
        """
        전체 뉴스레터 수집 실행
        """
        start_time = datetime.now()
        total_collected = 0
        total_errors = 0
        
        # 활성화된 소스들 가져오기
        sources = self.db.query(NewsletterSource).filter(
            NewsletterSource.is_active == True
        ).all()
        
        logger.info(f"뉴스레터 수집 시작: {len(sources)}개 소스")
        
        async with NewsletterCollector() as collector:
            for source in sources:
                try:
                    if source.type == 'rss':
                        newsletters = await collector.collect_from_rss(source, self.db)
                    elif source.type == 'web':
                        newsletters = await collector.collect_from_web(source, self.db)
                    else:
                        logger.warning(f"지원하지 않는 소스 타입: {source.type}")
                        continue
                    
                    total_collected += len(newsletters)
                    
                except Exception as e:
                    logger.error(f"소스 수집 오류: {source.name} - {e}")
                    total_errors += 1
            
            total_collected = collector.collected_count
            total_errors = collector.error_count
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': duration,
            'sources_processed': len(sources),
            'newsletters_collected': total_collected,
            'errors': total_errors,
            'success_rate': (len(sources) - total_errors) / len(sources) if sources else 0
        }
        
        logger.info(f"수집 완료: {total_collected}개 수집, {total_errors}개 오류, {duration:.1f}초 소요")
        return result