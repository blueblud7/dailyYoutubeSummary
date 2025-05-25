import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.database import (
    SessionLocal, Video, Transcript, VideoAnalysis, 
    AnalysisCache, Channel, create_tables
)

class VideoCacheService:
    """
    영상 데이터와 AI 분석 결과를 캐싱하는 서비스
    ChatGPT API 사용량을 최적화하고 전체 시스템 성능을 향상시킴
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 테이블 생성 확인
        create_tables()
    
    def _generate_cache_key(self, video_id: str, transcript_text: str) -> str:
        """영상 ID와 자막으로 캐시 키 생성"""
        transcript_hash = hashlib.md5(transcript_text.encode('utf-8')).hexdigest()[:16]
        return f"{video_id}_{transcript_hash}"
    
    def save_video_data(self, video_info: Dict, transcript_text: str = None) -> bool:
        """영상 기본 정보와 자막을 데이터베이스에 저장"""
        db = SessionLocal()
        try:
            # 기존 영상 확인
            existing_video = db.query(Video).filter(Video.video_id == video_info['video_id']).first()
            
            if existing_video:
                # 업데이트
                existing_video.title = video_info.get('title', existing_video.title)
                existing_video.description = video_info.get('description', existing_video.description)
                existing_video.view_count = video_info.get('view_count', existing_video.view_count)
                existing_video.updated_at = datetime.utcnow()
            else:
                # 새로운 영상 생성
                video = Video(
                    video_id=video_info['video_id'],
                    channel_id=video_info.get('channel_id', ''),
                    title=video_info.get('title', ''),
                    description=video_info.get('description', ''),
                    published_at=video_info.get('published_at'),
                    duration=video_info.get('duration', ''),
                    view_count=video_info.get('view_count', 0),
                    like_count=video_info.get('like_count', 0),
                    comment_count=video_info.get('comment_count', 0),
                    video_url=video_info.get('url', f"https://www.youtube.com/watch?v={video_info['video_id']}"),
                    thumbnail_url=video_info.get('thumbnail_url', ''),
                    tags=json.dumps(video_info.get('tags', []))
                )
                db.add(video)
            
            # 자막 저장 (있는 경우)
            if transcript_text:
                self._save_transcript(db, video_info['video_id'], transcript_text)
            
            db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"영상 데이터 저장 실패: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def _save_transcript(self, db: Session, video_id: str, transcript_text: str):
        """자막 데이터 저장"""
        existing_transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
        
        if existing_transcript:
            existing_transcript.transcript_text = transcript_text
            existing_transcript.transcript_length = len(transcript_text)
            existing_transcript.updated_at = datetime.utcnow()
        else:
            transcript = Transcript(
                video_id=video_id,
                transcript_text=transcript_text,
                transcript_length=len(transcript_text),
                is_auto_generated=True,  # 일단 True로 설정
                language="ko"
            )
            db.add(transcript)
    
    def save_analysis_result(self, video_id: str, analysis_result: Dict, ai_model: str = "gpt-4o-mini") -> bool:
        """AI 분석 결과를 데이터베이스에 저장"""
        db = SessionLocal()
        try:
            # 기존 분석 결과 확인
            existing_analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
            
            detailed_analysis = analysis_result.get('detailed_analysis', {})
            
            if existing_analysis:
                # 업데이트
                self._update_analysis(existing_analysis, analysis_result, detailed_analysis, ai_model)
            else:
                # 새로운 분석 생성
                video_analysis = VideoAnalysis(
                    video_id=video_id,
                    executive_summary=detailed_analysis.get('executive_summary', analysis_result.get('summary', '')),
                    sentiment=analysis_result.get('sentiment', 'neutral'),
                    importance_score=analysis_result.get('importance', 0.5),
                    confidence_level=detailed_analysis.get('confidence_level', 0.8),
                    
                    # 상세 분석 (JSON으로 저장)
                    detailed_insights=json.dumps(detailed_analysis.get('detailed_insights', []), ensure_ascii=False),
                    market_analysis=json.dumps(detailed_analysis.get('market_analysis', {}), ensure_ascii=False),
                    investment_implications=json.dumps(detailed_analysis.get('investment_implications', {}), ensure_ascii=False),
                    key_data_points=json.dumps(detailed_analysis.get('key_data_points', []), ensure_ascii=False),
                    expert_opinions=json.dumps(detailed_analysis.get('expert_opinions', []), ensure_ascii=False),
                    historical_context=detailed_analysis.get('historical_context', ''),
                    actionable_steps=json.dumps(detailed_analysis.get('actionable_steps', []), ensure_ascii=False),
                    
                    # 메타데이터
                    topics=json.dumps(analysis_result.get('topics', []), ensure_ascii=False),
                    related_companies=json.dumps(detailed_analysis.get('related_companies', []), ensure_ascii=False),
                    economic_indicators=json.dumps(detailed_analysis.get('economic_indicators', []), ensure_ascii=False),
                    time_sensitive_info=detailed_analysis.get('time_sensitive_info', ''),
                    
                    # AI 모델 정보
                    ai_model_used=ai_model,
                    analysis_version="1.0"
                )
                db.add(video_analysis)
            
            db.commit()
            
            # 캐시 정보 업데이트
            self._update_cache_info(db, video_id, ai_model)
            
            return True
            
        except Exception as e:
            self.logger.error(f"분석 결과 저장 실패: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def _update_analysis(self, existing_analysis: VideoAnalysis, analysis_result: Dict, detailed_analysis: Dict, ai_model: str):
        """기존 분석 결과 업데이트"""
        existing_analysis.executive_summary = detailed_analysis.get('executive_summary', analysis_result.get('summary', ''))
        existing_analysis.sentiment = analysis_result.get('sentiment', 'neutral')
        existing_analysis.importance_score = analysis_result.get('importance', 0.5)
        existing_analysis.confidence_level = detailed_analysis.get('confidence_level', 0.8)
        
        # 상세 분석 업데이트
        existing_analysis.detailed_insights = json.dumps(detailed_analysis.get('detailed_insights', []), ensure_ascii=False)
        existing_analysis.market_analysis = json.dumps(detailed_analysis.get('market_analysis', {}), ensure_ascii=False)
        existing_analysis.investment_implications = json.dumps(detailed_analysis.get('investment_implications', {}), ensure_ascii=False)
        existing_analysis.key_data_points = json.dumps(detailed_analysis.get('key_data_points', []), ensure_ascii=False)
        existing_analysis.expert_opinions = json.dumps(detailed_analysis.get('expert_opinions', []), ensure_ascii=False)
        existing_analysis.historical_context = detailed_analysis.get('historical_context', '')
        existing_analysis.actionable_steps = json.dumps(detailed_analysis.get('actionable_steps', []), ensure_ascii=False)
        
        # 메타데이터 업데이트
        existing_analysis.topics = json.dumps(analysis_result.get('topics', []), ensure_ascii=False)
        existing_analysis.related_companies = json.dumps(detailed_analysis.get('related_companies', []), ensure_ascii=False)
        existing_analysis.economic_indicators = json.dumps(detailed_analysis.get('economic_indicators', []), ensure_ascii=False)
        existing_analysis.time_sensitive_info = detailed_analysis.get('time_sensitive_info', '')
        
        # AI 모델 정보 업데이트
        existing_analysis.ai_model_used = ai_model
        existing_analysis.updated_at = datetime.utcnow()
    
    def _update_cache_info(self, db: Session, video_id: str, ai_model: str):
        """캐시 정보 업데이트"""
        # 자막 가져오기
        transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
        if not transcript:
            return
        
        cache_key = self._generate_cache_key(video_id, transcript.transcript_text)
        
        existing_cache = db.query(AnalysisCache).filter(AnalysisCache.video_id == video_id).first()
        
        if existing_cache:
            existing_cache.cache_key = cache_key
            existing_cache.ai_model_version = ai_model
            existing_cache.last_accessed = datetime.utcnow()
            existing_cache.access_count += 1
            existing_cache.updated_at = datetime.utcnow()
        else:
            cache = AnalysisCache(
                video_id=video_id,
                cache_key=cache_key,
                ai_model_version=ai_model
            )
            db.add(cache)
        
        db.commit()
    
    def get_cached_analysis(self, video_id: str) -> Optional[Dict]:
        """캐시된 분석 결과 가져오기"""
        db = SessionLocal()
        try:
            # 분석 결과 조회
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
            
            if not analysis:
                return None
            
            # 캐시 정보 업데이트 (접근 시간, 접근 횟수)
            cache = db.query(AnalysisCache).filter(AnalysisCache.video_id == video_id).first()
            if cache:
                cache.last_accessed = datetime.utcnow()
                cache.access_count += 1
                db.commit()
            
            # 분석 결과를 원래 형식으로 변환
            return self._convert_db_to_analysis_format(analysis)
            
        except Exception as e:
            self.logger.error(f"캐시된 분석 결과 조회 실패: {e}")
            return None
        finally:
            db.close()
    
    def _convert_db_to_analysis_format(self, analysis: VideoAnalysis) -> Dict:
        """DB 분석 결과를 원래 형식으로 변환"""
        try:
            detailed_analysis = {
                "executive_summary": analysis.executive_summary or "",
                "detailed_insights": json.loads(analysis.detailed_insights or "[]"),
                "market_analysis": json.loads(analysis.market_analysis or "{}"),
                "investment_implications": json.loads(analysis.investment_implications or "{}"),
                "key_data_points": json.loads(analysis.key_data_points or "[]"),
                "expert_opinions": json.loads(analysis.expert_opinions or "[]"),
                "historical_context": analysis.historical_context or "",
                "actionable_steps": json.loads(analysis.actionable_steps or "[]"),
                "sentiment": analysis.sentiment,
                "importance": analysis.importance_score,
                "confidence_level": analysis.confidence_level,
                "topics": json.loads(analysis.topics or "[]"),
                "related_companies": json.loads(analysis.related_companies or "[]"),
                "economic_indicators": json.loads(analysis.economic_indicators or "[]"),
                "time_sensitive_info": analysis.time_sensitive_info or ""
            }
            
            return {
                "summary": analysis.executive_summary or "",
                "key_insights": json.loads(analysis.detailed_insights or "[]")[:4],
                "sentiment": analysis.sentiment,
                "importance": analysis.importance_score,
                "topics": json.loads(analysis.topics or "[]"),
                "market_impact": json.loads(analysis.market_analysis or "{}").get("current_situation", "분석 중"),
                "action_items": json.loads(analysis.actionable_steps or "[]")[:2],
                "detailed_analysis": detailed_analysis
            }
            
        except Exception as e:
            self.logger.error(f"분석 결과 형식 변환 실패: {e}")
            return {
                "summary": "분석 결과 로드 실패",
                "key_insights": [],
                "sentiment": "neutral",
                "importance": 0.5,
                "topics": [],
                "market_impact": "분석 대기 중",
                "action_items": []
            }
    
    def is_analysis_cached(self, video_id: str) -> bool:
        """분석 결과가 캐시되어 있는지 확인"""
        db = SessionLocal()
        try:
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video_id).first()
            return analysis is not None
        except Exception as e:
            self.logger.error(f"캐시 확인 실패: {e}")
            return False
        finally:
            db.close()
    
    def get_video_with_transcript(self, video_id: str) -> Optional[Tuple[Dict, str]]:
        """영상 정보와 자막을 함께 가져오기"""
        db = SessionLocal()
        try:
            video = db.query(Video).filter(Video.video_id == video_id).first()
            if not video:
                return None
            
            transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
            transcript_text = transcript.transcript_text if transcript else ""
            
            video_info = {
                'video_id': video.video_id,
                'title': video.title,
                'channel_id': video.channel_id,
                'published_at': video.published_at,
                'url': video.video_url
            }
            
            return video_info, transcript_text
            
        except Exception as e:
            self.logger.error(f"영상 정보 조회 실패: {e}")
            return None
        finally:
            db.close()
    
    def clean_old_cache(self, days_old: int = 30) -> int:
        """오래된 캐시 정리"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_caches = db.query(AnalysisCache).filter(
                AnalysisCache.last_accessed < cutoff_date
            ).all()
            
            count = len(old_caches)
            
            for cache in old_caches:
                # 관련 분석 결과도 삭제
                analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == cache.video_id).first()
                if analysis:
                    db.delete(analysis)
                db.delete(cache)
            
            db.commit()
            self.logger.info(f"오래된 캐시 {count}개 정리 완료")
            return count
            
        except Exception as e:
            self.logger.error(f"캐시 정리 실패: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def get_cache_statistics(self) -> Dict:
        """캐시 통계 정보 반환"""
        db = SessionLocal()
        try:
            total_videos = db.query(Video).count()
            cached_analyses = db.query(VideoAnalysis).count()
            total_transcripts = db.query(Transcript).count()
            
            # 최근 1주일 분석
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_analyses = db.query(VideoAnalysis).filter(
                VideoAnalysis.created_at >= week_ago
            ).count()
            
            # 캐시 히트율 계산
            cache_hit_rate = (cached_analyses / total_videos * 100) if total_videos > 0 else 0
            
            return {
                "total_videos": total_videos,
                "cached_analyses": cached_analyses,
                "total_transcripts": total_transcripts,
                "recent_analyses": recent_analyses,
                "cache_hit_rate": round(cache_hit_rate, 2)
            }
            
        except Exception as e:
            self.logger.error(f"캐시 통계 조회 실패: {e}")
            return {}
        finally:
            db.close() 