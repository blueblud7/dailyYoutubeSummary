import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.database import get_db, Channel, Video, Transcript, Analysis, Keyword, PersonInfluencer
from app.services.youtube_service import YouTubeService
from app.services.analysis_service import AnalysisService
import json

class DataCollector:
    def __init__(self):
        self.youtube_service = YouTubeService()
        self.analysis_service = AnalysisService()
        self.logger = logging.getLogger(__name__)
    
    def add_channel(self, channel_id: str, db: Session) -> Optional[Channel]:
        """새로운 채널을 데이터베이스에 추가합니다."""
        
        # 이미 존재하는 채널인지 확인
        existing_channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
        if existing_channel:
            self.logger.info(f"채널 {channel_id}는 이미 존재합니다.")
            return existing_channel
        
        # 채널 정보 가져오기
        channel_data = self.youtube_service.get_channel_details(channel_id)
        if not channel_data:
            self.logger.error(f"채널 {channel_id} 정보를 가져올 수 없습니다.")
            return None
        
        # 데이터베이스에 저장
        channel = Channel(
            channel_id=channel_data['channel_id'],
            channel_name=channel_data['channel_name'],
            channel_url=channel_data['channel_url'],
            description=channel_data['description'],
            subscriber_count=channel_data['subscriber_count'],
            video_count=channel_data['video_count']
        )
        
        db.add(channel)
        db.commit()
        db.refresh(channel)
        
        self.logger.info(f"채널 '{channel_data['channel_name']}' 추가 완료")
        return channel
    
    def add_keywords(self, keywords: List[str], category: str, db: Session) -> List[Keyword]:
        """키워드들을 데이터베이스에 추가합니다."""
        
        keyword_objects = []
        for keyword in keywords:
            existing_keyword = db.query(Keyword).filter(Keyword.keyword == keyword).first()
            if not existing_keyword:
                keyword_obj = Keyword(keyword=keyword, category=category)
                db.add(keyword_obj)
                keyword_objects.append(keyword_obj)
            else:
                keyword_objects.append(existing_keyword)
        
        db.commit()
        return keyword_objects
    
    def collect_channel_videos(self, channel_id: str, days_back: int = 7, db: Session = None) -> List[Video]:
        """특정 채널의 최근 비디오들을 수집합니다."""
        
        published_after = datetime.now() - timedelta(days=days_back)
        videos_data = self.youtube_service.get_channel_videos(
            channel_id, max_results=50, published_after=published_after
        )
        
        collected_videos = []
        for video_data in videos_data:
            # 이미 존재하는 비디오인지 확인
            existing_video = db.query(Video).filter(Video.video_id == video_data['video_id']).first()
            if existing_video:
                continue
            
            # 비디오 정보 저장
            video = Video(
                video_id=video_data['video_id'],
                channel_id=channel_id,
                title=video_data['title'],
                description=video_data['description'],
                published_at=video_data['published_at'],
                duration=video_data['duration'],
                view_count=video_data['view_count'],
                like_count=video_data['like_count'],
                comment_count=video_data['comment_count'],
                video_url=video_data['video_url'],
                thumbnail_url=video_data['thumbnail_url'],
                tags=json.dumps(video_data['tags'])
            )
            
            db.add(video)
            collected_videos.append(video)
        
        db.commit()
        self.logger.info(f"채널 {channel_id}에서 {len(collected_videos)}개 비디오 수집 완료")
        return collected_videos
    
    def collect_keyword_videos(self, keyword: str, days_back: int = 7, db: Session = None) -> List[Video]:
        """특정 키워드로 비디오를 검색하여 수집합니다."""
        
        published_after = datetime.now() - timedelta(days=days_back)
        videos_data = self.youtube_service.search_videos_by_keyword(
            keyword, max_results=30, published_after=published_after
        )
        
        collected_videos = []
        for video_data in videos_data:
            # 이미 존재하는 비디오인지 확인
            existing_video = db.query(Video).filter(Video.video_id == video_data['video_id']).first()
            if existing_video:
                continue
            
            # 채널 정보도 함께 저장
            channel_id = video_data['channel_id']
            existing_channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            if not existing_channel:
                self.add_channel(channel_id, db)
            
            # 비디오 정보 저장
            video = Video(
                video_id=video_data['video_id'],
                channel_id=channel_id,
                title=video_data['title'],
                description=video_data['description'],
                published_at=video_data['published_at'],
                duration=video_data['duration'],
                view_count=video_data['view_count'],
                like_count=video_data['like_count'],
                comment_count=video_data['comment_count'],
                video_url=video_data['video_url'],
                thumbnail_url=video_data['thumbnail_url'],
                tags=json.dumps(video_data['tags'])
            )
            
            db.add(video)
            collected_videos.append(video)
        
        db.commit()
        self.logger.info(f"키워드 '{keyword}'로 {len(collected_videos)}개 비디오 수집 완료")
        return collected_videos
    
    def collect_video_transcripts(self, videos: List[Video], db: Session) -> List[Transcript]:
        """비디오들의 자막을 수집합니다."""
        
        collected_transcripts = []
        for video in videos:
            # 이미 자막이 있는지 확인
            existing_transcript = db.query(Transcript).filter(
                Transcript.video_id == video.video_id
            ).first()
            
            if existing_transcript:
                continue
            
            # 자막 가져오기
            transcript_data = self.youtube_service.get_video_transcript(video.video_id)
            if transcript_data:
                transcript = Transcript(
                    video_id=transcript_data['video_id'],
                    transcript_text=transcript_data['transcript_text'],
                    is_auto_generated=transcript_data['is_auto_generated'],
                    language=transcript_data['language']
                )
                
                db.add(transcript)
                collected_transcripts.append(transcript)
                self.logger.info(f"비디오 {video.video_id} 자막 수집 완료")
            else:
                self.logger.warning(f"비디오 {video.video_id} 자막 수집 실패")
        
        db.commit()
        return collected_transcripts
    
    def analyze_videos(self, videos: List[Video], keywords: List[str], db: Session) -> List[Analysis]:
        """비디오들을 분석하여 인사이트를 추출합니다."""
        
        analyses = []
        for video in videos:
            # 이미 분석이 있는지 확인
            existing_analysis = db.query(Analysis).filter(
                Analysis.video_id == video.video_id
            ).first()
            
            if existing_analysis:
                continue
            
            # 자막 가져오기
            transcript = db.query(Transcript).filter(
                Transcript.video_id == video.video_id
            ).first()
            
            # 분석용 텍스트 준비
            analysis_text = ""
            if transcript and transcript.transcript_text:
                analysis_text = transcript.transcript_text
                self.logger.info(f"비디오 {video.video_id}: 자막 사용하여 분석")
            else:
                # 자막이 없으면 제목과 설명 사용
                analysis_text = f"제목: {video.title}\n\n설명: {video.description[:1000] if video.description else '설명 없음'}"
                self.logger.info(f"비디오 {video.video_id}: 자막이 없어 제목/설명으로 분석")
            
            if not analysis_text.strip():
                self.logger.warning(f"비디오 {video.video_id}에 분석할 텍스트가 없어 건너뜁니다.")
                continue
            
            # 채널 정보 가져오기
            channel = db.query(Channel).filter(
                Channel.channel_id == video.channel_id
            ).first()
            
            channel_name = channel.channel_name if channel else "Unknown"
            
            # AI 분석 수행
            analysis_result = self.analysis_service.analyze_transcript(
                analysis_text,
                video.title,
                channel_name,
                keywords
            )
            
            # 키워드별로 분석 저장
            for keyword in keywords:
                keyword_obj = db.query(Keyword).filter(Keyword.keyword == keyword).first()
                if keyword_obj:
                    analysis = Analysis(
                        video_id=video.video_id,
                        keyword_id=keyword_obj.id,
                        summary=analysis_result['summary'],
                        sentiment_score=analysis_result['sentiment_score'],
                        key_insights=json.dumps(analysis_result['key_insights']),
                        importance_score=analysis_result['importance_score'],
                        mentioned_entities=json.dumps(analysis_result['mentioned_entities'])
                    )
                    
                    db.add(analysis)
                    analyses.append(analysis)
            
            self.logger.info(f"비디오 {video.video_id} 분석 완료")
        
        db.commit()
        return analyses
    
    def run_daily_collection(self, channel_ids: List[str], keywords: List[str], 
                           keyword_category: str = "투자", db: Session = None) -> Dict:
        """일일 데이터 수집 및 분석을 실행합니다."""
        
        self.logger.info("일일 데이터 수집 시작")
        
        # 키워드 추가/업데이트
        keyword_objects = self.add_keywords(keywords, keyword_category, db)
        
        collected_videos = []
        
        # 채널별 비디오 수집
        for channel_id in channel_ids:
            channel = self.add_channel(channel_id, db)
            if channel:
                videos = self.collect_channel_videos(channel_id, days_back=1, db=db)
                collected_videos.extend(videos)
        
        # 키워드별 비디오 수집
        for keyword in keywords:
            videos = self.collect_keyword_videos(keyword, days_back=1, db=db)
            collected_videos.extend(videos)
        
        # 중복 제거
        unique_videos = list({video.video_id: video for video in collected_videos}.values())
        
        # 자막 수집
        transcripts = self.collect_video_transcripts(unique_videos, db)
        
        # 자막이 있는 비디오만 분석
        videos_with_transcripts = [
            video for video in unique_videos 
            if db.query(Transcript).filter(Transcript.video_id == video.video_id).first()
        ]
        
        # 분석 수행
        analyses = self.analyze_videos(videos_with_transcripts, keywords, db)
        
        result = {
            "collection_date": datetime.now().isoformat(),
            "total_videos_collected": len(unique_videos),
            "transcripts_collected": len(transcripts),
            "analyses_performed": len(analyses),
            "channels_processed": len(channel_ids),
            "keywords_processed": keywords
        }
        
        self.logger.info(f"일일 수집 완료: {result}")
        return result 