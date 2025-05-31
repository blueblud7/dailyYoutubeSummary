import os
import logging
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv('config.env')

class YouTubeService:
    def __init__(self):
        self.api_keys = os.getenv("YOUTUBE_API_KEYS", "").split(",")
        self.current_key_index = 0
        self.youtube = None
        self.logger = logging.getLogger(__name__)
        self._build_service()
    
    def _build_service(self):
        """현재 API 키로 YouTube 서비스 객체를 생성합니다."""
        if self.current_key_index < len(self.api_keys):
            api_key = self.api_keys[self.current_key_index].strip()
            if api_key:  # API 키가 있는 경우에만 빌드
                self.youtube = build('youtube', 'v3', developerKey=api_key)
                self.logger.info(f"API 키 {self.current_key_index + 1} 사용 중")
            else:
                self.logger.error("API 키가 설정되지 않았습니다.")
    
    def _switch_api_key(self):
        """API 할당량 초과 시 다음 API 키로 전환합니다."""
        self.current_key_index += 1
        if self.current_key_index < len(self.api_keys):
            self._build_service()
            self.logger.info(f"API 키 {self.current_key_index + 1}로 전환")
            return True
        else:
            self.logger.error("모든 API 키의 할당량이 소진되었습니다")
            return False
    
    def _handle_quota_exceeded(self, error):
        """할당량 초과 에러 처리"""
        if "quotaExceeded" in str(error):
            return self._switch_api_key()
        return False
    
    def search_channels(self, query: str, max_results: int = 10) -> List[Dict]:
        """채널을 검색합니다."""
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="channel",
                maxResults=max_results
            )
            response = request.execute()
            
            channels = []
            for item in response['items']:
                channel_info = {
                    'channel_id': item['id']['channelId'],
                    'channel_name': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail_url': item['snippet']['thumbnails']['default']['url'],
                    'published_at': item['snippet']['publishedAt']
                }
                channels.append(channel_info)
            
            return channels
            
        except Exception as e:
            if self._handle_quota_exceeded(e):
                return self.search_channels(query, max_results)
            self.logger.error(f"채널 검색 중 오류 발생: {e}")
            return []
    
    def get_channel_details(self, channel_id: str) -> Optional[Dict]:
        """채널의 상세 정보를 가져옵니다."""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                return {
                    'channel_id': channel_id,
                    'channel_name': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
                    'video_count': int(item['statistics'].get('videoCount', 0)),
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'channel_url': f"https://www.youtube.com/channel/{channel_id}",
                    'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                }
            return None
            
        except Exception as e:
            if self._handle_quota_exceeded(e):
                return self.get_channel_details(channel_id)
            self.logger.error(f"채널 정보 조회 중 오류 발생: {e}")
            return None
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50, 
                          published_after: Optional[datetime] = None) -> List[Dict]:
        """채널의 비디오 목록을 가져옵니다."""
        try:
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_request = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response['items']:
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                playlist_request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                playlist_response = playlist_request.execute()
                
                video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
                
                # 비디오 상세 정보 가져오기
                videos_request = self.youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=",".join(video_ids)
                )
                videos_response = videos_request.execute()
                
                for video in videos_response['items']:
                    published_at = datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00'))
                    
                    # 날짜 필터링 (timezone-aware 비교)
                    if published_after:
                        if published_after.tzinfo is None:
                            from datetime import timezone
                            published_after = published_after.replace(tzinfo=timezone.utc)
                        if published_at < published_after:
                            continue
                    
                    video_info = {
                        'video_id': video['id'],
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'],
                        'published_at': published_at,
                        'duration': video['contentDetails']['duration'],
                        'view_count': int(video['statistics'].get('viewCount', 0)),
                        'like_count': int(video['statistics'].get('likeCount', 0)),
                        'comment_count': int(video['statistics'].get('commentCount', 0)),
                        'video_url': f"https://www.youtube.com/watch?v={video['id']}",
                        'thumbnail_url': video['snippet']['thumbnails']['default']['url'],
                        'tags': video['snippet'].get('tags', [])
                    }
                    videos.append(video_info)
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos[:max_results]
            
        except Exception as e:
            if self._handle_quota_exceeded(e):
                return self.get_channel_videos(channel_id, max_results, published_after)
            self.logger.error(f"비디오 목록 조회 중 오류 발생: {e}")
            return []
    
    def search_videos_by_keyword(self, keyword: str, max_results: int = 50,
                                published_after: Optional[datetime] = None) -> List[Dict]:
        """키워드로 비디오를 검색합니다."""
        try:
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "maxResults": min(50, max_results),
                "order": "relevance"
            }
            
            if published_after:
                if published_after.tzinfo is None:
                    from datetime import timezone
                    published_after = published_after.replace(tzinfo=timezone.utc)
                search_params["publishedAfter"] = published_after.isoformat().replace('+00:00', 'Z')
            
            request = self.youtube.search().list(**search_params)
            response = request.execute()
            
            video_ids = [item['id']['videoId'] for item in response['items']]
            
            # 비디오 상세 정보 가져오기
            videos_request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids)
            )
            videos_response = videos_request.execute()
            
            videos = []
            for video in videos_response['items']:
                published_at = datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00'))
                video_info = {
                    'video_id': video['id'],
                    'channel_id': video['snippet']['channelId'],
                    'channel_name': video['snippet']['channelTitle'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'published_at': published_at,
                    'duration': video['contentDetails']['duration'],
                    'view_count': int(video['statistics'].get('viewCount', 0)),
                    'like_count': int(video['statistics'].get('likeCount', 0)),
                    'comment_count': int(video['statistics'].get('commentCount', 0)),
                    'video_url': f"https://www.youtube.com/watch?v={video['id']}",
                    'thumbnail_url': video['snippet']['thumbnails']['default']['url'],
                    'tags': video['snippet'].get('tags', [])
                }
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            if self._handle_quota_exceeded(e):
                return self.search_videos_by_keyword(keyword, max_results, published_after)
            self.logger.error(f"키워드 검색 중 오류 발생: {e}")
            return []
    
    def get_video_transcript(self, video_id: str, language: str = 'ko') -> Optional[Dict]:
        """비디오의 자막을 가져옵니다."""
        try:
            self.logger.info(f"🔍 자막 검색 시작: video_id={video_id}, 언어={language}")
            
            # 자막 목록 가져오기
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript_text = ""
            is_auto_generated = False
            final_language = language
            
            # 시도할 언어 목록 (우선순위대로)
            language_priorities = [
                [language],  # 요청된 언어 (한국어)
                ['en'],      # 영어
                ['ja'],      # 일본어
                ['zh', 'zh-cn', 'zh-tw'],  # 중국어
            ]
            
            found_transcript = False
            
            # 1단계: 자동생성 자막을 먼저 시도 (더 안정적)
            self.logger.info("🤖 자동생성 자막 우선 검색 중...")
            for lang_list in language_priorities:
                if found_transcript:
                    break
                try:
                    transcript = transcript_list.find_generated_transcript(lang_list)
                    transcript_data = transcript.fetch()
                    transcript_text = " ".join([entry['text'] for entry in transcript_data])
                    is_auto_generated = True
                    final_language = transcript.language_code
                    found_transcript = True
                    self.logger.info(f"✅ 자동생성 자막 발견: {final_language}")
                    break
                except NoTranscriptFound:
                    continue
                except Exception as e:
                    self.logger.warning(f"자동생성 자막 가져오기 실패 ({lang_list}): {e}")
                    continue
            
            # 2단계: 자동생성 자막이 없으면 수동 자막 시도
            if not found_transcript:
                self.logger.info("📝 수동 자막 검색 중...")
                for lang_list in language_priorities:
                    if found_transcript:
                        break
                    try:
                        transcript = transcript_list.find_manually_created_transcript(lang_list)
                        transcript_data = transcript.fetch()
                        transcript_text = " ".join([entry['text'] for entry in transcript_data])
                        is_auto_generated = False
                        final_language = transcript.language_code
                        found_transcript = True
                        self.logger.info(f"✅ 수동 자막 발견: {final_language}")
                        break
                    except NoTranscriptFound:
                        continue
                    except Exception as e:
                        self.logger.warning(f"수동 자막 가져오기 실패 ({lang_list}): {e}")
                        continue
            
            # 3단계: 모든 우선순위 언어에서 자막을 찾지 못한 경우
            if not found_transcript:
                # 사용 가능한 자막 목록 확인
                available_transcripts = []
                for transcript in transcript_list:
                    transcript_type = 'auto' if transcript.is_generated else 'manual'
                    available_transcripts.append(f"{transcript.language_code}({transcript_type})")
                
                self.logger.warning(f"비디오 {video_id}: 우선순위 언어에서 자막을 찾을 수 없습니다.")
                self.logger.info(f"사용 가능한 자막: {', '.join(available_transcripts) if available_transcripts else '없음'}")
                
                # 4단계: 마지막 시도 - 사용 가능한 첫 번째 자막 사용 (자동생성 자막 우선)
                if available_transcripts:
                    try:
                        # 자동생성 자막 먼저 찾기
                        auto_transcript = None
                        manual_transcript = None
                        
                        for transcript in transcript_list:
                            if transcript.is_generated and auto_transcript is None:
                                auto_transcript = transcript
                            elif not transcript.is_generated and manual_transcript is None:
                                manual_transcript = transcript
                        
                        # 자동생성 자막이 있으면 우선 사용
                        chosen_transcript = auto_transcript if auto_transcript else manual_transcript
                        
                        if chosen_transcript:
                            try:
                                transcript_data = chosen_transcript.fetch()
                                transcript_text = " ".join([entry['text'] for entry in transcript_data])
                                is_auto_generated = chosen_transcript.is_generated
                                final_language = chosen_transcript.language_code
                                found_transcript = True
                                transcript_type = "자동생성" if is_auto_generated else "수동"
                                self.logger.info(f"✅ 대체 자막 사용: {final_language} ({transcript_type})")
                            except Exception as e:
                                self.logger.error(f"비디오 {video_id}: 대체 자막 XML 파싱 실패: {e}")
                                # XML 파싱이 실패하면 다른 자막 시도
                                if auto_transcript and chosen_transcript == auto_transcript and manual_transcript:
                                    try:
                                        self.logger.info("자동생성 자막 실패, 수동 자막 시도...")
                                        transcript_data = manual_transcript.fetch()
                                        transcript_text = " ".join([entry['text'] for entry in transcript_data])
                                        is_auto_generated = False
                                        final_language = manual_transcript.language_code
                                        found_transcript = True
                                        self.logger.info(f"✅ 수동 자막으로 대체: {final_language}")
                                    except Exception as e2:
                                        self.logger.error(f"수동 자막도 실패: {e2}")
                                        return None
                                else:
                                    return None
                        
                    except Exception as e:
                        self.logger.error(f"비디오 {video_id}: 대체 자막 가져오기 실패: {e}")
                        return None
                else:
                    self.logger.error(f"비디오 {video_id}: 사용 가능한 자막이 전혀 없습니다")
                    return None
            
            if found_transcript and transcript_text:
                return {
                    'video_id': video_id,
                    'transcript_text': transcript_text,
                    'is_auto_generated': is_auto_generated,
                    'language': final_language
                }
            else:
                self.logger.warning(f"비디오 {video_id}: 자막 텍스트가 비어있습니다")
                return None
            
        except TranscriptsDisabled:
            self.logger.warning(f"비디오 {video_id}의 자막이 비활성화되어 있습니다")
            return None
        except Exception as e:
            self.logger.error(f"자막 조회 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """YouTube 영상 정보 가져오기"""
        try:
            self.logger.info(f"🔍 영상 정보 요청 시작: video_id={video_id}")
            
            # YouTube API로 영상 정보 가져오기
            video_request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            video_response = video_request.execute()
            
            self.logger.info(f"📊 API 응답 받음: items 개수={len(video_response.get('items', []))}")
            
            if not video_response['items']:
                self.logger.warning(f"⚠️ 영상 ID {video_id}에 대한 정보가 없습니다")
                return None
            
            video_info = video_response['items'][0]
            snippet = video_info['snippet']
            
            self.logger.info(f"✅ 영상 정보 추출 완료: title={snippet['title'][:50]}...")
            
            return {
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'channel_name': snippet['channelTitle'],
                'channel_id': snippet['channelId'],
                'published_at': snippet['publishedAt'],
                'view_count': int(video_info['statistics'].get('viewCount', 0)),
                'like_count': int(video_info['statistics'].get('likeCount', 0)),
                'comment_count': int(video_info['statistics'].get('commentCount', 0)),
            }
            
        except Exception as e:
            if self._handle_quota_exceeded(e):
                return self.get_video_info(video_id)
            self.logger.error(f"❌ 영상 정보 가져오기 실패: {e}")
            return None 