#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.telegram_bot_service import TelegramBotService
from app.models.database import SessionLocal
from dotenv import load_dotenv

async def test_telegram_bot():
    """텔레그램 봇의 주요 기능을 테스트합니다."""
    
    print("🤖 텔레그램 봇 기능 테스트")
    print("="*50)
    
    # 환경 변수 로드
    load_dotenv('config.env')
    
    # 텔레그램 봇 서비스 초기화
    bot_service = TelegramBotService()
    
    # 1. 봇 설정 확인
    print("\n🔧 봇 설정 확인...")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        print("📋 설정 방법:")
        print("1. 텔레그램에서 @BotFather에게 /newbot 명령")
        print("2. 봇 이름과 사용자명 설정")
        print("3. 받은 토큰을 config.env에 추가:")
        print("   TELEGRAM_BOT_TOKEN=your-bot-token")
        return False
    else:
        print(f"✅ 봇 토큰 설정됨: {bot_token[:10]}...")
    
    if not chat_id:
        print("⚠️ TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        print("📋 채팅 ID 확인 방법:")
        print("1. 봇과 대화 시작")
        print("2. @userinfobot에게 /start 명령으로 Chat ID 확인")
        print("3. config.env에 추가: TELEGRAM_CHAT_ID=your-chat-id")
    else:
        print(f"✅ 채팅 ID 설정됨: {chat_id}")
    
    # 2. 개별 기능 테스트
    print("\n🧪 개별 기능 테스트...")
    
    try:
        db = SessionLocal()
        
        # 키워드 리포트 테스트
        print("   🔍 키워드 리포트 테스트...")
        keyword_report = bot_service.personalized_service.generate_keyword_focused_report(
            db, "주식", days_back=3
        )
        
        if keyword_report.get('message'):
            print(f"   ℹ️  {keyword_report['message']}")
        else:
            formatted = bot_service._format_keyword_report(keyword_report)
            print(f"   ✅ 키워드 리포트 포맷팅 성공 ({len(formatted)} 글자)")
        
        # 채널 리포트 테스트
        print("   📺 채널 리포트 테스트...")
        channel_report = bot_service.personalized_service.generate_channel_focused_report(
            db, "체슬리TV", days_back=7
        )
        
        if channel_report.get('message'):
            print(f"   ℹ️  {channel_report['message']}")
        else:
            formatted = bot_service._format_channel_report(channel_report)
            print(f"   ✅ 채널 리포트 포맷팅 성공 ({len(formatted)} 글자)")
        
        # 일일 리포트 테스트
        print("   📊 일일 리포트 테스트...")
        daily_report = bot_service.report_service.generate_daily_report(db)
        
        if daily_report.get('error'):
            print(f"   ℹ️  {daily_report['error']}")
        else:
            formatted = bot_service._format_daily_report(daily_report)
            print(f"   ✅ 일일 리포트 포맷팅 성공 ({len(formatted)} 글자)")
        
    except Exception as e:
        print(f"   ❌ 기능 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # 3. 알림 발송 테스트 (설정이 있는 경우만)
    if bot_token and chat_id:
        print("\n📱 알림 발송 테스트...")
        try:
            test_message = """
🧪 **텔레그램 봇 테스트**

이 메시지는 투자 인사이트 분석 봇의 테스트 메시지입니다.

✅ 봇이 정상적으로 동작하고 있습니다!

사용 가능한 명령어:
• `/keyword 주식` - 주식 분석
• `/daily` - 일일 리포트
• `/help` - 전체 사용법
            """
            
            result = await bot_service.send_notification(test_message.strip())
            
            if result:
                print("   ✅ 테스트 메시지 발송 성공!")
                print("   📱 텔레그램에서 메시지를 확인해보세요.")
            else:
                print("   ❌ 테스트 메시지 발송 실패")
                
        except Exception as e:
            print(f"   ❌ 알림 발송 테스트 중 오류: {e}")
    
    # 4. 명령어 안내
    print(f"\n📋 사용 가능한 명령어:")
    commands = [
        "/start - 봇 시작 및 환영 메시지",
        "/help - 상세 사용법 안내",
        "/keyword [키워드] - 특정 키워드 분석 (예: /keyword 주식)",
        "/channel [채널명] - 특정 채널 분석 (예: /channel 체슬리TV)",
        "/influencer [인물명] - 인물 언급 분석 (예: /influencer 박세익)",
        "/daily - 오늘의 일일 리포트",
        "/weekly - 주간 종합 리포트", 
        "/hot - 현재 핫한 키워드 TOP 10",
        "/trend - 최근 3일 트렌드 분석",
        "/multi [키워드] [채널] [인물] - 다차원 분석"
    ]
    
    for cmd in commands:
        print(f"   • {cmd}")
    
    print(f"\n🚀 봇 실행 방법:")
    print(f"   python run_telegram_bot.py")
    
    return True

async def test_notification_features():
    """알림 기능을 상세 테스트합니다."""
    
    print("\n📧 알림 기능 상세 테스트")
    print("="*30)
    
    bot_service = TelegramBotService()
    
    # 포맷팅 테스트
    print("🎨 메시지 포맷팅 테스트...")
    
    # 가상 데이터로 포맷팅 테스트
    sample_keyword_report = {
        'keyword': '테스트',
        'statistics': {
            'total_analyses': 5,
            'total_channels': 2,
            'avg_sentiment': 0.25,
            'sentiment_distribution': {
                'positive': 3,
                'neutral': 1,
                'negative': 1
            }
        },
        'top_videos': [
            {
                'video_title': '테스트 영상 제목입니다',
                'channel_name': '테스트 채널',
                'importance_score': 0.85
            }
        ]
    }
    
    formatted = bot_service._format_keyword_report(sample_keyword_report)
    print(f"✅ 키워드 리포트 포맷팅: {len(formatted)} 글자")
    print("📝 미리보기:")
    print(formatted[:200] + "..." if len(formatted) > 200 else formatted)

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 테스트 실행
    asyncio.run(test_telegram_bot())
    asyncio.run(test_notification_features()) 