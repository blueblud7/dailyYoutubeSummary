#!/usr/bin/env python3
"""
최종 시스템 기능 개요
"""

from smart_subscription_reporter_v2 import SmartSubscriptionReporterV2
from app.models.database import SessionLocal, Channel, Keyword

def show_system_overview():
    """전체 시스템 기능 개요 표시"""
    
    print("🚀 === 투자 분석 시스템 최종 버전 === 🚀\n")
    
    # 현재 구독 채널 확인
    db = SessionLocal()
    channels = db.query(Channel).all()
    keywords = db.query(Keyword).all()
    db.close()
    
    print("📺 **구독 채널 현황**")
    print(f"   총 {len(channels)}개 채널 구독 중:")
    for i, ch in enumerate(channels, 1):
        print(f"   {i:2d}. {ch.channel_name}")
    print()
    
    print("🔍 **키워드 현황**")
    categories = {}
    for kw in keywords:
        if kw.category not in categories:
            categories[kw.category] = 0
        categories[kw.category] += 1
    
    print(f"   총 {len(keywords)}개 키워드 ({len(categories)}개 카테고리):")
    for category, count in categories.items():
        print(f"   • {category}: {count}개")
    print()
    
    print("🤖 **텔레그램 봇 기능**")
    print("   ✅ 구독 채널 관리 (추가/제거)")
    print("   ✅ 키워드 관리 (추가/제거)")
    print("   ✅ 정기 분석 실행")
    print("   ✅ 시스템 통계 조회")
    print("   🔥 **NEW: YouTube URL 즉시 요약**")
    print()
    
    print("🎬 **YouTube URL 요약 기능**")
    print("   지원 형식:")
    print("   • https://youtube.com/watch?v=VIDEO_ID")
    print("   • https://youtu.be/VIDEO_ID") 
    print("   • https://youtube.com/shorts/VIDEO_ID")
    print("   • https://youtube.com/embed/VIDEO_ID")
    print("   • https://m.youtube.com/watch?v=VIDEO_ID")
    print()
    print("   처리 과정:")
    print("   1. 📹 영상 정보 추출 (제목, 채널, 조회수 등)")
    print("   2. 📝 자막 추출 (한국어/영어)")
    print("   3. 🤖 AI 분석 (GPT-4o 활용)")
    print("   4. 📊 구조화된 요약 제공")
    print()
    
    print("📊 **AI 분석 내용**")
    print("   • 📋 종합 요약")
    print("   • 🔍 상세 분석")
    print("   • 💰 투자 시사점")
    print("   • 📈 시장 분석")
    print("   • 🎯 핵심 키워드")
    print("   • 👥 전문가 의견")
    print("   • 📉 리스크 분석")
    print("   • 🔄 실행 가능한 단계")
    print()
    
    print("⚡ **시스템 최적화**")
    print("   • 🗄️ 스마트 캐싱 (API 비용 절약)")
    print("   • 🔄 YouTube API 키 순환")
    print("   • 📱 텔레그램 실시간 알림")
    print("   • 🎯 키워드 기반 필터링")
    print("   • 📈 성능 통계 추적")
    print()
    
    print("💡 **사용법**")
    print("   1. 텔레그램 봇에 /start 입력")
    print("   2. 메뉴에서 원하는 기능 선택")
    print("   3. YouTube URL 공유시 자동 요약")
    print("   4. 정기 분석으로 최신 트렌드 파악")
    print()
    
    print("🎯 **주요 장점**")
    print("   • 🚀 빠른 요약 (30초~1분)")
    print("   • 🧠 깊이 있는 AI 분석") 
    print("   • 💰 투자 관점 특화")
    print("   • 📱 모바일 친화적")
    print("   • 🔄 실시간 업데이트")
    print("   • 💾 데이터 누적 및 활용")
    print()
    
    print("🔮 **확장 가능성**")
    print("   • 📊 포트폴리오 연동")
    print("   • 📈 주가/코인 가격 알림")
    print("   • 🎯 개인화된 추천")
    print("   • 📰 뉴스 자동 수집")
    print("   • 🤝 소셜 기능")
    print()
    
    print("✨ **시스템이 완전히 준비되었습니다!** ✨")
    print("📱 텔레그램에서 봇과 상호작용을 시작하세요!")

if __name__ == "__main__":
    show_system_overview() 