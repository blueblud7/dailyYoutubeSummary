#!/usr/bin/env python3
"""
구독 채널 업데이트 확인 + 자막 추출 + AI 분석 + 요약 리포트 생성
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models.database import SessionLocal, Channel
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

# OpenAI 버전 호환성을 위한 처리
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI 라이브러리를 사용할 수 없습니다.")
    OPENAI_AVAILABLE = False

load_dotenv('config.env')

class SmartSubscriptionReporter:
    def __init__(self):
        self.api_keys = os.getenv("YOUTUBE_API_KEYS", "").split(",")
        self.youtube = build('youtube', 'v3', developerKey=self.api_keys[0].strip())
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # OpenAI 클라이언트 초기화
        if OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.ai_enabled = True
                print("✅ AI 분석 기능이 활성화되었습니다.")
            except Exception as e:
                print(f"⚠️ OpenAI 초기화 실패: {e}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
    
    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """YouTube 영상의 자막을 추출합니다 (자동 생성 포함)."""
        try:
            # 한국어 자막 우선 시도
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # 수동 한국어 자막 찾기
                for transcript in transcript_list:
                    if transcript.language_code == 'ko' and not transcript.is_generated:
                        transcript_data = transcript.fetch()
                        return ' '.join([entry['text'] for entry in transcript_data])
                
                # 자동 생성 한국어 자막 찾기
                for transcript in transcript_list:
                    if transcript.language_code == 'ko' and transcript.is_generated:
                        transcript_data = transcript.fetch()
                        return ' '.join([entry['text'] for entry in transcript_data])
                
                # 영어 자막으로 대체 시도
                for transcript in transcript_list:
                    if transcript.language_code == 'en':
                        transcript_data = transcript.fetch()
                        return ' '.join([entry['text'] for entry in transcript_data])
                
            except Exception:
                # 직접 자막 가져오기 시도
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
                return ' '.join([entry['text'] for entry in transcript_data])
                
        except Exception as e:
            print(f"   ⚠️ 자막 추출 실패: {str(e)[:50]}...")
            return None
    
    def analyze_content_with_ai(self, title: str, transcript: str, channel_name: str) -> Dict:
        """AI를 사용하여 영상 내용을 분석합니다."""
        if not self.ai_enabled:
            return {
                "summary": f"'{title}' - 자막 기반 분석 (AI 분석 불가)",
                "key_insights": ["자막이 추출되었습니다"],
                "sentiment": "neutral",
                "importance": 0.5,
                "topics": ["일반"]
            }
        
        try:
            # 자막이 너무 길면 처음 2000자만 사용
            content_to_analyze = transcript[:2000] if transcript else title
            
            prompt = f"""
다음은 YouTube 채널 '{channel_name}'의 영상 '{title}'의 내용입니다.

내용:
{content_to_analyze}

위 내용을 분석하여 다음 JSON 형식으로 응답해주세요:
{{
    "summary": "한국어로 3-4문장의 핵심 요약",
    "key_insights": ["핵심 인사이트 1", "핵심 인사이트 2", "핵심 인사이트 3"],
    "sentiment": "positive/negative/neutral",
    "importance": 0.0-1.0 사이의 중요도 점수,
    "topics": ["주요 주제1", "주요 주제2"]
}}

