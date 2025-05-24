#!/usr/bin/env python3
"""
시스템 현재 상태 확인 스크립트
"""

from smart_subscription_reporter_v2 import SmartSubscriptionReporterV2
from app.models.database import SessionLocal, Channel, Keyword

def check_system_status():
    """현재 시스템 상태 확인"""
    
    # 현재 상태 확인
    db = SessionLocal()
    channels = db.query(Channel).all()
    keywords = db.query(Keyword).all()
    db.close()
    
    print('🎯 === 투자 분석 시스템 현황 === 🎯\n')
    
    print('📺 구독 채널 현황:')
    for i, ch in enumerate(channels, 1):
        print(f'   {i}. {ch.channel_name} ({ch.channel_id})')
    
    print(f'\n🔍 키워드 현황: 총 {len(keywords)}개')
    categories = {}
    for kw in keywords:
        if kw.category not in categories:
            categories[kw.category] = 0
        categories[kw.category] += 1
    
    for category, count in categories.items():
        print(f'   {category}: {count}개')
    
    print('\n🤖 텔레그램 봇 기능:')
    print('   ✅ 채널 추가/제거')
    print('   ✅ 키워드 추가/제거') 
    print('   ✅ 분석 실행')
    print('   ✅ 통계 보기')
    
    print('\n💡 사용법:')
    print('   1. 텔레그램에서 봇에게 /start 명령어 입력')
    print('   2. 메뉴를 선택하여 채널/키워드 관리')
    print('   3. "분석 실행" 버튼으로 즉시 분석 가능')
    
    print('\n🚀 시스템이 준비되었습니다!')

if __name__ == "__main__":
    check_system_status() 