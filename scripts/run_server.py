#!/usr/bin/env python3
"""
웰니스 리트리트 뉴스레터 서버 실행 스크립트
개발 및 프로덕션 환경에서 서버를 실행하는 스크립트
"""
import os
import sys
import argparse
import uvicorn
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="웰니스 리트리트 뉴스레터 서버 실행")
    parser.add_argument("--host", default="0.0.0.0", help="서버 호스트 (기본값: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="서버 포트 (기본값: 8000)")
    parser.add_argument("--reload", action="store_true", help="개발 모드 (자동 리로드)")
    parser.add_argument("--workers", type=int, default=1, help="워커 프로세스 수 (기본값: 1)")
    parser.add_argument("--log-level", default="info", 
                       choices=["critical", "error", "warning", "info", "debug"],
                       help="로그 레벨 (기본값: info)")
    parser.add_argument("--env", default="development", 
                       choices=["development", "production"],
                       help="실행 환경 (기본값: development)")
    
    args = parser.parse_args()
    
    # 환경 변수 설정
    os.environ["ENVIRONMENT"] = args.env
    
    if args.env == "development":
        os.environ["DEBUG"] = "true"
        os.environ["SQL_ECHO"] = "true"
    else:
        os.environ["DEBUG"] = "false"
        os.environ["SQL_ECHO"] = "false"
    
    # 서버 설정
    config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "access_log": True,
    }
    
    if args.env == "development" or args.reload:
        config.update({
            "reload": True,
            "reload_dirs": [str(project_root / "app")],
        })
    else:
        config.update({
            "workers": args.workers,
            "reload": False,
        })
    
    print(f"🚀 웰니스 리트리트 뉴스레터 서버 시작")
    print(f"   환경: {args.env}")
    print(f"   주소: http://{args.host}:{args.port}")
    print(f"   로그 레벨: {args.log_level}")
    
    if args.env == "development":
        print(f"   개발 모드: 자동 리로드 활성화")
    else:
        print(f"   프로덕션 모드: 워커 {args.workers}개")
    
    print("   Ctrl+C로 종료")
    print("-" * 50)
    
    # 서버 시작
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()