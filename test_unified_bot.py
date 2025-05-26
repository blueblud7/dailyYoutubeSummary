#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

def test_unified_bot():
    """통합 봇의 기본 기능을 테스트합니다."""
    
    print("🧪 통합 텔레그램 봇 테스트 시작")
    print("="*50)
    
    # 환경 변수 로드
    load_dotenv('config.env')
    
    # 1. 환경 변수 확인
    print("1️⃣ 환경 변수 확인...")
    required_vars = {
        'TELEGRAM_BOT_TOKEN': os.getenv("TELEGRAM_BOT_TOKEN"),
        'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY"),
        'YOUTUBE_API_KEYS': os.getenv("YOUTUBE_API_KEYS"),
        'TELEGRAM_CHAT_ID': os.getenv("TELEGRAM_CHAT_ID")
    }
    
    for var_name, var_value in required_vars.items():
        status = "✅ 설정됨" if var_value else "❌ 없음"
        print(f"   {var_name}: {status}")
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        print(f"\n❌ 누락된 환경 변수: {', '.join(missing_vars)}")
        return False
    
    # 2. 봇 클래스 import 테스트
    print("\n2️⃣ 봇 클래스 import 테스트...")
    try:
        from unified_telegram_bot import UnifiedTelegramBot
        print("   ✅ UnifiedTelegramBot 클래스 import 성공")
    except Exception as e:
        print(f"   ❌ import 실패: {e}")
        return False
    
    # 3. 봇 초기화 테스트
    print("\n3️⃣ 봇 초기화 테스트...")
    try:
        bot = UnifiedTelegramBot()
        print("   ✅ 봇 초기화 성공")
        
        # YouTube 서비스 확인
        if bot.youtube_service and bot.youtube_service.youtube:
            print("   ✅ YouTube 서비스 초기화 성공")
        else:
            print("   ⚠️ YouTube 서비스 초기화 문제")
        
        # 분석 서비스 확인
        if bot.analysis_service and bot.analysis_service.client:
            print("   ✅ AI 분석 서비스 초기화 성공")
        else:
            print("   ⚠️ AI 분석 서비스 초기화 문제")
        
    except Exception as e:
        print(f"   ❌ 봇 초기화 실패: {e}")
        return False
    
    # 4. YouTube URL 패턴 테스트
    print("\n4️⃣ YouTube URL 패턴 테스트...")
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
    ]
    
    for url in test_urls:
        video_id = bot.extract_video_id(url)
        if video_id == "dQw4w9WgXcQ":
            print(f"   ✅ {url[:30]}... → {video_id}")
        else:
            print(f"   ❌ {url[:30]}... → {video_id}")
    
    # 5. 데이터베이스 연결 테스트
    print("\n5️⃣ 데이터베이스 연결 테스트...")
    try:
        from app.models.database import SessionLocal, Channel, Keyword
        db = SessionLocal()
        
        # 채널 및 키워드 수 확인
        channel_count = db.query(Channel).count()
        keyword_count = db.query(Keyword).count()
        
        print(f"   ✅ 데이터베이스 연결 성공")
        print(f"   📺 등록된 채널: {channel_count}개")
        print(f"   🔍 등록된 키워드: {keyword_count}개")
        
        db.close()
        
    except Exception as e:
        print(f"   ❌ 데이터베이스 연결 실패: {e}")
    
    print("\n✅ 통합 봇 테스트 완료!")
    print("="*50)
    print("🚀 봇을 실행하려면: python run_unified_bot.py")
    print("📱 텔레그램에서 /start 명령으로 시작하세요!")
    
    return True

if __name__ == "__main__":
    test_unified_bot() 