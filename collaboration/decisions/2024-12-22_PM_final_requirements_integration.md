# 최종 요구사항 통합 및 결정서

**발신자**: 중앙 관리자 (PM)  
**수신자**: 뉴스레터 작가, 웹 디자이너/개발자  
**일시**: 2024-12-22  
**주제**: 피드백 검토 완료 및 최종 프로젝트 요구사항 확정

---

## 📋 **요약**

팀 여러분의 전문적이고 깊이 있는 피드백을 바탕으로 프로젝트의 최종 요구사항을 확정했습니다. 

**핵심 원칙**: 사용자 중심의 단순하고 실용적인 웰니스 뉴스레터 서비스 구축

---

## ✅ **피드백 검토 및 결정사항**

### **Writer 피드백 반영 결과**

#### **✅ 채택된 제안사항**

**1. 카테고리 3개로 단순화**
- **기존**: 5개 카테고리 (마음/몸/영양/스파/자연치유)
- **최종**: 3개 카테고리 (마음 웰니스/몸 웰니스/스파 & 힐링)
- **근거**: 사용자 혼란 최소화, 모바일 친화적 인터페이스

**2. 검색 기능 단순화**
- **기존**: 복잡한 필터링 및 정렬 시스템
- **최종**: 기본 키워드 검색 + 카테고리 필터만
- **근거**: 사용자 경험 개선, 개발 복잡성 감소

**3. 수집 소스 우선순위 적용**
- **1차 우선순위**: Mindful Magazine, Yoga Journal, Spa Magazine, Well+Good
- **품질 중심**: 신뢰할 수 있는 소스 우선 수집
- **단계적 확장**: 서비스 안정화 후 추가 소스 검토

**4. 품질 평가 기준 강화**
- **웰니스 특화 기준** 추가: 전문성 검증, 접근성, 실용성
- **안전성 고려**: 의료적 면책 조항, 과장 표현 지양
- **초보자 친화성**: 전문 용어 설명, 포용적 언어 사용

#### **🔄 수정된 제안사항**

**개인화 시스템 범위 조정**
- **Writer 제안**: 단계적 개인화 (기본 → 고급)
- **PM 결정**: Phase 1에서는 지역 기반 + 관심 카테고리만 구현
- **근거**: MVP 완성 우선, 복잡성 최소화

### **Developer 피드백 반영 결과**

#### **✅ 채택된 제안사항**

**1. 기술 스택 확정**
```
Backend: FastAPI + SQLAlchemy + PostgreSQL + Redis
Frontend: HTML5 + Tailwind CSS + Alpine.js + Jinja2
DevOps: Docker + GitHub Actions + Heroku
Testing: pytest + pytest-cov + pytest-asyncio
```

**2. 아키텍처 단순화**
- **마이크로서비스 지향** → **모놀리식 구조**로 시작
- **복잡한 API 설계** → **핵심 6개 엔드포인트**만 구현
- **확장성 고려**: 향후 분리 가능한 구조 유지

**3. 데이터베이스 설계 확정**
- **개발**: SQLite (빠른 프로토타이핑)
- **프로덕션**: PostgreSQL (확장성 및 성능)
- **핵심 테이블**: newsletters, newsletter_sources, categories

**4. TDD 구현 전략**
- **90% 코드 커버리지** 목표
- **핵심 플로우 우선**: 수집 → 저장 → 표시
- **자동화된 테스트**: CI/CD 파이프라인 통합

#### **🔄 조정된 제안사항**

**프론트엔드 기술 스택**
- **Developer 제안**: Alpine.js + Tailwind CSS
- **PM 결정**: 제안 그대로 채택, Vue.js/React는 향후 고려
- **근거**: 쉬운 기술셋 요구사항에 부합, 빠른 개발 가능

**성능 목표 현실화**
- **응답시간**: 200ms → 500ms (현실적 목표)
- **동시 사용자**: 1000명 → 100명 (초기 목표)
- **가용성**: 99.9% → 99% (초기 서비스 수준)

---

## 🎯 **최종 프로젝트 요구사항**

### **핵심 기능 요구사항**

#### **1. 뉴스레터 수집 시스템**
```python
# 필수 구현 기능
- RSS 피드 자동 수집 (4개 우선 소스)
- 중복 제거 (content hash 기반)
- 카테고리 자동 분류 (키워드 기반)
- 품질 점수 자동 계산
- 스케줄링 (1시간마다 수집)
```

