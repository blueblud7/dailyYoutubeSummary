#!/usr/bin/env python3
"""
텔레그램 봇에서 daily, weekly 명령어 시뮬레이션 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.telegram_bot_service import TelegramBotService
from app.models.database import SessionLocal

def simulate_daily_command():
    """daily 명령어 시뮬레이션"""
    print("🔍 /daily 명령어 시뮬레이션...")
    
    try:
        bot_service = TelegramBotService()
        db = SessionLocal()
        
        # 일일 리포트 생성
        report = bot_service.report_service.generate_daily_report(db)
        
        if report.get('error'):
            print(f"❌ 오류: {report['error']}")
        elif report.get('message'):
            print(f"ℹ️ {report['message']}")
        else:
            # 포맷팅된 메시지 생성
            formatted_message = bot_service._format_daily_report(report)
            
            print("✅ 일일 리포트 생성 성공!")
            print(f"📏 메시지 길이: {len(formatted_message)} 문자")
            
            # 메시지가 너무 길면 분할
            if len(formatted_message) > 4000:
                parts = bot_service._split_message(formatted_message, 4000)
                print(f"📄 메시지 분할: {len(parts)}개 부분")
                
                for i, part in enumerate(parts, 1):
                    print(f"\n--- 파트 {i} ---")
                    print(part[:200] + "..." if len(part) > 200 else part)
            else:
                print("\n--- 완성된 메시지 ---")
                print(formatted_message)
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 시뮬레이션 실패: {e}")
        return False

def simulate_weekly_command():
    """weekly 명령어 시뮬레이션"""
    print("\n🔍 /weekly 명령어 시뮬레이션...")
    
    try:
        bot_service = TelegramBotService()
        db = SessionLocal()
        
        # 주간 리포트 생성
        report = bot_service.report_service.generate_weekly_report(db)
        
        if report.get('error'):
            print(f"❌ 오류: {report['error']}")
        elif report.get('message'):
            print(f"ℹ️ {report['message']}")
        else:
            # 포맷팅된 메시지 생성
            formatted_message = bot_service._format_weekly_report(report)
            
            print("✅ 주간 리포트 생성 성공!")
            print(f"📏 메시지 길이: {len(formatted_message)} 문자")
            
            # 메시지가 너무 길면 분할
            if len(formatted_message) > 4000:
                parts = bot_service._split_message(formatted_message, 4000)
                print(f"📄 메시지 분할: {len(parts)}개 부분")
                
                for i, part in enumerate(parts, 1):
                    print(f"\n--- 파트 {i} ---")
                    print(part[:200] + "..." if len(part) > 200 else part)
            else:
                print("\n--- 완성된 메시지 ---")
                print(formatted_message)
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 시뮬레이션 실패: {e}")
        return False

def test_natural_language():
    """자연어 명령어 테스트"""
    print("\n🔍 자연어 명령어 테스트...")
    
    test_phrases = [
        "오늘 리포트 보여줘",
        "일일 분석 해줘",
        "주간 트렌드는?",
        "이번주 어땠어?",
        "weekly 리포트 줘"
    ]
    
    for phrase in test_phrases:
        print(f"\n💬 '{phrase}'")
        
        # daily 키워드 체크
        if any(word in phrase.lower() for word in ['오늘', '일일', 'daily']):
            print("  → /daily 명령어로 처리됨")
        elif any(word in phrase.lower() for word in ['주간', '이번주', 'weekly']):
            print("  → /weekly 명령어로 처리됨")
        else:
            print("  → 인식되지 않음")

if __name__ == "__main__":
    print("🤖 텔레그램 봇 Daily/Weekly 명령어 시뮬레이션\n")
    
    # 1. Daily 명령어 시뮬레이션
    daily_success = simulate_daily_command()
    
    # 2. Weekly 명령어 시뮬레이션
    weekly_success = simulate_weekly_command()
    
    # 3. 자연어 처리 테스트
    test_natural_language()
    
    print("\n🎉 시뮬레이션 완료!")
    
    # 결과 요약
    print("\n📋 시뮬레이션 결과:")
    print(f"• /daily 명령어: {'✅ 성공' if daily_success else '❌ 실패'}")
    print(f"• /weekly 명령어: {'✅ 성공' if weekly_success else '❌ 실패'}")
    
    if daily_success and weekly_success:
        print("\n🎊 텔레그램에서 /daily, /weekly 명령어를 사용할 수 있습니다!")
        print("📱 텔레그램에서 다음과 같이 테스트해보세요:")
        print("   • /daily")
        print("   • /weekly")
        print("   • '오늘 리포트 보여줘'")
        print("   • '주간 트렌드는?'")
    else:
        print("\n⚠️ 일부 기능에 문제가 있습니다. 로그를 확인해주세요.") 