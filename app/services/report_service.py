import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.database import Video, Analysis, Channel, Keyword, Report
from app.services.analysis_service import AnalysisService
import os

class ReportService:
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.logger = logging.getLogger(__name__)
    
    def get_period_analyses(self, db: Session, start_date: datetime, 
                          end_date: datetime, keywords: List[str] = None) -> List[Dict]:
        """특정 기간의 분석 결과를 가져옵니다."""
        
        query = db.query(Analysis).join(Video).filter(
            and_(
                Video.published_at >= start_date,
                Video.published_at <= end_date
            )
        )
        
        if keywords:
            keyword_ids = db.query(Keyword.id).filter(Keyword.keyword.in_(keywords)).all()
            keyword_ids = [kid[0] for kid in keyword_ids]
            query = query.filter(Analysis.keyword_id.in_(keyword_ids))
        
        analyses = query.all()
        
        # 분석 결과를 딕셔너리 형태로 변환
        analysis_dicts = []
        for analysis in analyses:
            video = db.query(Video).filter(Video.video_id == analysis.video_id).first()
            channel = db.query(Channel).filter(Channel.channel_id == video.channel_id).first()
            keyword = db.query(Keyword).filter(Keyword.id == analysis.keyword_id).first()
            
            analysis_dict = {
                'summary': analysis.summary,
                'sentiment_score': analysis.sentiment_score,
                'importance_score': analysis.importance_score,
                'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else [],
                'video_title': video.title,
                'channel_name': channel.channel_name if channel else 'Unknown',
                'keyword': keyword.keyword if keyword else 'Unknown',
                'published_at': video.published_at,
                'video_url': video.video_url
            }
            analysis_dicts.append(analysis_dict)
        
        return analysis_dicts
    
    def get_top_videos(self, db: Session, start_date: datetime, 
                      end_date: datetime, limit: int = 10) -> List[Dict]:
        """특정 기간의 주요 비디오들을 가져옵니다."""
        
        videos = db.query(Video).filter(
            and_(
                Video.published_at >= start_date,
                Video.published_at <= end_date
            )
        ).order_by(Video.view_count.desc()).limit(limit).all()
        
        video_dicts = []
        for video in videos:
            channel = db.query(Channel).filter(Channel.channel_id == video.channel_id).first()
            analysis = db.query(Analysis).filter(Analysis.video_id == video.video_id).first()
            
            video_dict = {
                'title': video.title,
                'channel_name': channel.channel_name if channel else 'Unknown',
                'view_count': video.view_count,
                'like_count': video.like_count,
                'published_at': video.published_at,
                'video_url': video.video_url,
                'importance_score': analysis.importance_score if analysis else 0,
                'sentiment_score': analysis.sentiment_score if analysis else 0
            }
            video_dicts.append(video_dict)
        
        return video_dicts
    
    def get_channel_perspectives(self, db: Session, topic_keywords: List[str], 
                               start_date: datetime, end_date: datetime) -> Dict[str, List[Dict]]:
        """특정 주제에 대한 채널별 관점을 수집합니다."""
        
        # 키워드 관련 분석들 가져오기
        keyword_ids = db.query(Keyword.id).filter(Keyword.keyword.in_(topic_keywords)).all()
        keyword_ids = [kid[0] for kid in keyword_ids]
        
        analyses = db.query(Analysis).join(Video).filter(
            and_(
                Analysis.keyword_id.in_(keyword_ids),
                Video.published_at >= start_date,
                Video.published_at <= end_date
            )
        ).all()
        
        # 채널별로 그룹화
        channel_analyses = {}
        for analysis in analyses:
            video = db.query(Video).filter(Video.video_id == analysis.video_id).first()
            channel = db.query(Channel).filter(Channel.channel_id == video.channel_id).first()
            
            if channel:
                channel_name = channel.channel_name
                if channel_name not in channel_analyses:
                    channel_analyses[channel_name] = []
                
                analysis_dict = {
                    'summary': analysis.summary,
                    'sentiment_score': analysis.sentiment_score,
                    'importance_score': analysis.importance_score,
                    'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                    'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else []
                }
                channel_analyses[channel_name].append(analysis_dict)
        
        return channel_analyses
    
    def generate_daily_report(self, db: Session, target_date: datetime = None, 
                            keywords: List[str] = None) -> Dict:
        """일일 투자 인사이트 리포트를 생성합니다."""
        
        if not target_date:
            target_date = datetime.now().date()
        
        start_date = datetime.combine(target_date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        # 해당 날짜의 분석 결과 가져오기
        analyses = self.get_period_analyses(db, start_date, end_date, keywords)
        
        if not analyses:
            return {
                "report_type": "daily",
                "date": target_date.isoformat(),
                "message": "해당 날짜에 분석할 데이터가 없습니다."
            }
        
        # 주요 비디오들 가져오기
        top_videos = self.get_top_videos(db, start_date, end_date, limit=10)
        
        # 트렌드 분석 생성
        trend_analysis = self.analysis_service.generate_trend_analysis(
            analyses, keywords or [], "당일"
        )
        
        # 일일 리포트 생성
        daily_report = self.analysis_service.generate_daily_report(
            trend_analysis, top_videos, start_date
        )
        
        # 데이터베이스에 저장
        report = Report(
            report_type="daily",
            title=daily_report['title'],
            content=json.dumps(daily_report),
            summary=daily_report['executive_summary'],
            key_trends=json.dumps(trend_analysis['key_themes']),
            market_sentiment=trend_analysis['market_sentiment'],
            recommendations=json.dumps(daily_report['action_items']),
            date_range_start=start_date,
            date_range_end=end_date
        )
        
        db.add(report)
        db.commit()
        
        return {
            "report_type": "daily",
            "date": target_date.isoformat(),
            "report_id": report.id,
            "trend_analysis": trend_analysis,
            "daily_report": daily_report,
            "statistics": {
                "total_videos_analyzed": len(analyses),
                "total_channels": len(set([a['channel_name'] for a in analyses])),
                "avg_sentiment": sum([a['sentiment_score'] for a in analyses]) / len(analyses),
                "top_videos_count": len(top_videos)
            }
        }
    
    def generate_weekly_report(self, db: Session, end_date: datetime = None, 
                             keywords: List[str] = None) -> Dict:
        """주간 투자 인사이트 리포트를 생성합니다."""
        
        if not end_date:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=7)
        
        # 주간 분석 결과 가져오기
        analyses = self.get_period_analyses(db, start_date, end_date, keywords)
        
        if not analyses:
            return {
                "report_type": "weekly",
                "message": "해당 주간에 분석할 데이터가 없습니다."
            }
        
        # 주요 비디오들
        top_videos = self.get_top_videos(db, start_date, end_date, limit=15)
        
        # 트렌드 분석
        trend_analysis = self.analysis_service.generate_trend_analysis(
            analyses, keywords or [], "최근 7일"
        )
        
        # 채널별 관점 비교 (주요 키워드에 대해)
        perspective_comparisons = {}
        if keywords:
            for keyword in keywords[:3]:  # 상위 3개 키워드만
                channel_perspectives = self.get_channel_perspectives(
                    db, [keyword], start_date, end_date
                )
                if channel_perspectives:
                    comparison = self.analysis_service.compare_perspectives(
                        keyword, channel_perspectives
                    )
                    perspective_comparisons[keyword] = comparison
        
        # 주간 통계
        weekly_stats = {
            "total_videos": len(analyses),
            "total_channels": len(set([a['channel_name'] for a in analyses])),
            "avg_sentiment": sum([a['sentiment_score'] for a in analyses]) / len(analyses),
            "sentiment_distribution": {
                "positive": len([a for a in analyses if a['sentiment_score'] > 0.1]),
                "neutral": len([a for a in analyses if -0.1 <= a['sentiment_score'] <= 0.1]),
                "negative": len([a for a in analyses if a['sentiment_score'] < -0.1])
            },
            "top_entities": self._get_top_entities(analyses, 10)
        }
        
        report_content = {
            "trend_analysis": trend_analysis,
            "perspective_comparisons": perspective_comparisons,
            "top_videos": top_videos,
            "weekly_statistics": weekly_stats
        }
        
        # 데이터베이스에 저장
        report = Report(
            report_type="weekly",
            title=f"주간 투자 인사이트 리포트 ({start_date.strftime('%Y.%m.%d')} - {end_date.strftime('%Y.%m.%d')})",
            content=json.dumps(report_content),
            summary=trend_analysis['summary'],
            key_trends=json.dumps(trend_analysis['key_themes']),
            market_sentiment=trend_analysis['market_sentiment'],
            date_range_start=start_date,
            date_range_end=end_date
        )
        
        db.add(report)
        db.commit()
        
        return {
            "report_type": "weekly",
            "period": f"{start_date.strftime('%Y.%m.%d')} - {end_date.strftime('%Y.%m.%d')}",
            "report_id": report.id,
            **report_content
        }
    
    def generate_perspective_comparison_report(self, db: Session, topic: str, 
                                             keywords: List[str], days_back: int = 7) -> Dict:
        """특정 주제에 대한 관점 비교 리포트를 생성합니다."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 채널별 관점 수집
        channel_perspectives = self.get_channel_perspectives(db, keywords, start_date, end_date)
        
        if not channel_perspectives:
            return {
                "topic": topic,
                "message": "해당 주제에 대한 분석 데이터가 없습니다."
            }
        
        # 관점 비교 분석
        comparison_result = self.analysis_service.compare_perspectives(
            topic, channel_perspectives
        )
        
        # 채널별 상세 정보
        channel_details = {}
        for channel_name, analyses in channel_perspectives.items():
            if analyses:
                avg_sentiment = sum([a['sentiment_score'] for a in analyses]) / len(analyses)
                avg_importance = sum([a['importance_score'] for a in analyses]) / len(analyses)
                
                channel_details[channel_name] = {
                    "video_count": len(analyses),
                    "avg_sentiment": avg_sentiment,
                    "avg_importance": avg_importance,
                    "key_insights": [insight for analysis in analyses for insight in analysis['key_insights']][:5],
                    "sentiment_label": self._get_sentiment_label(avg_sentiment)
                }
        
        return {
            "topic": topic,
            "period": f"{start_date.strftime('%Y.%m.%d')} - {end_date.strftime('%Y.%m.%d')}",
            "comparison_analysis": comparison_result,
            "channel_details": channel_details,
            "total_channels": len(channel_perspectives),
            "total_analyses": sum([len(analyses) for analyses in channel_perspectives.values()])
        }
    
    def _get_top_entities(self, analyses: List[Dict], limit: int = 10) -> List[Dict]:
        """분석에서 가장 많이 언급된 엔티티들을 반환합니다."""
        
        entity_counts = {}
        for analysis in analyses:
            for entity in analysis.get('mentioned_entities', []):
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"entity": entity, "count": count} for entity, count in sorted_entities[:limit]]
    
    def _get_sentiment_label(self, sentiment_score: float) -> str:
        """감정 점수를 라벨로 변환합니다."""
        if sentiment_score > 0.3:
            return "매우 긍정적"
        elif sentiment_score > 0.1:
            return "긍정적"
        elif sentiment_score > -0.1:
            return "중립적"
        elif sentiment_score > -0.3:
            return "부정적"
        else:
            return "매우 부정적"
    
    def get_report_history(self, db: Session, report_type: str = None, 
                          limit: int = 20) -> List[Dict]:
        """리포트 히스토리를 가져옵니다."""
        
        query = db.query(Report)
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        reports = query.order_by(Report.created_at.desc()).limit(limit).all()
        
        return [{
            "id": report.id,
            "report_type": report.report_type,
            "title": report.title,
            "summary": report.summary,
            "market_sentiment": report.market_sentiment,
            "date_range": f"{report.date_range_start.strftime('%Y.%m.%d')} - {report.date_range_end.strftime('%Y.%m.%d')}",
            "created_at": report.created_at.isoformat()
        } for report in reports] 