#### **2. 웹 인터페이스**
```html
<!-- 단일 페이지 구성 -->
메인 페이지 (/)
├── 헤더 (로고 + 간단한 네비게이션)
├── 검색창 (키워드 + 카테고리 필터)
├── 카테고리별 뉴스레터 (각 카테고리 최신 10개)
└── 푸터 (기본 정보)
```

#### **3. 검색 및 필터링**
- **키워드 검색**: 제목 + 내용 전문 검색
- **카테고리 필터**: 3개 주요 카테고리
- **정렬**: 최신순/인기순 (조회수 기반)
- **페이지네이션**: 20개씩 페이징

#### **4. 뉴스레터 상세 정보**
```json
{
  "title": "뉴스레터 제목",
  "summary": "요약 (200자 이내)",
  "source": "출처명",
  "source_url": "원문 링크",
  "category": "카테고리",
  "tags": ["태그1", "태그2"],
  "quality_score": 4.2,
  "published_date": "2024-12-22"
}
```

### **비기능적 요구사항**

#### **성능 요구사항**
- **응답 시간**: 평균 500ms 이하
- **동시 사용자**: 100명 동시 접속 지원
- **가용성**: 99% 이상 (월 7시간 이하 다운타임)
- **데이터 신선도**: 매시간 새로운 뉴스레터 수집

#### **보안 요구사항**
- **기본 보안**: SQL 인젝션, XSS, CSRF 방지
- **HTTPS**: 모든 통신 암호화
- **API 보안**: Rate limiting (100 req/min per IP)
- **데이터 보호**: 개인정보 수집 최소화

#### **사용성 요구사항**
- **모바일 친화적**: 반응형 디자인 (320px~1920px)
- **접근성**: WCAG 2.1 AA 부분 준수
- **브라우저 호환성**: Chrome, Safari, Firefox 최신 3버전
- **로딩 성능**: 첫 페이지 로딩 3초 이내

---

## 📊 **카테고리 체계 확정**

### **3개 통합 카테고리**

#### **🧘 마음 웰니스 (Mind Wellness)**
**포함 범위**: 
- 명상 및 마인드풀니스
- 정신건강 및 심리치료
- 영성 및 자기계발
- 스트레스 관리

**키워드**:
```python
MIND_WELLNESS_KEYWORDS = [
    '명상', 'meditation', '마인드풀니스', 'mindfulness',
    '정신건강', 'mental health', '심리', 'psychology',
    '스트레스', 'stress', '마음', 'mind', '영성', 'spirituality'
]
```

#### **💪 몸 웰니스 (Body Wellness)**
**포함 범위**:
- 요가 및 피트니스
- 영양 및 다이어트 (기존 영양 카테고리 통합)
- 수면 및 회복
- 신체건강 관리

**키워드**:
```python
BODY_WELLNESS_KEYWORDS = [
    '요가', 'yoga', '피트니스', 'fitness', '운동', 'exercise',
    '영양', 'nutrition', '다이어트', 'diet', '건강식', 'healthy food',
    '수면', 'sleep', '몸', 'body', '건강', 'health'
]
```

#### **🌿 스파 & 힐링 (Spa & Healing)**
**포함 범위**:
- 스파 및 마사지
- 자연치유 (기존 자연치유 카테고리 통합)
- 아로마테라피 및 허브치료
- 미용 및 바디케어

**키워드**:
```python
SPA_HEALING_KEYWORDS = [
    '스파', 'spa', '마사지', 'massage', '아로마', 'aromatherapy',
    '허브', 'herb', '자연치유', 'natural healing', '힐링', 'healing',
    '미용', 'beauty', '바디케어', 'body care', '테라피', 'therapy'
]
```

---

## 🏗️ **시스템 아키텍처 확정**

### **기술 스택 최종 선정**

#### **백엔드**
```yaml
Framework: FastAPI 0.104+
ORM: SQLAlchemy 2.0+
Database: 
  - Development: SQLite
  - Production: PostgreSQL 14+
Cache: Redis 7+
Task Queue: APScheduler (단순 스케줄링)
```

#### **프론트엔드**
```yaml
Base: HTML5 + CSS3
CSS Framework: Tailwind CSS 3.0+
JavaScript: Alpine.js 3.0+ (Vanilla JS 보완)
Template Engine: Jinja2
Icons: Heroicons (SVG)
```

#### **개발 도구**
```yaml
Package Manager: Poetry
Code Quality: Black, isort, mypy
Testing: pytest, pytest-cov, pytest-asyncio
CI/CD: GitHub Actions
Deployment: Heroku (초기) → DigitalOcean (확장 시)
```

