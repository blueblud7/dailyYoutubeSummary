#!/usr/bin/env python3
"""
테스트용 채널 데이터 추가 스크립트
"""

from app.models.database import SessionLocal, Channel, create_tables
from datetime import datetime

def add_test_channels():
    """테스트용 채널들을 데이터베이스에 추가"""
    create_tables()
    
    test_channels = [
        {
            "channel_id": "UCQl4P8PHxLJbGYqoT45XEiA",  # 체슬리TV
            "channel_name": "체슬리TV",
            "channel_url": "https://www.youtube.com/@chesley_tv",
            "description": "주식 투자, 경제 분석 채널"
        },
        {
            "channel_id": "UC4gKaXMj2pN0zdDU5s5SEWA",  # 삼프로TV
            "channel_name": "삼프로TV_경제의신과함께",
            "channel_url": "https://www.youtube.com/@3proTV",
            "description": "경제 전문 분석 채널"
        },
        {
            "channel_id": "UCxZMEpbpgkZ4xJYlk7n2CXw",  # 한경TV
            "channel_name": "한국경제TV",
            "channel_url": "https://www.youtube.com/@HankookEconomicTV",
            "description": "한국경제신문 공식 채널"
        },
        {
            "channel_id": "UC1kcH9BZB4Zt5QGn5zlm5Dw",  # 신사임당
            "channel_name": "신사임당",
            "channel_url": "https://www.youtube.com/@SINSAIMDANG",
            "description": "투자 교육 채널"
        },
        {
            "channel_id": "UCYVTLzsVOUlVE5L72SYFGhw",  # 부크온
            "channel_name": "부크온",
            "channel_url": "https://www.youtube.com/@BookOn",
            "description": "경제 도서 분석 채널"
        }
    ]
    
    db = SessionLocal()
    
    try:
        added_count = 0
        for channel_data in test_channels:
            # 기존 채널 확인
            existing = db.query(Channel).filter(Channel.channel_id == channel_data["channel_id"]).first()
            
            if existing:
                print(f"✅ 이미 존재하는 채널: {channel_data['channel_name']}")
                continue
            
            # 새 채널 추가
            channel = Channel(
                channel_id=channel_data["channel_id"],
                channel_name=channel_data["channel_name"],
                channel_url=channel_data["channel_url"],
                description=channel_data["description"],
                subscriber_count=0,
                video_count=0
            )
            
            db.add(channel)
            added_count += 1
            print(f"➕ 채널 추가: {channel_data['channel_name']}")
        
        db.commit()
        print(f"\n🎉 총 {added_count}개 채널이 추가되었습니다!")
        
        # 최종 채널 수 확인
        total_channels = db.query(Channel).count()
        print(f"📺 데이터베이스에 총 {total_channels}개 채널이 저장되어 있습니다.")
        
    except Exception as e:
        print(f"❌ 채널 추가 중 오류: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_channels() 