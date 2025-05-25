#!/usr/bin/env python3
"""
새로운 구독 채널 업데이트 스크립트
"""

from smart_subscription_reporter_v2 import SmartSubscriptionReporterV2
from app.models.database import SessionLocal, Channel, create_tables
from datetime import datetime

def find_and_update_channels():
    """새로운 구독 채널들을 찾아서 데이터베이스 업데이트"""
    
    reporter = SmartSubscriptionReporterV2()
    
    # 채널 검색할 키워드들
    search_terms = [
        '오종태',
        '홍춘욱', 
        '김준송TV',
        '체슬리TV',
        '언더스탠딩',
        '손경제',
        'MK_Invest',
        '한경 글로벌마켓'
    ]
    
    print('📺 새로운 구독 채널 ID 검색 중...\n')
    
    found_channels = []
    
    for term in search_terms:
        try:
            result = reporter._execute_youtube_api_with_retry(
                lambda: reporter.youtube.search().list(
                    part='snippet',
                    q=term,
                    type='channel',
                    maxResults=2
                ).execute()
            )
            
            print(f'🔍 "{term}" 검색 결과:')
            for i, item in enumerate(result['items'][:2], 1):
                title = item['snippet']['title']
                channel_id = item['id']['channelId']
                description = item['snippet'].get('description', '')
                print(f'  {i}. {title}: {channel_id}')
                
                if i == 1:  # 첫 번째 결과를 사용
                    found_channels.append({
                        'channel_name': title,
                        'channel_id': channel_id,
                        'description': description,
                        'search_term': term
                    })
            print()
            
        except Exception as e:
            print(f'❌ {term} 검색 실패: {e}')
            print()
    
    # 데이터베이스 업데이트
    print('📊 데이터베이스 업데이트 중...\n')
    
    db = SessionLocal()
    try:
        # 기존 채널들 삭제
        existing_channels = db.query(Channel).all()
        for channel in existing_channels:
            print(f'🗑️ 기존 채널 삭제: {channel.channel_name}')
            db.delete(channel)
        
        # 새 채널들 추가
        for channel_data in found_channels:
            channel = Channel(
                channel_id=channel_data['channel_id'],
                channel_name=channel_data['channel_name'],
                channel_url=f"https://www.youtube.com/channel/{channel_data['channel_id']}",
                description=f"{channel_data['description']} (검색어: {channel_data['search_term']})",
                subscriber_count=0,
                video_count=0
            )
            
            db.add(channel)
            print(f'➕ 새 채널 추가: {channel_data["channel_name"]}')
        
        db.commit()
        print(f'\n🎉 총 {len(found_channels)}개 채널이 업데이트되었습니다!')
        
        # 최종 채널 목록 확인
        print('\n📺 최종 구독 채널 목록:')
        final_channels = db.query(Channel).all()
        for i, channel in enumerate(final_channels, 1):
            print(f'{i}. {channel.channel_name} ({channel.channel_id})')
        
    except Exception as e:
        print(f'❌ 데이터베이스 업데이트 실패: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    find_and_update_channels() 