### **데이터베이스 스키마 확정**

#### **핵심 테이블**
```sql
-- 뉴스레터 메인 테이블
CREATE TABLE newsletters (
    id UUID PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary VARCHAR(500),
    source_url VARCHAR(1000) UNIQUE,
    content_hash VARCHAR(64) UNIQUE,
    
    primary_category VARCHAR(50) NOT NULL,
    tags TEXT[],
    quality_score DECIMAL(3,2) DEFAULT 0.0,
    view_count INTEGER DEFAULT 0,
    
    published_date TIMESTAMP,
    collected_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 뉴스레터 소스 테이블
CREATE TABLE newsletter_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    type VARCHAR(50) DEFAULT 'rss',
    is_active BOOLEAN DEFAULT true,
    default_category VARCHAR(50),
    last_collected TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **API 엔드포인트 확정**
```python
# 핵심 6개 엔드포인트
GET  /api/v1/newsletters/           # 목록 조회 (필터링 포함)
GET  /api/v1/newsletters/{id}/      # 상세 조회
POST /api/v1/newsletters/collect/   # 수동 수집 (관리자용)
GET  /api/v1/categories/            # 카테고리 목록
GET  /api/v1/search/                # 통합 검색
GET  /api/v1/stats/                 # 기본 통계
```

---

## 📅 **개발 일정 확정**

### **Phase 1: 기반 구축 (Week 1-2)**
```
Week 1:
- 프로젝트 셋업 및 기본 구조
- 데이터베이스 스키마 구현
- 기본 모델 및 API 뼈대

Week 2:
- RSS 수집 엔진 구현
- 카테고리 분류 로직
- 기본 테스트 코드 작성
```

### **Phase 2: 핵심 기능 (Week 3-4)**
```
Week 3:
- 웹 인터페이스 기본 구조
- 뉴스레터 목록/상세 페이지
- 검색 및 필터링 기능

Week 4:
- 뉴스레터 수집 스케줄링
- 품질 평가 시스템
- 관리자 기능
```

### **Phase 3: 완성 및 배포 (Week 5-6)**
```
Week 5:
- 사용자 인터페이스 완성
- 성능 최적화
- 통합 테스트

Week 6:
- 배포 환경 구축
- 문서화 및 최종 검토
- 서비스 런칭
```

---

## 🧪 **테스트 전략 확정**

### **TDD 구현 계획**

#### **단위 테스트 (90% 커버리지 목표)**
```python
# 필수 테스트 모듈
test_models.py          # 데이터 모델 테스트
test_collectors.py      # RSS 수집 로직 테스트
test_categorizer.py     # 카테고리 분류 테스트
test_api.py            # API 엔드포인트 테스트
test_quality.py        # 품질 평가 테스트
```

#### **통합 테스트**
```python
# E2E 핵심 플로우
test_newsletter_lifecycle.py  # 수집 → 저장 → 표시
test_search_functionality.py  # 검색 및 필터링
test_admin_operations.py      # 관리자 기능
```

#### **성능 테스트**
```python
# 성능 임계점 검증
- API 응답 시간 테스트 (500ms 이하)
- 동시 접속 테스트 (100명)
- 대용량 데이터 처리 테스트
```

---

## 📈 **품질 관리 기준**

### **컨텐츠 품질 평가**

#### **자동 평가 (70%)**
```python
def calculate_quality_score(newsletter):
    score = 0.0
    
    # 정확성 (40%)
    score += check_factual_accuracy() * 0.4
    
    # 관련성 (30%)  
    score += check_wellness_relevance() * 0.3
    
    # 완성도 (20%)
    score += check_content_completeness() * 0.2
    
    # 독창성 (10%)
    score += check_uniqueness() * 0.1
    
    return min(5.0, score)
