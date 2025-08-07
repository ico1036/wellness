#!/usr/bin/env python3
"""
뉴스레터 수집 시스템 수정 스크립트
중복 체크 로직 개선 및 강제 수집 옵션 추가
"""
import sys
sys.path.append('/Users/jwcorp/wellness_cursor/backend')

from sqlalchemy.orm import Session
from app.core.database import get_db, engine, Base
from app.models.newsletter import Newsletter, NewsletterSource
from datetime import datetime, timedelta

def show_current_status():
    """현재 뉴스레터 상태 표시"""
    print("📊 현재 뉴스레터 수집 상태")
    print("="*50)
    
    db = next(get_db())
    try:
        total = db.query(Newsletter).count()
        print(f"총 뉴스레터: {total}개")
        
        # 소스별 개수
        sources = db.query(NewsletterSource).all()
        for source in sources:
            count = db.query(Newsletter).filter(Newsletter.source == source.name).count()
            status = "✅" if source.is_active else "❌"
            print(f"  {status} {source.name}: {count}개")
            
        # 최근 수집된 뉴스레터
        recent = db.query(Newsletter).order_by(Newsletter.collected_date.desc()).limit(5).all()
        print(f"\n📰 최근 수집된 뉴스레터 5개:")
        for i, nl in enumerate(recent):
            date_str = nl.collected_date.strftime('%Y-%m-%d %H:%M') if nl.collected_date else 'Unknown'
            print(f"  {i+1}. {nl.title[:60]}... ({date_str})")
            
    finally:
        db.close()

def clear_all_newsletters():
    """모든 뉴스레터 삭제 (테스트용)"""
    print("\n⚠️ 모든 뉴스레터 삭제")
    print("="*50)
    
    response = input("정말로 모든 뉴스레터를 삭제하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ 삭제 취소됨")
        return
        
    db = next(get_db())
    try:
        count = db.query(Newsletter).count()
        db.query(Newsletter).delete()
        db.commit()
        print(f"✅ {count}개 뉴스레터가 삭제되었습니다")
    finally:
        db.close()

def clear_old_newsletters(days=7):
    """오래된 뉴스레터만 삭제"""
    print(f"\n🗑️ {days}일 이전 뉴스레터 삭제")
    print("="*50)
    
    db = next(get_db())
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        old_newsletters = db.query(Newsletter).filter(
            Newsletter.collected_date < cutoff_date
        ).all()
        
        print(f"삭제 대상: {len(old_newsletters)}개")
        
        if len(old_newsletters) > 0:
            response = input(f"{days}일 이전 뉴스레터 {len(old_newsletters)}개를 삭제하시겠습니까? (yes/no): ")
            if response.lower() == 'yes':
                db.query(Newsletter).filter(Newsletter.collected_date < cutoff_date).delete()
                db.commit()
                print(f"✅ {len(old_newsletters)}개 뉴스레터가 삭제되었습니다")
            else:
                print("❌ 삭제 취소됨")
        else:
            print("삭제할 오래된 뉴스레터가 없습니다")
            
    finally:
        db.close()

def fix_wellandgood_source():
    """Well+Good 소스 URL 수정"""
    print("\n🔧 Well+Good 소스 수정")
    print("="*50)
    
    db = next(get_db())
    try:
        source = db.query(NewsletterSource).filter(NewsletterSource.name == "Well+Good").first()
        if source:
            # HTTP 500 에러가 나는 URL을 대체 URL로 변경
            new_urls = [
                "https://feeds.feedburner.com/wellandgood",  # 대체 URL 1
                "https://www.wellandgood.com/rss",  # 대체 URL 2
            ]
            
            print(f"현재 URL: {source.url}")
            print("새로운 URL 옵션:")
            for i, url in enumerate(new_urls):
                print(f"  {i+1}. {url}")
            
            # 일단 소스를 비활성화
            source.is_active = False
            db.commit()
            print("⚠️ Well+Good 소스를 일시적으로 비활성화했습니다")
        else:
            print("❌ Well+Good 소스를 찾을 수 없습니다")
    finally:
        db.close()

def improve_duplicate_check():
    """중복 체크 로직 개선 제안"""
    print("\n💡 중복 체크 로직 개선 제안")
    print("="*50)
    print("""
현재 문제: 모든 뉴스레터가 중복으로 판단되어 새로운 수집이 안 됨

개선 방안:
1. 시간 기반 중복 체크: 최근 7일 내 뉴스레터만 중복 체크
2. URL 기반 중복 체크: content_hash 대신 source_url로 중복 체크  
3. 제목 기반 중복 체크: 유사한 제목(90% 이상 일치)만 중복으로 판단
4. 강제 수집 모드: 중복 체크 무시하고 수집

추천: 시간 기반 중복 체크 (최근 30일)
    """)

def create_test_solution():
    """테스트 솔루션 생성"""
    print("\n🧪 테스트 솔루션 생성")
    print("="*50)
    
    # NewsletterCollector의 중복 체크 로직을 임시로 수정하는 패치 파일 생성
    patch_content = '''
# NewsletterCollector 중복 체크 로직 개선 패치

# 기존 _create_newsletter 메서드의 중복 체크 부분을 다음과 같이 수정:

# 1. 시간 기반 중복 체크 (최근 30일)
from datetime import datetime, timedelta

cutoff_date = datetime.now() - timedelta(days=30)
existing = db.query(Newsletter).filter(
    Newsletter.content_hash == content_hash,
    Newsletter.collected_date >= cutoff_date
).first()

# 2. 또는 URL 기반 중복 체크
existing = db.query(Newsletter).filter(
    Newsletter.source_url == newsletter_data.source_url
).first()

# 3. 강제 수집 모드 추가
if force_collect:
    existing = None  # 중복 체크 건너뛰기
'''
    
    with open('collection_patch.txt', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✅ collection_patch.txt 파일이 생성되었습니다")
    print("이 패치를 적용하여 중복 체크 로직을 개선할 수 있습니다")

def main():
    """메인 함수"""
    print("🔧 뉴스레터 수집 시스템 수정 도구")
    print("="*60)
    
    while True:
        print("\n선택하세요:")
        print("1. 현재 상태 확인")
        print("2. 모든 뉴스레터 삭제 (테스트용)")
        print("3. 오래된 뉴스레터 삭제")
        print("4. Well+Good 소스 수정")
        print("5. 중복 체크 개선 제안")
        print("6. 테스트 솔루션 생성")
        print("0. 종료")
        
        choice = input("\n번호를 입력하세요: ").strip()
        
        if choice == '1':
            show_current_status()
        elif choice == '2':
            clear_all_newsletters()
        elif choice == '3':
            days = input("몇 일 이전 뉴스레터를 삭제할까요? (기본: 7): ").strip()
            days = int(days) if days.isdigit() else 7
            clear_old_newsletters(days)
        elif choice == '4':
            fix_wellandgood_source()
        elif choice == '5':
            improve_duplicate_check()
        elif choice == '6':
            create_test_solution()
        elif choice == '0':
            print("👋 프로그램을 종료합니다")
            break
        else:
            print("❌ 잘못된 선택입니다")

if __name__ == "__main__":
    main()