#!/bin/bash

echo "🚀 웰니스 리트리트 뉴스레터 서버를 시작합니다..."
echo ""

# backend 디렉토리로 이동
cd backend

# uv를 사용하여 서버 실행
echo "📡 서버 실행 중... (Ctrl+C로 종료)"
echo "🌐 웹사이트: http://127.0.0.1:8000"
echo "📚 API 문서: http://127.0.0.1:8000/docs"
echo ""

uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload