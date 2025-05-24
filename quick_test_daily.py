#!/usr/bin/env python3
"""
개선된 Daily 리포트 기능 빠른 테스트
"""

import sys
import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal
from app.services.report_service import ReportService

def test_daily_report():
    """일일 리포트 빠른 테스트"""
    print("🚀 Daily 리포트 기능 빠른 테스트")
    
    db = SessionLocal()
    try:
        report_service = ReportService()
        
        print("📊 일일 리포트 생성 중...")
        result = report_service.generate_daily_report(db)
        
        print(f"✅ 결과: {result.get('report_type')}")
        
        if result.get('error'):
            print(f"❌ 오류: {result['error']}")
            return False
        elif result.get('message'):
            print(f"ℹ️ 메시지: {result['message']}")
            return True
        else:
            print(f"📅 날짜: {result.get('date')}")
            stats = result.get('statistics', {})
            print(f"📈 분석 영상: {stats.get('total_videos_analyzed', 0)}개")
            print(f"😊 평균 감정: {stats.get('avg_sentiment', 0):.2f}")
            
            daily_report = result.get('daily_report', {})
            if daily_report.get('executive_summary'):
                print(f"💡 요약: {daily_report['executive_summary'][:100]}...")
            
            return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_daily_report()
    print(f"\n🎯 테스트 결과: {'성공' if success else '실패'}")
    
    if success:
        print("\n✅ 이제 텔레그램에서 /daily 명령어를 다시 시도해보세요!")
    else:
        print("\n❌ 문제가 지속됩니다. 로그를 확인해주세요.") 