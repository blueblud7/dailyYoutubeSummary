#!/usr/bin/env python3
"""
구독 채널의 새 영상을 수집하고 간단한 리포트를 생성하는 테스트 스크립트
"""

import logging
from datetime import datetime, timedelta
from app.models.database import SessionLocal, Channel, Video
from app.services.youtube_service import YouTubeService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_subscription_updates():
    """구독 채널들의 새 영상을 확인합니다."""
    logger.info("=== 구독 채널 업데이트 확인 시작 ===")
    
    db = SessionLocal()
    youtube_service = YouTubeService()
    
    try:
        # DB에서 구독 채널 목록 가져오기
        channels = db.query(Channel).all()
        logger.info(f"총 {len(channels)}개 구독 채널 발견")
        
        total_new_videos = 0
        channel_updates = {}
        
        for channel in channels:
            logger.info(f"📺 {channel.channel_name} 채널 확인 중...")
            
            try:
                # 최근 3일간의 새 영상 조회
                published_after = datetime.now() - timedelta(days=3)
                videos_data = youtube_service.get_channel_videos(
                    channel.channel_id, 
                    max_results=10,
                    published_after=published_after
                )
                
                if videos_data:
                    # DB에 이미 있는 영상인지 확인
                    new_videos = []
                    for video_data in videos_data:
                        existing_video = db.query(Video).filter(
                            Video.video_id == video_data['video_id']
                        ).first()
                        
                        if not existing_video:
                            new_videos.append(video_data)
                    
                    if new_videos:
                        logger.info(f"   ✅ {len(new_videos)}개 새 영상 발견")
                        total_new_videos += len(new_videos)
                        
                        channel_updates[channel.channel_name] = {
                            'new_videos': len(new_videos),
                            'videos': new_videos
                        }
                        
                        # 새 영상 정보 출력
                        for video in new_videos[:3]:  # 상위 3개만
                            print(f"      📹 {video['title'][:50]}...")
                            print(f"         📅 {video['published_at'].strftime('%Y-%m-%d %H:%M')}")
                            print(f"         👀 조회수: {video['view_count']:,}회")
                    else:
                        logger.info(f"   ℹ️ 새 영상 없음")
                        channel_updates[channel.channel_name] = {
                            'new_videos': 0,
                            'videos': []
                        }
                else:
                    logger.info(f"   ℹ️ 영상 정보를 가져올 수 없음")
                    
            except Exception as e:
                logger.error(f"   ❌ {channel.channel_name} 채널 처리 중 오류: {e}")
                continue
        
        # 결과 리포트 생성
        generate_simple_report(channel_updates, total_new_videos)
        
        return channel_updates
        
    except Exception as e:
        logger.error(f"구독 채널 업데이트 확인 중 오류: {e}")
        return {}
    finally:
        db.close()

def generate_simple_report(channel_updates, total_new_videos):
    """간단한 구독 채널 업데이트 리포트를 생성합니다."""
    print("\n" + "="*60)
    print("📊 구독 채널 업데이트 리포트")
    print("="*60)
    print(f"📅 확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📹 총 새 영상: {total_new_videos}개")
    print(f"📺 확인한 채널: {len(channel_updates)}개")
    
    if total_new_videos > 0:
        print(f"\n📺 채널별 업데이트:")
        for channel_name, updates in channel_updates.items():
            if updates['new_videos'] > 0:
                print(f"   • {channel_name}: {updates['new_videos']}개 새 영상")
        
        print(f"\n🔥 가장 활발한 채널:")
        sorted_channels = sorted(
            channel_updates.items(), 
            key=lambda x: x[1]['new_videos'], 
            reverse=True
        )
        
        for channel_name, updates in sorted_channels[:3]:
            if updates['new_videos'] > 0:
                print(f"   🏆 {channel_name}: {updates['new_videos']}개 영상")
                
        print(f"\n📄 최신 영상 샘플:")
        count = 0
        for channel_name, updates in sorted_channels:
            if count >= 5:  # 최대 5개만
                break
            for video in updates['videos'][:2]:  # 채널당 최대 2개
                if count >= 5:
                    break
                print(f"   📹 [{channel_name}] {video['title'][:45]}...")
                print(f"      📅 {video['published_at'].strftime('%m/%d %H:%M')} | 👀 {video['view_count']:,}회")
                count += 1
    else:
        print(f"\n💤 최근 3일간 새로운 영상이 없습니다.")
        print(f"   모든 구독 채널이 업데이트 없음")
    
    print("="*60)

def suggest_telegram_message(channel_updates, total_new_videos):
    """텔레그램 메시지 형태의 요약을 생성합니다."""
    if total_new_videos == 0:
        message = "📺 구독 채널 업데이트\n\n💤 최근 3일간 새로운 영상이 없습니다."
        return message
    
    message = f"📺 구독 채널 업데이트\n\n"
    message += f"🆕 총 {total_new_videos}개 새 영상 발견!\n\n"
    
    # 채널별 업데이트
    active_channels = [(name, data) for name, data in channel_updates.items() if data['new_videos'] > 0]
    
    if active_channels:
        message += "📊 채널별 업데이트:\n"
        for channel_name, updates in active_channels[:5]:  # 상위 5개만
            message += f"• {channel_name}: {updates['new_videos']}개\n"
        
        # 주요 영상 1-2개 소개
        message += f"\n🔥 주요 영상:\n"
        for i, (channel_name, updates) in enumerate(active_channels[:2]):
            if updates['videos']:
                video = updates['videos'][0]
                title = video['title'][:35] + "..." if len(video['title']) > 35 else video['title']
                message += f"{i+1}. [{channel_name}] {title}\n"
    
    print(f"\n📱 텔레그램 메시지 예시:")
    print("-" * 40)
    print(message)
    print("-" * 40)
    
    return message

if __name__ == "__main__":
    logger.info("🚀 구독 채널 업데이트 확인 시작")
    
    start_time = datetime.now()
    
    # 구독 채널 업데이트 확인
    updates = check_subscription_updates()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 텔레그램 메시지 형태 요약 생성
    total_new = sum(data['new_videos'] for data in updates.values())
    suggest_telegram_message(updates, total_new)
    
    print(f"\n✅ 완료! 소요 시간: {duration:.1f}초")
    
    if total_new > 0:
        print(f"📧 구독자들에게 업데이트 알림을 보낼 수 있습니다!")
    else:
        print(f"💤 업데이트할 내용이 없습니다.") 