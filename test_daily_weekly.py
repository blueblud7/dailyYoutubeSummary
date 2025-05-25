#!/usr/bin/env python3
"""
Daily와 Weekly 리포트 기능 테스트 스크립트
"""

import os
import sys
from datetime import datetime, timedelta
import json

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
sys.path.insert(0, project_root)

# 환경 변수 설정
os.environ['PYTHONPATH'] = project_root

try:
    from app.models.database import SessionLocal
    from app.services.report_service import ReportService
    from app.services.telegram_bot_service import TelegramBotService
    
    def get_db():
        """데이터베이스 세션 생성"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print(f"현재 작업 디렉토리: {os.getcwd()}")
    print(f"Python 경로: {sys.path}")
    sys.exit(1)

def test_daily_report():
    """Daily 리포트 생성 테스트"""
    print("🌅 일일 리포트 테스트 중...")
    
    try:
        db = next(get_db())
        report_service = ReportService()
        
        # 오늘 날짜로 테스트
        result = report_service.generate_daily_report(db)
        
        if 'error' in result:
            print(f"❌ 일일 리포트 생성 실패: {result['error']}")
            return result
        else:
            print(f"✅ 일일 리포트 생성 성공!")
            print(f"📅 날짜: {result.get('date', 'N/A')}")
            if 'trend_analysis' in result:
                trend = result['trend_analysis']
                print(f"📊 분석된 동영상: {len(trend.get('top_videos', []))}개")
                print(f"🎯 주요 테마: {len(trend.get('key_themes', []))}개")
            return result
        
    except Exception as e:
        print(f"❌ 일일 리포트 테스트 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        if 'db' in locals():
            db.close()

def test_weekly_report():
    """Weekly 리포트 생성 테스트"""
    print("\n📅 주간 리포트 테스트 중...")
    
    try:
        db = next(get_db())
        report_service = ReportService()
        
        # 주간 리포트 생성
        result = report_service.generate_weekly_report(db)
        
        if 'error' in result:
            print(f"❌ 주간 리포트 생성 실패: {result['error']}")
            return result
        else:
            print(f"✅ 주간 리포트 생성 성공!")
            print(f"📅 기간: {result.get('period', 'N/A')}")
            
            # 주간 통계 확인
            stats = result.get('weekly_statistics', {})
            if stats:
                print(f"📊 주간 통계:")
                print(f"  • 총 비디오: {stats.get('total_videos', 0)}개")
                print(f"  • 총 채널: {stats.get('total_channels', 0)}개")
                print(f"  • 평균 감정: {stats.get('avg_sentiment', 0):.2f}")
                
            # 트렌드 분석 확인
            trend = result.get('trend_analysis', {})
            if trend:
                print(f"📈 트렌드 분석:")
                print(f"  • 요약: {trend.get('summary', 'N/A')[:100]}...")
                print(f"  • 주요 테마: {len(trend.get('key_themes', []))}개")
                
            return result
        
    except Exception as e:
        print(f"❌ 주간 리포트 테스트 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        if 'db' in locals():
            db.close()

def test_formatting():
    """포맷팅 테스트"""
    print("\n💬 포맷팅 테스트 중...")
    
    try:
        bot_service = TelegramBotService()
        
        # 샘플 일일 리포트
        sample_daily = {
            'report_type': 'daily',
            'date': '2024-05-24',
            'title': '테스트 일일 리포트',
            'executive_summary': '오늘의 주요 시장 동향을 요약했습니다.',
            'market_highlights': ['미국 증시 상승', '금리 동결 전망'],
            'key_developments': ['테슬라 실적 발표'],
            'tomorrow_outlook': '내일도 상승세 지속 전망'
        }
        
        # 샘플 주간 리포트
        sample_weekly = {
            'report_type': 'weekly',
            'period': '2024.05.18 - 2024.05.24',
            'title': '테스트 주간 리포트',
            'trend_analysis': {
                'summary': '이번 주는 전반적으로 상승세를 보였습니다.',
                'key_themes': ['AI 혁신', '반도체 회복', '금리 정책'],
                'market_sentiment': 'positive'
            },
            'weekly_statistics': {
                'total_videos': 25,
                'total_channels': 8,
                'avg_sentiment': 0.25
            }
        }
        
        # 포맷팅 테스트
        daily_formatted = bot_service._format_daily_report(sample_daily)
        print("✅ 일일 리포트 포맷팅 성공")
        
        weekly_formatted = bot_service._format_weekly_report(sample_weekly)
        print("✅ 주간 리포트 포맷팅 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 포맷팅 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Daily/Weekly 리포트 기능 테스트 시작\n")
    
    # 1. Daily 리포트 테스트
    daily_result = test_daily_report()
    
    # 2. Weekly 리포트 테스트  
    weekly_result = test_weekly_report()
    
    # 3. 포맷팅 테스트
    formatting_result = test_formatting()
    
    # 결과 요약
    print("\n" + "="*50)
    print("📋 테스트 결과 요약")
    print("="*50)
    print(f"• 일일 리포트: {'✅ 성공' if daily_result and not daily_result.get('error') else '❌ 실패'}")
    print(f"• 주간 리포트: {'✅ 성공' if weekly_result and not weekly_result.get('error') else '❌ 실패'}")
    print(f"• 포맷팅: {'✅ 성공' if formatting_result else '❌ 실패'}")
    
    if (daily_result and not daily_result.get('error') and 
        weekly_result and not weekly_result.get('error') and 
        formatting_result):
        print("\n🎊 모든 테스트 성공! 텔레그램에서 /daily, /weekly 명령어를 사용할 수 있습니다!")
        print("\n📱 사용 방법:")
        print("   • /daily")
        print("   • /weekly")
    else:
        print("\n💥 일부 테스트 실패. 로그를 확인해주세요.") 