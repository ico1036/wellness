#!/usr/bin/env python3
"""
테스트 실행 스크립트
다양한 테스트 시나리오를 지원하는 테스트 실행 도구
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
backend_root = project_root / "backend"
sys.path.insert(0, str(backend_root))

def run_command(command, cwd=None):
    """명령어 실행"""
    print(f"🔧 실행: {' '.join(command)}")
    try:
        result = subprocess.run(command, cwd=cwd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 명령어 실행 실패: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ 명령어를 찾을 수 없습니다: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="웰니스 리트리트 뉴스레터 테스트 실행")
    parser.add_argument("--type", default="all", 
                       choices=["all", "unit", "integration", "api", "coverage"],
                       help="테스트 타입 (기본값: all)")
    parser.add_argument("--file", help="특정 테스트 파일 실행")
    parser.add_argument("--function", help="특정 테스트 함수 실행")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    parser.add_argument("--fast", action="store_true", help="빠른 테스트 (slow 마커 제외)")
    parser.add_argument("--coverage", action="store_true", help="커버리지 리포트 생성")
    parser.add_argument("--html-coverage", action="store_true", help="HTML 커버리지 리포트")
    parser.add_argument("--lint", action="store_true", help="린트 검사 실행")
    parser.add_argument("--format", action="store_true", help="코드 포맷팅 실행")
    
    args = parser.parse_args()
    
    # 백엔드 디렉토리로 이동
    os.chdir(backend_root)
    
    success = True
    
    print("🧪 웰니스 리트리트 뉴스레터 테스트 실행")
    print("=" * 50)
    
    # 코드 포맷팅
    if args.format:
        print("\n📝 코드 포맷팅 실행...")
        commands = [
            ["uv", "run", "black", "app/"],
            ["uv", "run", "isort", "app/"],
        ]
        for cmd in commands:
            if not run_command(cmd):
                success = False
    
    # 린트 검사
    if args.lint:
        print("\n🔍 린트 검사 실행...")
        commands = [
            ["uv", "run", "black", "--check", "app/"],
            ["uv", "run", "isort", "--check-only", "app/"],
            ["uv", "run", "mypy", "app/"],
        ]
        for cmd in commands:
            if not run_command(cmd):
                success = False
    
    # 테스트 실행
    if not args.format and not args.lint:
        print(f"\n🧪 테스트 실행 ({args.type})...")
        
        # pytest 명령어 구성
        cmd = ["uv", "run", "pytest"]
        
        # 상세 출력
        if args.verbose:
            cmd.append("-v")
        
        # 특정 파일
        if args.file:
            cmd.append(f"app/tests/{args.file}")
        
        # 특정 함수
        if args.function:
            if args.file:
                cmd[-1] += f"::{args.function}"
            else:
                cmd.append(f"-k {args.function}")
        
        # 테스트 타입별 마커
        if args.type == "unit":
            cmd.extend(["-m", "unit"])
        elif args.type == "integration":
            cmd.extend(["-m", "integration"])
        elif args.type == "api":
            cmd.extend(["-m", "api"])
        
        # 빠른 테스트
        if args.fast:
            cmd.extend(["-m", "not slow"])
        
        # 커버리지
        if args.coverage or args.html_coverage or args.type == "coverage":
            cmd.extend(["--cov=app", "--cov-report=term-missing"])
            if args.html_coverage:
                cmd.append("--cov-report=html:htmlcov")
        
        # 파일이나 함수가 지정되지 않았으면 기본 테스트 경로
        if not args.file and not args.function:
            cmd.append("app/tests/")
        
        success = run_command(cmd)
    
    # 결과 출력
    print("\n" + "=" * 50)
    if success:
        print("✅ 모든 작업이 성공적으로 완료되었습니다!")
        
        # 커버리지 HTML 리포트 안내
        if args.html_coverage:
            html_path = backend_root / "htmlcov" / "index.html"
            if html_path.exists():
                print(f"📊 HTML 커버리지 리포트: file://{html_path}")
    else:
        print("❌ 일부 작업이 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()