```

#### **수동 검토 (30%)**
- **안전성 검토**: 의학적 주장 검증
- **윤리성 검토**: 과장 광고 및 허위 정보 확인
- **사용자 적합성**: 타겟 사용자에게 유용한지 판단

### **서비스 품질 모니터링**
```python
# 핵심 지표 모니터링
- 응답 시간 (P95 < 500ms)
- 에러율 (< 1%)
- 수집 성공률 (> 95%)
- 사용자 만족도 (향후 설문조사)
```

---

## 🚀 **배포 및 운영 계획**

### **배포 전략**

#### **개발 환경**
```yaml
Local: Docker Compose
- FastAPI + PostgreSQL + Redis
- 실시간 코드 리로딩
- 테스트 데이터 자동 생성
```

#### **프로덕션 환경**
```yaml
Platform: Heroku (초기)
- Heroku Postgres (Standard-0)
- Heroku Redis (Premium-0) 
- GitHub 연동 자동 배포
```

### **CI/CD 파이프라인**
```yaml
# GitHub Actions 워크플로우
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    - 코드 품질 검사 (black, isort, mypy)
    - 단위 테스트 실행 (pytest)
    - 커버리지 검사 (90% 이상)
    
  deploy:
    - Staging 자동 배포 (develop 브랜치)
    - Production 수동 배포 (main 브랜치)
```

### **모니터링 및 알람**
```python
# 기본 모니터링 지표
- 애플리케이션 성능 (응답시간, 에러율)
- 인프라 상태 (CPU, 메모리, 디스크)
- 비즈니스 지표 (수집량, 사용자 활동)

# 알람 조건
- API 응답시간 > 1초
- 에러율 > 5%
- 뉴스레터 수집 실패 > 50%
```

---

## ✅ **성공 기준 및 검수 조건**

### **기능적 성공 기준**
- [ ] **뉴스레터 자동 수집**: 4개 소스에서 정상 수집
- [ ] **카테고리 분류**: 90% 이상 정확도
- [ ] **검색 기능**: 키워드 + 카테고리 필터 정상 작동
- [ ] **웹 인터페이스**: 모든 기능 정상 작동
- [ ] **관리자 기능**: 수동 수집 및 기본 관리 가능

### **비기능적 성공 기준**
- [ ] **성능**: API 응답시간 평균 500ms 이하
- [ ] **안정성**: 99% 이상 가용성 (주간 기준)
- [ ] **사용성**: 모바일/데스크톱 반응형 지원
- [ ] **보안**: 기본 보안 요구사항 충족
- [ ] **코드 품질**: 90% 이상 테스트 커버리지

### **비즈니스 성공 기준**
- [ ] **컨텐츠 품질**: 평균 품질 점수 3.5/5.0 이상
- [ ] **사용자 만족**: 직관적이고 사용하기 쉬운 인터페이스
- [ ] **유지보수성**: 새로운 기능 추가 및 수정 용이
- [ ] **확장성**: 향후 기능 확장 가능한 구조

---

## 📞 **프로젝트 진행 방식**

### **커뮤니케이션**
- **일일 체크인**: 매일 오전 진행상황 공유 (Slack)
- **주간 리뷰**: 매주 수요일 팀 미팅 (30분)
- **문제 해결**: 블로킹 이슈 발생 시 즉시 논의

### **문서화**
- **코드 문서화**: API 문서 자동 생성 (FastAPI)
- **사용자 가이드**: 기본 사용법 README
- **개발자 가이드**: 설치 및 개발 환경 구축 가이드

### **품질 관리**
- **코드 리뷰**: 모든 PR에 대한 리뷰 필수
- **테스트 우선**: 새 기능 개발 시 TDD 준수
- **지속적 개선**: 매주 회고 및 개선점 도출

---

## 🎯 **최종 메시지**

두 분의 전문적인 피드백 덕분에 훨씬 현실적이고 사용자 중심적인 서비스를 설계할 수 있었습니다.

### **핵심 가치**
1. **사용자 중심**: 전문가 관점보다는 실제 사용자 경험 우선
2. **단순함**: 복잡한 기능보다는 핵심 기능의 완성도
3. **품질**: 많은 기능보다는 신뢰할 수 있는 정보
4. **지속가능성**: 유지보수하기 쉬운 구조와 코드

### **개발 철학**
- **점진적 개선**: 완벽한 첫 버전보다는 지속적 개선
- **사용자 피드백**: 가정보다는 실제 사용자 의견 반영
- **기술 실용성**: 최신 기술보다는 검증된 안정적 기술

---

**이제 멋진 웰니스 리트리트 뉴스레터 서비스를 만들어봅시다!**

각자의 전문 분야에서 최고의 결과물을 만들어주시길 기대합니다.

궁금한 점이나 추가 논의가 필요한 사항이 있으시면 언제든 말씀해 주세요.

감사합니다!

**중앙 관리자 (PM)**

---

**문서 승인일**: 2024-12-22  
**프로젝트 개발 시작일**: 2024-12-23  
**예상 완료일**: 2025-01-31