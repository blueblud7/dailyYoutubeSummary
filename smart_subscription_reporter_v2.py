#!/usr/bin/env python3
"""
구독 채널 업데이트 확인 + 자막 추출 + AI 분석 + 완전한 요약 리포트 생성 (개선 버전 + 캐시 시스템)
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models.database import SessionLocal, Channel
from app.services.video_cache_service import VideoCacheService
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

class SmartSubscriptionReporterV2:
    def __init__(self):
        self.api_keys = os.getenv("YOUTUBE_API_KEYS", "").split(",")
        self.api_keys = [key.strip() for key in self.api_keys if key.strip()]  # 빈 키 제거
        self.current_key_index = 0
        self.youtube = None
        self._init_youtube_api()
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # 캐시 서비스 초기화
        self.cache_service = VideoCacheService()
        print("📊 캐시 서비스 초기화 완료")
        
        # OpenAI 클라이언트 초기화
        if OPENAI_AVAILABLE:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key and api_key.startswith('sk-'):
                    self.openai_client = OpenAI(api_key=api_key)
                    self.ai_enabled = True
                    print("✅ AI 분석 기능이 활성화되었습니다.")
                else:
                    print("⚠️ OpenAI API 키가 유효하지 않습니다.")
                    self.ai_enabled = False
            except Exception as e:
                print(f"⚠️ OpenAI 초기화 실패: {e}")
                self.ai_enabled = False
        else:
            print("⚠️ OpenAI 라이브러리를 사용할 수 없습니다.")
            self.ai_enabled = False
        
        # 캐시 통계 출력
        self._print_cache_stats()
    
    def _init_youtube_api(self):
        """YouTube API 클라이언트 초기화"""
        if not self.api_keys:
            print("❌ YouTube API 키가 설정되지 않았습니다.")
            return
        
        try:
            current_key = self.api_keys[self.current_key_index]
            self.youtube = build('youtube', 'v3', developerKey=current_key)
            print(f"✅ YouTube API 초기화 완료 (키 {self.current_key_index + 1}/{len(self.api_keys)})")
        except Exception as e:
            print(f"⚠️ YouTube API 초기화 실패: {e}")
    
    def _rotate_api_key(self):
        """다음 API 키로 순환"""
        if len(self.api_keys) <= 1:
            print("⚠️ 사용 가능한 다른 API 키가 없습니다.")
            return False
        
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        try:
            current_key = self.api_keys[self.current_key_index]
            self.youtube = build('youtube', 'v3', developerKey=current_key)
            print(f"🔄 API 키 순환 완료 (키 {self.current_key_index + 1}/{len(self.api_keys)})")
            return True
        except Exception as e:
            print(f"⚠️ API 키 순환 실패: {e}")
            return False
    
    def _execute_youtube_api_with_retry(self, api_call, max_retries=3):
        """YouTube API 호출을 재시도와 키 순환으로 실행"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return api_call()
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # 할당량 초과 또는 403 에러 시 키 순환
                if "quota" in error_str.lower() or "403" in error_str:
                    print(f"   🔄 할당량 초과 감지, API 키 순환 시도 (시도 {attempt + 1}/{max_retries})")
                    if self._rotate_api_key():
                        continue
                    else:
                        break
                else:
                    print(f"   ⚠️ API 호출 오류: {str(e)[:50]}...")
                    break
        
        print(f"   ❌ API 호출 최종 실패: {str(last_error)[:50]}...")
        raise last_error
    
    def _print_cache_stats(self):
        """캐시 통계 출력"""
        try:
            stats = self.cache_service.get_cache_statistics()
            if stats:
                print(f"📈 캐시 통계: 전체 영상 {stats.get('total_videos', 0)}개, "
                      f"캐시된 분석 {stats.get('cached_analyses', 0)}개 "
                      f"(히트율: {stats.get('cache_hit_rate', 0)}%)")
        except Exception as e:
            print(f"⚠️ 캐시 통계 조회 실패: {e}")
    
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
    
    def analyze_content_with_ai(self, title: str, transcript: str, channel_name: str, video_id: str) -> Dict:
        """
        AI를 사용하여 영상 내용을 매우 상세하게 분석합니다.
        캐시된 결과가 있으면 우선 사용하여 API 사용량을 최적화합니다.
        """
        # 1. 캐시된 분석 결과 확인
        cached_result = self.cache_service.get_cached_analysis(video_id)
        if cached_result:
            print(f"         🎯 캐시된 분석 결과 사용 (API 절약!)")
            return cached_result
        
        # 2. AI 분석이 비활성화된 경우
        if not self.ai_enabled:
            result = {
                "summary": f"'{title}' - 자막이 성공적으로 추출되었습니다. AI 분석이 비활성화되어 있어 상세 분석을 제공할 수 없습니다.",
                "key_insights": ["자막 추출 성공", "투자 관련 콘텐츠", "분석 대기 중"],
                "sentiment": "neutral",
                "importance": 0.5,
                "topics": ["투자", "분석"]
            }
            return result
        
        # 3. 새로운 AI 분석 수행
        print(f"         🤖 새로운 AI 분석 수행 중...")
        try:
            # 전체 자막 사용 (최대 15000자까지 확장)
            content_to_analyze = transcript[:15000] if transcript else title
            
            prompt = f"""
다음은 YouTube 채널 '{channel_name}'의 영상 '{title}'의 자막 전문입니다. 
이 내용을 투자/경제 전문가 관점에서 매우 상세하게 분석하여 시청자가 영상을 보지 않아도 충분히 이해할 수 있도록 포괄적인 분석을 제공해주세요.

영상 제목: {title}
채널명: {channel_name}
자막 내용:
{content_to_analyze}

다음 JSON 형식으로 상세한 분석을 제공해주세요:
{{
    "executive_summary": "영상의 핵심 내용을 10-15문장으로 매우 상세하게 요약 (스토리라인, 주요 논점, 결론까지 포함)",
    "detailed_insights": [
        "구체적이고 실용적인 핵심 인사이트 1 (숫자, 데이터, 구체적 사례 포함)",
        "구체적이고 실용적인 핵심 인사이트 2 (숫자, 데이터, 구체적 사례 포함)",
        "구체적이고 실용적인 핵심 인사이트 3 (숫자, 데이터, 구체적 사례 포함)",
        "구체적이고 실용적인 핵심 인사이트 4 (숫자, 데이터, 구체적 사례 포함)",
        "구체적이고 실용적인 핵심 인사이트 5 (숫자, 데이터, 구체적 사례 포함)"
    ],
    "market_analysis": {{
        "current_situation": "현재 시장 상황에 대한 상세 분석",
        "future_outlook": "미래 시장 전망 및 예측",
        "risk_factors": ["리스크 요인 1", "리스크 요인 2", "리스크 요인 3"],
        "opportunities": ["기회 요인 1", "기회 요인 2", "기회 요인 3"]
    }},
    "investment_implications": {{
        "short_term": "단기 투자 관점에서의 시사점",
        "long_term": "장기 투자 관점에서의 시사점",
        "sectors_to_watch": ["주목해야 할 섹터 1", "주목해야 할 섹터 2", "주목해야 할 섹터 3"],
        "specific_recommendations": ["구체적 투자 제안 1", "구체적 투자 제안 2"]
    }},
    "key_data_points": [
        "영상에서 언급된 중요한 수치나 데이터 1",
        "영상에서 언급된 중요한 수치나 데이터 2",
        "영상에서 언급된 중요한 수치나 데이터 3"
    ],
    "expert_opinions": [
        "영상에서 제시된 전문가 의견이나 분석 1",
        "영상에서 제시된 전문가 의견이나 분석 2"
    ],
    "historical_context": "언급된 역사적 맥락이나 과거 사례 분석",
    "actionable_steps": [
        "투자자가 즉시 취할 수 있는 구체적 행동 1",
        "투자자가 즉시 취할 수 있는 구체적 행동 2",
        "투자자가 즉시 취할 수 있는 구체적 행동 3"
    ],
    "sentiment": "positive/negative/neutral/mixed",
    "importance": 0.0-1.0 사이의 중요도 점수,
    "confidence_level": 0.0-1.0 사이의 분석 신뢰도,
    "topics": ["주요 키워드 1", "주요 키워드 2", "주요 키워드 3", "주요 키워드 4"],
    "related_companies": ["언급된 기업명들"],
    "economic_indicators": ["언급된 경제지표들"],
    "time_sensitive_info": "시간에 민감한 정보가 있다면 명시"
}}

분석 시 중요 포인트:
1. 영상의 전체 스토리를 파악하고 논리적 흐름을 설명
2. 구체적인 숫자, 데이터, 사례를 최대한 많이 포함
3. 투자자 관점에서 실제로 활용 가능한 정보 제공
4. 단순한 요약이 아닌 깊이 있는 분석과 해석 포함
5. 시장 영향도와 투자 시사점을 명확히 구분
6. 영상을 보지 않아도 충분히 이해할 수 있는 수준의 상세함
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 더 강력한 모델 사용
                messages=[
                    {"role": "system", "content": "당신은 투자 및 경제 분야의 전문 분석가입니다. YouTube 영상의 내용을 매우 상세하고 포괄적으로 분석하여 시청자가 영상을 보지 않아도 충분히 이해할 수 있는 수준의 분석을 제공해야 합니다. 반드시 유효한 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,  # 토큰 수 대폭 증가
                temperature=0.2  # 더 일관된 분석을 위해 낮춤
            )
            
            content = response.choices[0].message.content.strip()
            print(f"         📤 OpenAI 응답 길이: {len(content)}자")
            
            # JSON 파싱 전에 내용 확인
            if not content:
                raise ValueError("OpenAI에서 빈 응답을 받았습니다.")
            
            # JSON 형식이 아닌 경우를 위한 처리
            if not content.startswith('{'):
                # JSON 부분만 추출 시도
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]
                else:
                    raise ValueError("유효한 JSON을 찾을 수 없습니다")
            
            result = json.loads(content)
            
            # 기존 형식과의 호환성을 위한 필드 매핑
            legacy_result = {
                "summary": result.get("executive_summary", "상세 분석을 확인하세요."),
                "key_insights": result.get("detailed_insights", [])[:4],  # 기존 호환성
                "sentiment": result.get("sentiment", "neutral"),
                "importance": result.get("importance", 0.5),
                "topics": result.get("topics", []),
                "market_impact": result.get("market_analysis", {}).get("current_situation", "분석 중"),
                "action_items": result.get("actionable_steps", [])[:2],
                # 새로운 상세 분석 필드들
                "detailed_analysis": result
            }
            
            # 4. 분석 결과를 캐시에 저장
            self.cache_service.save_analysis_result(video_id, legacy_result, "gpt-4o-mini")
            print(f"         💾 분석 결과 캐시 저장 완료")
            
            return legacy_result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON 파싱 실패: {e}")
            print(f"   📄 응답 내용: {content[:200]}...")
            result = {
                "summary": f"'{title}' 영상은 {channel_name} 채널의 최신 콘텐츠입니다. AI 분석 중 JSON 파싱 오류가 발생했습니다.",
                "key_insights": ["AI 응답 형식 오류", "수동 검토 필요", "자막 데이터 확보"],
                "sentiment": "neutral", 
                "importance": 0.5,
                "topics": ["일반"],
                "market_impact": "분석 대기 중",
                "action_items": ["영상 직접 확인 권장"]
            }
            return result
        except Exception as e:
            print(f"   ⚠️ AI 분석 실패: {e}")
            result = {
                "summary": f"'{title}' 영상은 {channel_name} 채널의 최신 콘텐츠입니다. 자막이 추출되어 내용 분석이 가능하지만, AI 분석 중 기술적 문제가 발생했습니다.",
                "key_insights": ["영상 분석 중 오류 발생", "수동 검토 필요", "자막 데이터 확보"],
                "sentiment": "neutral", 
                "importance": 0.5,
                "topics": ["일반"],
                "market_impact": "분석 대기 중",
                "action_items": ["영상 직접 확인 권장"]
            }
            return result
    
    def check_and_analyze_updates(self, hours_back=24, max_videos_per_channel=2):
        """구독 채널 업데이트를 확인하고 상세 분석합니다."""
        print(f"🔍 최근 {hours_back}시간 구독 채널 상세 분석 시작...")
        
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
                    # 최근 영상 검색 (키 순환 로직 적용)
                    def search_videos():
                        return self.youtube.search().list(
                            part="snippet",
                            channelId=channel.channel_id,
                            maxResults=max_videos_per_channel,
                            order="date",
                            type="video",
                            publishedAfter=cutoff_time.isoformat() + 'Z'
                        ).execute()
                    
                    search_response = self._execute_youtube_api_with_retry(search_videos)
                    
                    if not search_response['items']:
                        print(f"      💤 새 영상 없음")
                        continue
                    
                    channel_videos = []
                    
                    for item in search_response['items']:
                        video_id = item['id']['videoId']
                        title = item['snippet']['title']
                        
                        print(f"      📹 '{title[:40]}...' 상세 분석 중")
                        
                        # 영상 정보 준비
                        video_info_for_db = {
                            'video_id': video_id,
                            'channel_id': channel.channel_id,
                            'title': title,
                            'description': item['snippet'].get('description', ''),
                            'published_at': datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00')),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'thumbnail_url': item['snippet']['thumbnails'].get('default', {}).get('url', '')
                        }
                        
                        # 자막 추출
                        transcript = self.get_video_transcript(video_id)
                        if transcript:
                            print(f"         ✅ 자막 추출 성공 ({len(transcript):,}자)")
                        else:
                            print(f"         ⚠️ 자막 없음")
                        
                        # 영상 정보와 자막을 DB에 저장
                        try:
                            save_success = self.cache_service.save_video_data(video_info_for_db, transcript)
                            if save_success:
                                print(f"         💾 영상 데이터 DB 저장 완료")
                            else:
                                print(f"         ⚠️ 영상 데이터 DB 저장 실패")
                        except Exception as e:
                            print(f"         ⚠️ DB 저장 중 오류: {str(e)[:30]}...")
                        
                        # AI 상세 분석 (캐시 우선 사용)
                        analysis = self.analyze_content_with_ai(
                            title, transcript or "", channel.channel_name, video_id
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
                        print(f"         🎯 상세 분석 완료 (중요도: {analysis['importance']:.2f})")
                    
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
    
    def generate_detailed_report(self, analysis_data: Dict) -> str:
        """분석 데이터를 바탕으로 매우 상세한 리포트를 생성합니다."""
        if analysis_data['total_videos'] == 0:
            return f"📺 구독 채널 상세 리포트\n\n💤 최근 {analysis_data['hours_back']}시간간 새로운 영상이 없습니다."
        
        # 중요도별 영상 정렬
        all_videos = []
        for channel_update in analysis_data['channel_updates']:
            for video in channel_update['videos']:
                video['channel_name'] = channel_update['channel_name']
                all_videos.append(video)
        
        # 중요도 순으로 정렬
        all_videos.sort(key=lambda x: x['analysis']['importance'], reverse=True)
        
        # 리포트 생성 (매우 상세하게)
        report = f"📊 구독 채널 상세 분석 리포트\n"
        report += f"🆕 총 {analysis_data['total_videos']}개 새 영상 AI 분석 완료!\n\n"
        
        # 🔥 최고 중요도 영상 (상위 3개) - 완전한 분석 포함
        report += "🔥 **최고 중요도 영상 상세 분석**\n\n"
        for i, video in enumerate(all_videos[:3], 1):
            analysis = video['analysis']
            detailed = analysis.get('detailed_analysis', {})
            
            importance = analysis['importance']
            confidence = detailed.get('confidence_level', 0.8)
            title = video['title'][:80] + "..." if len(video['title']) > 80 else video['title']
            
            report += f"**{i}. [{video['channel_name']}] {title}**\n"
            report += f"📊 중요도: {importance:.2f} | 💭 감정: {analysis['sentiment']} | 🎯 신뢰도: {confidence:.2f}\n"
            report += f"📺 자막 길이: {video.get('transcript_length', 0):,}자\n\n"
            
            # 상세 요약 (Executive Summary)
            if detailed.get('executive_summary'):
                report += f"📋 **종합 요약:**\n{detailed['executive_summary']}\n\n"
            
            # 핵심 인사이트 (Detailed Insights)
            if detailed.get('detailed_insights'):
                report += f"💡 **핵심 인사이트:**\n"
                for j, insight in enumerate(detailed['detailed_insights'][:5], 1):
                    report += f"{j}. {insight}\n"
                report += "\n"
            
            # 시장 분석 (Market Analysis)
            market_analysis = detailed.get('market_analysis', {})
            if market_analysis:
                report += f"📈 **시장 분석:**\n"
                if market_analysis.get('current_situation'):
                    report += f"• **현재 상황:** {market_analysis['current_situation']}\n"
                if market_analysis.get('future_outlook'):
                    report += f"• **미래 전망:** {market_analysis['future_outlook']}\n"
                
                if market_analysis.get('risk_factors'):
                    report += f"• **리스크 요인:** {', '.join(market_analysis['risk_factors'][:3])}\n"
                if market_analysis.get('opportunities'):
                    report += f"• **기회 요인:** {', '.join(market_analysis['opportunities'][:3])}\n"
                report += "\n"
            
            # 투자 시사점 (Investment Implications)
            investment = detailed.get('investment_implications', {})
            if investment:
                report += f"💰 **투자 시사점:**\n"
                if investment.get('short_term'):
                    report += f"• **단기:** {investment['short_term']}\n"
                if investment.get('long_term'):
                    report += f"• **장기:** {investment['long_term']}\n"
                if investment.get('sectors_to_watch'):
                    report += f"• **주목 섹터:** {', '.join(investment['sectors_to_watch'][:3])}\n"
                if investment.get('specific_recommendations'):
                    report += f"• **구체적 제안:** {'; '.join(investment['specific_recommendations'][:2])}\n"
                report += "\n"
            
            # 핵심 데이터 포인트
            if detailed.get('key_data_points'):
                report += f"📊 **핵심 데이터:**\n"
                for data_point in detailed['key_data_points'][:3]:
                    report += f"• {data_point}\n"
                report += "\n"
            
            # 전문가 의견
            if detailed.get('expert_opinions'):
                report += f"🎓 **전문가 의견:**\n"
                for opinion in detailed['expert_opinions'][:2]:
                    report += f"• {opinion}\n"
                report += "\n"
            
            # 역사적 맥락
            if detailed.get('historical_context'):
                report += f"📚 **역사적 맥락:** {detailed['historical_context']}\n\n"
            
            # 실행 가능한 단계
            if detailed.get('actionable_steps'):
                report += f"✅ **실행 단계:**\n"
                for j, step in enumerate(detailed['actionable_steps'][:3], 1):
                    report += f"{j}. {step}\n"
                report += "\n"
            
            # 관련 기업 및 경제지표
            if detailed.get('related_companies') or detailed.get('economic_indicators'):
                report += f"🏢 **관련 정보:**\n"
                if detailed.get('related_companies'):
                    companies = ', '.join(detailed['related_companies'][:5])
                    report += f"• **관련 기업:** {companies}\n"
                if detailed.get('economic_indicators'):
                    indicators = ', '.join(detailed['economic_indicators'][:5])
                    report += f"• **경제지표:** {indicators}\n"
                report += "\n"
            
            # 시간 민감 정보
            if detailed.get('time_sensitive_info'):
                report += f"⏰ **시간 민감 정보:** {detailed['time_sensitive_info']}\n\n"
            
            report += f"🔗 [영상 보기]({video['url']})\n"
            report += "═" * 80 + "\n\n"
        
        # 전체 영상에 대한 종합 분석
        if len(all_videos) > 3:
            report += f"📋 **기타 분석된 영상 ({len(all_videos)-3}개)**\n\n"
            for i, video in enumerate(all_videos[3:], 4):
                title = video['title'][:60] + "..." if len(video['title']) > 60 else video['title']
                importance = video['analysis']['importance']
                sentiment = video['analysis']['sentiment']
                
                report += f"**{i}. [{video['channel_name']}] {title}**\n"
                report += f"📊 중요도: {importance:.2f} | 💭 감정: {sentiment}\n"
                
                # 간단한 요약만 포함
                summary = video['analysis']['summary'][:200] + "..." if len(video['analysis']['summary']) > 200 else video['analysis']['summary']
                report += f"📝 **요약:** {summary}\n"
                report += f"🔗 [영상 보기]({video['url']})\n"
                report += "─" * 50 + "\n\n"
        
        return report
    
    def generate_summary_report(self, analysis_data: Dict) -> str:
        """요약 버전 리포트를 생성합니다."""
        if analysis_data['total_videos'] == 0:
            return f"📺 구독 채널 요약 리포트\n\n💤 최근 {analysis_data['hours_back']}시간간 새로운 영상이 없습니다."
        
        # 중요도별 영상 정렬
        all_videos = []
        for channel_update in analysis_data['channel_updates']:
            for video in channel_update['videos']:
                video['channel_name'] = channel_update['channel_name']
                all_videos.append(video)
        
        all_videos.sort(key=lambda x: x['analysis']['importance'], reverse=True)
        
        report = f"📋 구독 채널 요약 리포트\n"
        report += f"🆕 총 {analysis_data['total_videos']}개 영상 분석\n\n"
        
        # 📊 채널별 요약
        report += "📺 **채널별 업데이트**\n"
        for update in analysis_data['channel_updates']:
            if update['videos']:
                avg_importance = sum(v['analysis']['importance'] for v in update['videos']) / len(update['videos'])
                report += f"• **{update['channel_name']}**: {update['video_count']}개 영상 (중요도: {avg_importance:.2f})\n"
        
        # 🎯 종합 인사이트
        all_insights = []
        for video in all_videos[:5]:  # 상위 5개 영상의 인사이트
            all_insights.extend(video['analysis']['key_insights'])
        
        if all_insights:
            report += f"\n🎯 **종합 핵심 인사이트**\n"
            unique_insights = list(dict.fromkeys(all_insights))  # 중복 제거
            for i, insight in enumerate(unique_insights[:5], 1):
                report += f"{i}. {insight}\n"
        
        # 📈 주요 토픽 분석
        all_topics = []
        for video in all_videos:
            all_topics.extend(video['analysis']['topics'])
        
        topic_count = {}
        for topic in all_topics:
            topic_count[topic] = topic_count.get(topic, 0) + 1
        
        sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_topics:
            report += f"\n📈 **주요 토픽**: "
            report += ", ".join([f"{topic}({count})" for topic, count in sorted_topics[:6]])
        
        # 🔥 최고 중요도 영상 링크
        report += f"\n\n🔥 **최고 중요도 영상**\n"
        for i, video in enumerate(all_videos[:3], 1):
            title = video['title'][:45] + "..." if len(video['title']) > 45 else video['title']
            report += f"{i}. [{video['channel_name']}] {title}\n"
            report += f"   [영상 보기]({video['url']})\n"
        
        report += f"\n⏰ 분석 시간: {analysis_data['analysis_time'].strftime('%Y-%m-%d %H:%M')}"
        
        return report
    
    def send_telegram_reports(self, detailed_report: str, summary_report: str) -> bool:
        """텔레그램으로 상세 리포트와 요약 리포트를 모두 전송합니다."""
        if not self.telegram_token or not self.telegram_chat_id:
            print("❌ 텔레그램 설정이 없습니다.")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # 1. 요약 리포트 먼저 전송
        print("📤 요약 리포트 전송 중...")
        summary_data = {
            'chat_id': self.telegram_chat_id,
            'text': summary_report,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=summary_data)
            if response.status_code == 200:
                print("✅ 요약 리포트 전송 성공!")
            else:
                print(f"❌ 요약 리포트 전송 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 요약 리포트 전송 중 오류: {e}")
            return False
        
        # 2. 상세 리포트를 분할하여 전송
        print("📤 상세 리포트 전송 중...")
        
        # 상세 리포트를 영상별로 분할
        sections = detailed_report.split("═" * 80)
        
        messages = []
        if sections:
            # 첫 번째 섹션 (헤더)
            messages.append(sections[0].strip())
            
            # 나머지 섹션들 (각 영상)
            for section in sections[1:]:
                if section.strip():
                    messages.append(section.strip())
        
        # 메시지 전송
        success_count = 0
        for i, message in enumerate(messages):
            if not message.strip():
                continue
                
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
                    print(f"✅ 상세 리포트 {i+1}/{len(messages)} 전송 성공")
                else:
                    print(f"❌ 상세 리포트 {i+1} 전송 실패: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 상세 리포트 {i+1} 전송 중 오류: {e}")
        
        return success_count > 0
    
    def run_detailed_analysis(self, hours_back=24, send_telegram=True):
        """상세 분석 전체 사이클을 실행합니다."""
        start_time = datetime.now()
        print(f"🚀 구독 채널 상세 분석 시작 ({start_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 캐시 통계 출력 (분석 전)
        print(f"\n📊 캐시 상태 (분석 전):")
        self._print_detailed_cache_stats()
        
        # 1. 업데이트 확인 및 상세 분석
        analysis_data = self.check_and_analyze_updates(hours_back)
        
        if not analysis_data:
            print("❌ 분석 실패")
            return False
        
        # 캐시 통계 출력 (분석 후)
        print(f"\n📊 캐시 상태 (분석 후):")
        self._print_detailed_cache_stats()
        
        # 2. 상세 리포트와 요약 리포트 생성
        detailed_report = self.generate_detailed_report(analysis_data)
        summary_report = self.generate_summary_report(analysis_data)
        
        print(f"\n📋 생성된 요약 리포트:")
        print("=" * 60)
        print(summary_report)
        print("=" * 60)
        
        print(f"\n📄 생성된 상세 리포트 (일부):")
        print("=" * 60)
        print(detailed_report[:1000] + "..." if len(detailed_report) > 1000 else detailed_report)
        print("=" * 60)
        
        # 3. 텔레그램 전송
        if send_telegram and analysis_data['total_videos'] > 0:
            print(f"\n📤 텔레그램 리포트 전송 중...")
            telegram_success = self.send_telegram_reports(detailed_report, summary_report)
        else:
            print(f"\n💤 업데이트가 없어 텔레그램 전송을 건너뜁니다.")
            telegram_success = True
        
        # 4. 캐시 정리 (30일 이상 된 데이터)
        try:
            cleaned_count = self.cache_service.clean_old_cache(30)
            if cleaned_count > 0:
                print(f"\n🧹 오래된 캐시 {cleaned_count}개 정리 완료")
        except Exception as e:
            print(f"\n⚠️ 캐시 정리 중 오류: {e}")
        
        # 5. 결과 요약
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n🎉 상세 분석 완료!")
        print(f"   ⏱️ 소요 시간: {duration:.1f}초")
        print(f"   📹 분석된 영상: {analysis_data['total_videos']}개")
        print(f"   🧠 AI 분석: {'활성화' if self.ai_enabled else '비활성화'}")
        print(f"   📤 텔레그램: {'성공' if telegram_success else '실패'}")
        
        # 최종 캐시 통계
        final_stats = self.cache_service.get_cache_statistics()
        if final_stats:
            cache_hit_rate = final_stats.get('cache_hit_rate', 0)
            print(f"   💾 캐시 히트율: {cache_hit_rate}% (API 비용 절약!)")
        
        return True
    
    def _print_detailed_cache_stats(self):
        """상세한 캐시 통계 출력"""
        try:
            stats = self.cache_service.get_cache_statistics()
            if stats:
                print(f"   📹 전체 영상: {stats.get('total_videos', 0)}개")
                print(f"   🎯 캐시된 분석: {stats.get('cached_analyses', 0)}개")
                print(f"   📝 자막 보유: {stats.get('total_transcripts', 0)}개")
                print(f"   🆕 최근 7일 분석: {stats.get('recent_analyses', 0)}개")
                print(f"   📊 캐시 히트율: {stats.get('cache_hit_rate', 0)}%")
                
                # API 절약 계산
                total_videos = stats.get('total_videos', 0)
                cached_analyses = stats.get('cached_analyses', 0)
                if total_videos > 0:
                    api_savings = (cached_analyses / total_videos) * 100
                    print(f"   💰 예상 API 비용 절약: {api_savings:.1f}%")
        except Exception as e:
            print(f"   ⚠️ 캐시 통계 조회 실패: {e}")

def main():
    """메인 실행 함수"""
    reporter = SmartSubscriptionReporterV2()
    
    # 최근 24시간 상세 분석 실행
    success = reporter.run_detailed_analysis(
        hours_back=24,
        send_telegram=True
    )
    
    if success:
        print("\n✅ 구독 채널 상세 리포트 시스템이 성공적으로 작동했습니다!")
    else:
        print("\n❌ 상세 리포트 시스템에 문제가 발생했습니다.")

if __name__ == "__main__":
    main() 