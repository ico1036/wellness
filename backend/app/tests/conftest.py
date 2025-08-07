"""
테스트 설정 및 공통 픽스처
pytest 설정 및 테스트용 데이터베이스 설정
"""
import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models.newsletter import Newsletter, NewsletterSource, Base


# 테스트용 SQLite 데이터베이스 (메모리)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 데이터베이스 세션"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_db():
    """테스트 데이터베이스 설정"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """테스트용 데이터베이스 세션"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db):
    """테스트용 FastAPI 클라이언트"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_newsletter_data():
    """테스트용 뉴스레터 데이터"""
    return {
        "id": "test_nl_001",
        "title": "발리 웰니스 리트리트 7일 프로그램",
        "summary": "발리에서 진행되는 요가와 명상 중심의 웰니스 리트리트 프로그램입니다.",
        "content": """
        발리의 아름다운 자연 속에서 진행되는 7일간의 웰니스 리트리트 프로그램을 소개합니다.
        
        이 프로그램은 다음과 같은 요소들을 포함합니다:
        - 매일 아침 요가 세션
        - 명상 및 마인드풀니스 연습
        - 건강한 발리 전통 음식
        - 스파 트리트먼트
        - 자연 속 힐링 액티비티
        
        참가자들은 일상의 스트레스에서 벗어나 진정한 휴식과 재생을 경험할 수 있습니다.
        """,
        "source": "Bali Wellness Center",
        "source_url": "https://example.com/bali-retreat",
        "primary_category": "mind_wellness",
        "secondary_category": "요가",
        "tags": ["발리", "요가", "명상", "7일"],
        "location": {
            "country": "인도네시아",
            "region": "발리",
            "specific": "우붓"
        },
        "program_info": {
            "duration": "1주일",
            "price_range": "고가",
            "difficulty": "초급",
            "group_size": "소그룹"
        },
        "quality_score": 0.8,
        "content_hash": "test_hash_001"
    }


@pytest.fixture
def sample_newsletter(db_session, sample_newsletter_data):
    """테스트용 뉴스레터 객체"""
    newsletter = Newsletter(**sample_newsletter_data)
    db_session.add(newsletter)
    db_session.commit()
    db_session.refresh(newsletter)
    return newsletter


@pytest.fixture
def sample_newsletter_source_data():
    """테스트용 뉴스레터 소스 데이터"""
    return {
        "name": "Test Wellness Blog",
        "url": "https://test-wellness.com/feed",
        "type": "rss",
        "default_category": "mind_wellness",
        "description": "테스트용 웰니스 블로그"
    }


@pytest.fixture
def sample_newsletter_source(db_session, sample_newsletter_source_data):
    """테스트용 뉴스레터 소스 객체"""
    source = NewsletterSource(**sample_newsletter_source_data)
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


@pytest.fixture
def multiple_newsletters(db_session):
    """테스트용 다중 뉴스레터 데이터"""
    newsletters_data = [
        {
            "id": "test_nl_002",
            "title": "태국 명상 리트리트",
            "summary": "태국 치앙마이의 전통 사원에서 진행되는 명상 프로그램",
            "content": "태국 치앙마이에서 진행되는 10일간의 명상 리트리트...",
            "source": "Thailand Meditation Center",
            "primary_category": "mind_wellness",
            "tags": ["태국", "명상", "10일"],
            "quality_score": 0.7,
            "content_hash": "test_hash_002"
        },
        {
            "id": "test_nl_003", 
            "title": "제주도 요가 힐링캠프",
            "summary": "제주도 바다를 바라보며 하는 요가와 힐링 프로그램",
            "content": "제주도의 아름다운 해안에서 진행되는 요가 힐링캠프...",
            "source": "Jeju Yoga Center",
            "primary_category": "body_wellness",
            "tags": ["제주도", "요가", "국내"],
            "quality_score": 0.9,
            "content_hash": "test_hash_003"
        },
        {
            "id": "test_nl_004",
            "title": "인도 아유르베다 스파",
            "summary": "인도 전통 아유르베다 치료와 스파 프로그램",
            "content": "인도의 전통적인 아유르베다 치료법을 바탕으로 한 스파...",
            "source": "India Ayurveda Spa",
            "primary_category": "spa_therapy",
            "tags": ["인도", "아유르베다", "스파"],
            "quality_score": 0.6,
            "content_hash": "test_hash_004"
        }
    ]
    
    newsletters = []
    for data in newsletters_data:
        newsletter = Newsletter(**data)
        db_session.add(newsletter)
        newsletters.append(newsletter)
    
    db_session.commit()
    return newsletters


@pytest.fixture
def rss_feed_xml():
    """테스트용 RSS 피드 XML"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Wellness Blog</title>
            <description>테스트용 웰니스 블로그</description>
            <link>https://test-wellness.com</link>
            <item>
                <title>여름 요가 리트리트 in 바다</title>
                <description>여름철 바다에서 진행되는 특별한 요가 리트리트 프로그램입니다.</description>
                <link>https://test-wellness.com/summer-yoga</link>
                <pubDate>Mon, 01 Jul 2024 10:00:00 GMT</pubDate>
            </item>
            <item>
                <title>명상으로 스트레스 해소하기</title>
                <description>일상 속에서 쉽게 할 수 있는 명상 방법을 소개합니다.</description>
                <link>https://test-wellness.com/meditation-stress</link>
                <pubDate>Sun, 30 Jun 2024 15:30:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """


@pytest.fixture
def mock_html_content():
    """테스트용 HTML 컨텐츠"""
    return """
    <html>
        <head><title>Test Wellness Site</title></head>
        <body>
            <div class="main">
                <article>
                    <h2><a href="/article1">발리 스파 리트리트</a></h2>
                    <p>발리에서 진행되는 럭셔리 스파 리트리트 프로그램입니다. 전통 발리 마사지와 현대적인 스파 시설을 결합한 특별한 경험을 제공합니다.</p>
                </article>
                <article>
                    <h3><a href="/article2">홈 요가 가이드</a></h3>
                    <p>집에서 쉽게 따라할 수 있는 요가 동작들을 소개합니다. 초보자도 부담없이 시작할 수 있는 간단한 동작부터 시작해보세요.</p>
                </article>
            </div>
        </body>
    </html>
    """


# 비동기 테스트 설정
@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 설정"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# 로깅 설정 (테스트시 로그 레벨 조정)
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("app").setLevel(logging.WARNING)