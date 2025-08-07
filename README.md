# 웰니스 리트리트 뉴스레터

> 단순하고 직관적인 웰니스 뉴스레터 수집 및 웹 서비스

## 🚀 실행 명령어

### 서버 시작
```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 접속 주소
```
http://127.0.0.1:8000/
```

## 🔧 유지보수 명령어

### 수동 뉴스레터 수집
```bash
cd backend
curl -X POST http://127.0.0.1:8000/api/v1/newsletters/collect/ -H "Content-Type: application/json"
```

### 현재 상태 확인
```bash
cd backend
curl -s "http://127.0.0.1:8000/api/v1/newsletters/stats/"
```

### 데이터베이스 정리 (오래된 뉴스레터 삭제)
```bash
cd backend
uv run python fix_collection_system.py
# 메뉴에서 3번 선택
```

### 소스 관리 (활성화/비활성화)
```bash
cd backend
PYTHONPATH=/Users/jwcorp/wellness_cursor/backend uv run python -c "
from app.core.database import get_db
from app.models.newsletter import NewsletterSource

db = next(get_db())
source = db.query(NewsletterSource).filter(NewsletterSource.name == '소스명').first()
if source:
    source.is_active = False  # 비활성화 (True로 하면 활성화)
    db.commit()
    print(f'✅ {source.name} 소스 상태 변경됨')
db.close()
"
```

## 📊 현재 설정

### 카테고리 (3개)
- 🧘 **마음 웰니스**: 명상, 마인드풀니스, 정신건강
- 💪 **몸 웰니스**: 요가, 운동, 영양
- 🌿 **스파 & 힐링**: 스파, 마사지, 자연치유

### 활성 소스 (3개)
- **Mindful Magazine**: https://www.mindful.org/feed/
- **Yoga Journal**: https://www.yogajournal.com/feed/
- **Spa Magazine**: https://www.spamagazine.com/feed/

### 비활성 소스 (1개)
- **Well+Good**: https://www.wellandgood.com/feed/ (HTTP 500 에러로 비활성화)

## ⚡ 문제 해결

### 수집이 안 될 때
```bash
# 1. 소스 상태 확인
cd backend
uv run python fix_collection_system.py
# 메뉴에서 1번 선택

# 2. 문제되는 소스 비활성화
# 위의 "소스 관리" 명령어 사용

# 3. 중복으로 인한 수집 실패시 오래된 데이터 정리
# 위의 "데이터베이스 정리" 명령어 사용
```

### 서버가 안 뜰 때
```bash
cd backend
uv sync  # 의존성 재설치
```

### 페이지가 안 보일 때
- 브라우저에서 `http://127.0.0.1:8000/` 직접 접속
- 모든 다른 URL은 자동으로 메인 페이지로 리다이렉트됨

## 📂 중요 파일 위치

```
wellness_cursor/
├── backend/
│   ├── app/main.py                    # 메인 서버
│   ├── app/services/newsletter_collector.py  # 수집 로직
│   ├── fix_collection_system.py      # 관리 도구
│   └── migrate_categories.py         # 카테고리 마이그레이션
└── frontend/templates/index.html     # 메인 페이지
```

## 🎯 관리자 체크리스트

### 일일 체크
- [ ] 사이트 정상 접속 확인
- [ ] 새 뉴스레터 수집 상태 확인

### 주간 체크  
- [ ] 데이터베이스 용량 확인
- [ ] RSS 소스 정상 작동 확인
- [ ] 오래된 뉴스레터 정리

### 월간 체크
- [ ] 새로운 RSS 소스 추가 검토
- [ ] 품질 낮은 소스 비활성화 검토

---
**마지막 업데이트**: 2025-08-07  
**현재 뉴스레터**: 30개 (3개 카테고리)