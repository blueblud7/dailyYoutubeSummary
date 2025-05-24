#!/usr/bin/env python3
"""
구독 채널의 새 영상을 빠르게 확인하는 스크립트
"""

from datetime import datetime, timedelta
from app.models.database import SessionLocal, Channel
from app.services.youtube_service import YouTubeService

def quick_channel_check():
    """구독 채널들의 새 영상을 빠르게 확인합니다."""
    print("📺 구독 채널 업데이트 확인 중...")
    
    db = SessionLocal()
    youtube_service = YouTubeService()
    
    try:
        # DB에서 구독 채널 목록 가져오기
        channels = db.query(Channel).all()
        print(f"총 {len(channels)}개 구독 채널 확인")
        
        total_new_videos = 0
        updates = []
        
        for i, channel in enumerate(channels[:3], 1):  # 처음 3개만 테스트
            print(f"{i}. {channel.channel_name} 확인 중...")
            
            try:
                # 최근 1일간의 새 영상 조회 (빠른 확인)
                published_after = datetime.now() - timedelta(days=1)
                videos_data = youtube_service.get_channel_videos(
                    channel.channel_id, 
                    max_results=5,
                    published_after=published_after
                )
                
                if videos_data:
                    print(f"   ✅ {len(videos_data)}개 영상 발견")
                    total_new_videos += len(videos_data)
                    
                    updates.append({
                        'channel': channel.channel_name,
                        'count': len(videos_data),
                        'latest': videos_data[0]['title'][:40] if videos_data else ''
                    })
                else:
                    print(f"   ℹ️ 새 영상 없음")
                    
            except Exception as e:
                print(f"   ❌ 오류: {str(e)[:50]}...")
                continue
        
        # 결과 출력
        print(f"\n📊 결과 요약:")
        print(f"   📹 총 새 영상: {total_new_videos}개")
        
        if updates:
            print(f"   📺 활발한 채널:")
            for update in updates:
                if update['count'] > 0:
                    print(f"      • {update['channel']}: {update['count']}개")
                    print(f"        최신: {update['latest']}...")
        
        # 텔레그램 메시지 형태
        if total_new_videos > 0:
            message = f"📺 구독 채널 업데이트\n🆕 {total_new_videos}개 새 영상!\n\n"
            for update in updates:
                if update['count'] > 0:
                    message += f"• {update['channel']}: {update['count']}개\n"
            
            print(f"\n📱 알림 메시지:")
            print("-" * 30)
            print(message)
            print("-" * 30)
        else:
            print(f"\n💤 새로운 영상이 없습니다.")
        
        return total_new_videos > 0
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 구독 채널 빠른 확인 시작\n")
    
    success = quick_channel_check()
    
    if success:
        print(f"\n✅ 새 영상이 있습니다! 리포트를 생성할 수 있습니다.")
    else:
        print(f"\n💤 업데이트가 없거나 확인 실패했습니다.")
    
    print(f"\n완료!") 