투자, 경제, 시장 관련 내용에 특히 주목해주세요.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"   ⚠️ AI 분석 실패: {e}")
            return {
                "summary": f"'{title}' - {channel_name}의 최신 영상",
                "key_insights": ["영상 분석 중 오류 발생"],
                "sentiment": "neutral", 
                "importance": 0.5,
                "topics": ["일반"]
            }
    
    def check_and_analyze_updates(self, hours_back=24, max_videos_per_channel=2):
        """구독 채널 업데이트를 확인하고 분석합니다."""
        print(f"🔍 최근 {hours_back}시간 구독 채널 분석 시작...")
        
        db = SessionLocal()
        
        try:
            channels = db.query(Channel).all()
            print(f"   📺 총 {len(channels)}개 채널 분석 중")
            
            analyzed_updates = []
            total_videos = 0
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for channel in channels:
                print(f"   🔍 {channel.channel_name} 분석 중...")
                
                try:
                    # 최근 영상 검색
                    search_response = self.youtube.search().list(
                        part="snippet",
                        channelId=channel.channel_id,
                        maxResults=max_videos_per_channel,
                        order="date",
                        type="video",
                        publishedAfter=cutoff_time.isoformat() + 'Z'
                    ).execute()
                    
                    if not search_response['items']:
                        print(f"      💤 새 영상 없음")
                        continue
                    
                    channel_videos = []
                    
                    for item in search_response['items']:
                        video_id = item['id']['videoId']
                        title = item['snippet']['title']
                        
                        print(f"      📹 '{title[:30]}...' 분석 중")
                        
                        # 자막 추출
                        transcript = self.get_video_transcript(video_id)
                        if transcript:
                            print(f"         ✅ 자막 추출 성공 ({len(transcript)}자)")
                        else:
                            print(f"         ⚠️ 자막 없음")
                        
                        # AI 분석
                        analysis = self.analyze_content_with_ai(
                            title, transcript or "", channel.channel_name
                        )
                        
                        video_info = {
                            'video_id': video_id,
                            'title': title,
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'published_at': item['snippet']['publishedAt'],
                            'transcript_available': bool(transcript),
                            'transcript_length': len(transcript) if transcript else 0,
                            'analysis': analysis
                        }
                        
                        channel_videos.append(video_info)
                        total_videos += 1
                        print(f"         🎯 분석 완료 (중요도: {analysis['importance']:.2f})")
                    
                    if channel_videos:
                        analyzed_updates.append({
                            'channel_name': channel.channel_name,
                            'video_count': len(channel_videos),
                            'videos': channel_videos
                        })
                
                except Exception as e:
                    print(f"      ❌ {channel.channel_name} 분석 실패: {str(e)[:50]}...")
                    continue
            
            return {
                'total_videos': total_videos,
                'channel_updates': analyzed_updates,
                'hours_back': hours_back,
                'analysis_time': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ 전체 분석 중 오류: {e}")
            return None
        finally:
            db.close()
    
    def generate_smart_report(self, analysis_data: Dict) -> str:
        """분석 데이터를 바탕으로 스마트 리포트를 생성합니다."""
        if analysis_data['total_videos'] == 0:
            return f"📺 구독 채널 스마트 리포트\n\n💤 최근 {analysis_data['hours_back']}시간간 새로운 영상이 없습니다."
        
        # 중요도별 영상 정렬
        all_videos = []
        for channel_update in analysis_data['channel_updates']:
            for video in channel_update['videos']:
                video['channel_name'] = channel_update['channel_name']
                all_videos.append(video)
        
        # 중요도 순으로 정렬
        all_videos.sort(key=lambda x: x['analysis']['importance'], reverse=True)
        
        # 리포트 생성
        report = f"📊 구독 채널 스마트 리포트\n"
        report += f"🆕 총 {analysis_data['total_videos']}개 새 영상 분석 완료!\n\n"
        
        # 🔥 주요 영상 (상위 3개)
        report += "🔥 **주요 영상 TOP 3**\n"
        for i, video in enumerate(all_videos[:3], 1):
            importance = video['analysis']['importance']
            title = video['title'][:40] + "..." if len(video['title']) > 40 else video['title']
            report += f"{i}. **[{video['channel_name']}]** {title}\n"
            report += f"   📊 중요도: {importance:.2f} | 💭 {video['analysis']['sentiment']}\n"
            report += f"   💡 {video['analysis']['summary'][:80]}...\n"
            report += f"   🔗 [영상 보기]({video['url']})\n\n"
        
        # 📊 채널별 요약
        report += "📺 **채널별 업데이트**\n"
        for update in analysis_data['channel_updates']:
            avg_importance = sum(v['analysis']['importance'] for v in update['videos']) / len(update['videos'])
            report += f"• **{update['channel_name']}**: {update['video_count']}개 영상"
            report += f" (평균 중요도: {avg_importance:.2f})\n"
        
        # 🎯 핵심 인사이트
        all_insights = []
        for video in all_videos[:5]:  # 상위 5개 영상의 인사이트
            all_insights.extend(video['analysis']['key_insights'])
        
        if all_insights:
            report += f"\n🎯 **핵심 인사이트**\n"
            for i, insight in enumerate(all_insights[:4], 1):
                report += f"{i}. {insight}\n"
        
        # 📈 주요 토픽
        all_topics = []
        for video in all_videos:
            all_topics.extend(video['analysis']['topics'])
        
        topic_count = {}
        for topic in all_topics:
            topic_count[topic] = topic_count.get(topic, 0) + 1
        
        sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_topics:
            report += f"\n📈 **주요 토픽**: "
            report += ", ".join([f"{topic}({count})" for topic, count in sorted_topics[:5]])
        
        report += f"\n\n⏰ 분석 시간: {analysis_data['analysis_time'].strftime('%Y-%m-%d %H:%M')}"
        
        return report
    
    def send_telegram_report(self, report: str) -> bool:
        """텔레그램으로 스마트 리포트를 전송합니다."""
        if not self.telegram_token or not self.telegram_chat_id:
            print("❌ 텔레그램 설정이 없습니다.")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # 메시지가 너무 길면 분할
        max_length = 4000
        if len(report) <= max_length:
            messages = [report]
        else:
            # 섹션별로 분할
            sections = report.split('\n\n')
            messages = []
            current_message = ""
            
            for section in sections:
                if len(current_message + section) < max_length:
                    current_message += section + "\n\n"
                else:
                    if current_message:
                        messages.append(current_message.strip())
                    current_message = section + "\n\n"
            
            if current_message:
                messages.append(current_message.strip())
        
        # 메시지 전송
        success_count = 0
        for i, message in enumerate(messages):
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            try:
                response = requests.post(url, data=data)
                if response.status_code == 200:
                    success_count += 1
                    if len(messages) > 1:
                        print(f"✅ 리포트 {i+1}/{len(messages)} 전송 성공")
                else:
                    print(f"❌ 메시지 {i+1} 전송 실패: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 메시지 {i+1} 전송 중 오류: {e}")
        
        if success_count == len(messages):
            print("✅ 스마트 리포트 전송 완료!")
            return True
        else:
            print(f"⚠️ {success_count}/{len(messages)} 메시지만 전송됨")
            return False
    
    def run_smart_analysis(self, hours_back=24, send_telegram=True):
        """스마트 분석 전체 사이클을 실행합니다."""
        start_time = datetime.now()
        print(f"🚀 구독 채널 스마트 분석 시작 ({start_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 1. 업데이트 확인 및 분석
        analysis_data = self.check_and_analyze_updates(hours_back)
        
        if not analysis_data:
            print("❌ 분석 실패")
            return False
        
        # 2. 스마트 리포트 생성
        report = self.generate_smart_report(analysis_data)
        
        print(f"\n📋 생성된 스마트 리포트:")
        print("=" * 60)
        print(report)
        print("=" * 60)
        
        # 3. 텔레그램 전송
        if send_telegram and analysis_data['total_videos'] > 0:
            print(f"\n📤 텔레그램 리포트 전송 중...")
            telegram_success = self.send_telegram_report(report)
        else:
            print(f"\n💤 업데이트가 없어 텔레그램 전송을 건너뜁니다.")
            telegram_success = True
        
        # 4. 결과 요약
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n🎉 스마트 분석 완료!")
        print(f"   ⏱️ 소요 시간: {duration:.1f}초")
        print(f"   📹 분석된 영상: {analysis_data['total_videos']}개")
        print(f"   🧠 AI 분석: {'활성화' if self.ai_enabled else '비활성화'}")
        print(f"   📤 텔레그램: {'성공' if telegram_success else '실패'}")
        
        return True

def main():
    """메인 실행 함수"""
    reporter = SmartSubscriptionReporter()
    
    # 최근 24시간 스마트 분석 실행
    success = reporter.run_smart_analysis(
        hours_back=24,
        send_telegram=True
    )
    
    if success:
        print("\n✅ 구독 채널 스마트 리포트 시스템이 성공적으로 작동했습니다!")
    else:
        print("\n❌ 스마트 리포트 시스템에 문제가 발생했습니다.")

if __name__ == "__main__":
    main() 