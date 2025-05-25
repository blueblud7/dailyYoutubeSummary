#!/usr/bin/env python3
"""
최소한의 API 호출로 빠르게 채널 업데이트를 확인
"""

from datetime import datetime, timedelta
from app.models.database import SessionLocal, Channel
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv('config.env')

def fast_check():
    """빠른 채널 업데이트 확인"""
    print("⚡ 빠른 채널 업데이트 확인")
    
    # YouTube API 설정
    api_keys = os.getenv("YOUTUBE_API_KEYS", "").split(",")
    youtube = build('youtube', 'v3', developerKey=api_keys[0].strip())
    
    db = SessionLocal()
    
    try:
        channels = db.query(Channel).limit(3).all()  # 처음 3개만
        print(f"📺 {len(channels)}개 채널 확인 중...")
        
        total_new = 0
        results = []
        
        for i, channel in enumerate(channels, 1):
            print(f"{i}. {channel.channel_name}... ", end="", flush=True)
            
            try:
                # 단순히 채널의 최신 비디오 1개만 확인
                search_response = youtube.search().list(
                    part="snippet",
                    channelId=channel.channel_id,
                    maxResults=1,
                    order="date",
                    type="video",
                    publishedAfter=(datetime.now() - timedelta(days=1)).isoformat() + 'Z'
                ).execute()
                
                count = len(search_response['items'])
                total_new += count
                
                if count > 0:
                    video = search_response['items'][0]
                    results.append({
                        'channel': channel.channel_name,
                        'count': count,
                        'title': video['snippet']['title'][:30] + "..."
                    })
                    print(f"✅ {count}개")
                else:
                    print("💤 없음")
                    
            except Exception as e:
                print(f"❌ 오류")
                continue
        
        # 결과 출력
        print(f"\n📊 결과: 총 {total_new}개 새 영상")
        
        if results:
            print("🔥 업데이트 있는 채널:")
            for result in results:
                print(f"   • {result['channel']}: {result['title']}")
            
            # 텔레그램 메시지
            message = f"📺 구독 채널 업데이트\n🆕 {total_new}개 새 영상!\n\n"
            for result in results:
                message += f"• {result['channel']}: {result['count']}개\n"
            
            print(f"\n📱 알림 메시지:")
            print(message)
            
            return True
        else:
            print("💤 새로운 영상이 없습니다.")
            return False
        
    except Exception as e:
        print(f"❌ 전체 오류: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    start = datetime.now()
    
    success = fast_check()
    
    duration = (datetime.now() - start).total_seconds()
    print(f"\n⏱️ 완료! 소요시간: {duration:.1f}초")
    
    if success:
        print("✅ 구독 채널에 새로운 업데이트가 있습니다!")
        print("📧 이제 리포트를 생성하고 알림을 보낼 수 있습니다.")
    else:
        print("💤 업데이트가 없거나 확인 실패") 