#!/usr/bin/env python3
"""
구독 채널 업데이트를 확인하고 텔레그램으로 알림을 보내는 스크립트
"""

import os
import requests
from datetime import datetime, timedelta
from app.models.database import SessionLocal, Channel
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv('config.env')

class SubscriptionNotifier:
    def __init__(self):
        self.api_keys = os.getenv("YOUTUBE_API_KEYS", "").split(",")
        self.youtube = build('youtube', 'v3', developerKey=self.api_keys[0].strip())
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    def check_updates(self, hours_back=24):
        """구독 채널들의 업데이트를 확인합니다."""
        print(f"📺 최근 {hours_back}시간 구독 채널 업데이트 확인 중...")
        
        db = SessionLocal()
        
        try:
            channels = db.query(Channel).all()
            print(f"   총 {len(channels)}개 채널 확인")
            
            updates = []
            total_new_videos = 0
            
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for channel in channels:
                try:
                    # 최근 영상 검색
                    search_response = self.youtube.search().list(
                        part="snippet",
                        channelId=channel.channel_id,
                        maxResults=3,
                        order="date",
                        type="video",
                        publishedAfter=cutoff_time.isoformat() + 'Z'
                    ).execute()
                    
                    if search_response['items']:
                        videos = []
                        for item in search_response['items']:
                            videos.append({
                                'title': item['snippet']['title'],
                                'published_at': item['snippet']['publishedAt'],
                                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                            })
                        
                        updates.append({
                            'channel_name': channel.channel_name,
                            'video_count': len(videos),
                            'videos': videos
                        })
                        
                        total_new_videos += len(videos)
                        print(f"   ✅ {channel.channel_name}: {len(videos)}개 새 영상")
                    else:
                        print(f"   💤 {channel.channel_name}: 업데이트 없음")
                        
                except Exception as e:
                    print(f"   ❌ {channel.channel_name}: 오류 ({str(e)[:30]}...)")
                    continue
            
            return {
                'total_updates': total_new_videos,
                'channel_updates': updates,
                'hours_back': hours_back
            }
            
        except Exception as e:
            print(f"❌ 전체 확인 중 오류: {e}")
            return None
        finally:
            db.close()
    
    def format_telegram_message(self, update_data):
        """텔레그램 메시지를 포맷팅합니다."""
        if update_data['total_updates'] == 0:
            return f"📺 구독 채널 업데이트\n\n💤 최근 {update_data['hours_back']}시간간 새로운 영상이 없습니다."
        
        message = f"📺 구독 채널 업데이트 알림\n"
        message += f"🆕 총 {update_data['total_updates']}개 새 영상 발견!\n\n"
        
        # 채널별 업데이트
        for update in update_data['channel_updates']:
            message += f"🎬 **{update['channel_name']}** ({update['video_count']}개)\n"
            
            # 최대 2개 영상만 표시
            for video in update['videos'][:2]:
                title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
                message += f"   📹 [{title}]({video['url']})\n"
            
            if update['video_count'] > 2:
                message += f"   ⋯ 외 {update['video_count'] - 2}개 더\n"
            message += "\n"
        
        message += f"⏰ 확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return message
    
    def send_telegram_notification(self, message):
        """텔레그램으로 알림을 보냅니다."""
        if not self.telegram_token or not self.telegram_chat_id:
            print("❌ 텔레그램 설정이 없습니다.")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        data = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("✅ 텔레그램 알림 전송 성공!")
                return True
            else:
                print(f"❌ 텔레그램 전송 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 텔레그램 전송 중 오류: {e}")
            return False
    
    def run_notification_cycle(self, hours_back=24, send_even_if_empty=False):
        """구독 채널 확인 및 알림 전체 사이클을 실행합니다."""
        start_time = datetime.now()
        print(f"🚀 구독 채널 알림 사이클 시작 ({start_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 1. 업데이트 확인
        update_data = self.check_updates(hours_back)
        
        if not update_data:
            print("❌ 업데이트 확인 실패")
            return False
        
        # 2. 메시지 생성
        message = self.format_telegram_message(update_data)
        
        print(f"\n📱 생성된 메시지:")
        print("-" * 50)
        print(message)
        print("-" * 50)
        
        # 3. 알림 발송 결정
        should_send = update_data['total_updates'] > 0 or send_even_if_empty
        
        if should_send:
            print(f"\n📤 텔레그램 알림 발송 중...")
            success = self.send_telegram_notification(message)
        else:
            print(f"\n💤 업데이트가 없어 알림을 보내지 않습니다.")
            success = True
        
        # 4. 결과 요약
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n🎉 알림 사이클 완료!")
        print(f"   ⏱️ 소요 시간: {duration:.1f}초")
        print(f"   📹 새 영상: {update_data['total_updates']}개")
        print(f"   📤 알림 발송: {'성공' if success else '실패'}")
        
        return success

def main():
    """메인 실행 함수"""
    notifier = SubscriptionNotifier()
    
    # 최근 24시간 업데이트 확인 및 알림
    success = notifier.run_notification_cycle(
        hours_back=24,
        send_even_if_empty=False  # 업데이트가 있을 때만 알림
    )
    
    if success:
        print("\n✅ 구독 채널 알림 시스템이 정상적으로 작동했습니다!")
    else:
        print("\n❌ 알림 시스템에 문제가 발생했습니다.")

if __name__ == "__main__":
    main() 