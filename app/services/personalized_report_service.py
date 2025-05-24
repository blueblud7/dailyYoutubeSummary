import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.database import Video, Analysis, Channel, Keyword, PersonInfluencer
from app.services.analysis_service import AnalysisService
from app.services.notification_service import NotificationService

class PersonalizedReportService:
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
    
    def generate_keyword_focused_report(self, db: Session, keyword: str, 
                                      days_back: int = 1) -> Dict:
        """특정 키워드에 집중한 리포트를 생성합니다."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 키워드 관련 분석들 가져오기
        keyword_obj = db.query(Keyword).filter(Keyword.keyword == keyword).first()
        if not keyword_obj:
            return {
                "keyword": keyword,
                "message": f"'{keyword}' 키워드가 등록되지 않았습니다."
            }
        
        analyses = db.query(Analysis).join(Video).filter(
            and_(
                Analysis.keyword_id == keyword_obj.id,
                Video.published_at >= start_date,
                Video.published_at <= end_date
            )
        ).all()
        
        if not analyses:
            return {
                "keyword": keyword,
                "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
                "message": f"해당 기간에 '{keyword}' 관련 분석이 없습니다."
            }
        
        # 분석 데이터 가공
        analysis_data = []
        for analysis in analyses:
            video = db.query(Video).filter(Video.video_id == analysis.video_id).first()
            channel = db.query(Channel).filter(Channel.channel_id == video.channel_id).first()
            
            analysis_data.append({
                'summary': analysis.summary,
                'sentiment_score': analysis.sentiment_score,
                'importance_score': analysis.importance_score,
                'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else [],
                'video_title': video.title,
                'channel_name': channel.channel_name if channel else 'Unknown',
                'published_at': video.published_at,
                'video_url': video.video_url,
                'view_count': video.view_count
            })
        
        # 키워드별 트렌드 분석
        keyword_trend = self.analysis_service.generate_trend_analysis(
            analysis_data, [keyword], f"최근 {days_back}일"
        )
        
        # 채널별 관점 정리
        channel_perspectives = {}
        for data in analysis_data:
            channel_name = data['channel_name']
            if channel_name not in channel_perspectives:
                channel_perspectives[channel_name] = []
            channel_perspectives[channel_name].append(data)
        
        # 통계 정보
        statistics = {
            "total_analyses": len(analysis_data),
            "total_channels": len(channel_perspectives),
            "avg_sentiment": sum(d['sentiment_score'] for d in analysis_data) / len(analysis_data),
            "avg_importance": sum(d['importance_score'] for d in analysis_data) / len(analysis_data),
            "sentiment_distribution": {
                "positive": len([d for d in analysis_data if d['sentiment_score'] > 0.1]),
                "neutral": len([d for d in analysis_data if -0.1 <= d['sentiment_score'] <= 0.1]),
                "negative": len([d for d in analysis_data if d['sentiment_score'] < -0.1])
            }
        }
        
        return {
            "keyword": keyword,
            "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            "keyword_trend": keyword_trend,
            "channel_perspectives": channel_perspectives,
            "top_videos": sorted(analysis_data, key=lambda x: x['importance_score'], reverse=True)[:5],
            "statistics": statistics
        }
    
    def generate_influencer_focused_report(self, db: Session, influencer_name: str, 
                                         days_back: int = 7) -> Dict:
        """특정 인플루언서에 집중한 리포트를 생성합니다."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 인플루언서 정보 가져오기
        influencer = db.query(PersonInfluencer).filter(
            PersonInfluencer.name == influencer_name
        ).first()
        
        if not influencer:
            return {
                "influencer": influencer_name,
                "message": f"'{influencer_name}' 인플루언서가 등록되지 않았습니다."
            }
        
        # 해당 인플루언서가 언급된 분석들 찾기
        analyses = db.query(Analysis).join(Video).filter(
            and_(
                Video.published_at >= start_date,
                Video.published_at <= end_date,
                Analysis.mentioned_entities.like(f'%{influencer_name}%')
            )
        ).all()
        
        if not analyses:
            return {
                "influencer": influencer_name,
                "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
                "message": f"해당 기간에 '{influencer_name}' 관련 언급이 없습니다."
            }
        
        # 분석 데이터 가공
        analysis_data = []
        for analysis in analyses:
            video = db.query(Video).filter(Video.video_id == analysis.video_id).first()
            channel = db.query(Channel).filter(Channel.channel_id == video.channel_id).first()
            
            analysis_data.append({
                'summary': analysis.summary,
                'sentiment_score': analysis.sentiment_score,
                'importance_score': analysis.importance_score,
                'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else [],
                'video_title': video.title,
                'channel_name': channel.channel_name if channel else 'Unknown',
                'published_at': video.published_at,
                'video_url': video.video_url
            })
        
        # 인플루언서 언급 분석
        mention_analysis = self._analyze_influencer_mentions(analysis_data, influencer_name)
        
        return {
            "influencer": influencer_name,
            "specialty": influencer.specialty if influencer else "전문 분야 미상",
            "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            "mention_analysis": mention_analysis,
            "related_videos": sorted(analysis_data, key=lambda x: x['importance_score'], reverse=True)[:10],
            "statistics": {
                "total_mentions": len(analysis_data),
                "avg_sentiment": sum(d['sentiment_score'] for d in analysis_data) / len(analysis_data),
                "channels_mentioned": len(set(d['channel_name'] for d in analysis_data))
            }
        }
    
    def generate_channel_focused_report(self, db: Session, channel_name: str, 
                                      days_back: int = 7) -> Dict:
        """특정 채널에 집중한 리포트를 생성합니다."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 채널 정보 가져오기
        channel = db.query(Channel).filter(Channel.channel_name == channel_name).first()
        
        if not channel:
            return {
                "channel": channel_name,
                "message": f"'{channel_name}' 채널이 등록되지 않았습니다."
            }
        
        # 해당 채널의 비디오들과 분석 가져오기
        videos = db.query(Video).filter(
            and_(
                Video.channel_id == channel.channel_id,
                Video.published_at >= start_date,
                Video.published_at <= end_date
            )
        ).all()
        
        if not videos:
            return {
                "channel": channel_name,
                "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
                "message": f"해당 기간에 '{channel_name}' 채널의 영상이 없습니다."
            }
        
        # 비디오별 분석 데이터 수집
        video_analyses = []
        for video in videos:
            analyses = db.query(Analysis).filter(Analysis.video_id == video.video_id).all()
            
            for analysis in analyses:
                keyword = db.query(Keyword).filter(Keyword.id == analysis.keyword_id).first()
                
                video_analyses.append({
                    'video_title': video.title,
                    'published_at': video.published_at,
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'video_url': video.video_url,
                    'summary': analysis.summary,
                    'sentiment_score': analysis.sentiment_score,
                    'importance_score': analysis.importance_score,
                    'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                    'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else [],
                    'keyword': keyword.keyword if keyword else 'Unknown'
                })
        
        if not video_analyses:
            return {
                "channel": channel_name,
                "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
                "message": f"해당 기간에 '{channel_name}' 채널의 분석이 없습니다."
            }
        
        # 채널 트렌드 분석
        channel_trend = self.analysis_service.generate_trend_analysis(
            video_analyses, [], f"최근 {days_back}일"
        )
        
        # 채널 통계
        statistics = {
            "total_videos": len(videos),
            "total_analyses": len(video_analyses),
            "avg_views": sum(v.view_count for v in videos) / len(videos),
            "avg_sentiment": sum(va['sentiment_score'] for va in video_analyses) / len(video_analyses),
            "most_mentioned_entities": self._get_top_entities(video_analyses, 10),
            "content_keywords": list(set(va['keyword'] for va in video_analyses))
        }
        
        return {
            "channel": channel_name,
            "subscriber_count": channel.subscriber_count,
            "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            "channel_trend": channel_trend,
            "top_videos": sorted(video_analyses, key=lambda x: x['importance_score'], reverse=True)[:5],
            "recent_videos": sorted(video_analyses, key=lambda x: x['published_at'], reverse=True)[:10],
            "statistics": statistics
        }
    
    def generate_multi_dimension_report(self, db: Session, keywords: List[str] = None,
                                      channels: List[str] = None, 
                                      influencers: List[str] = None,
                                      days_back: int = 7) -> Dict:
        """다차원 개인화 리포트를 생성합니다."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        report_sections = {}
        
        # 키워드별 분석
        if keywords:
            keyword_reports = {}
            for keyword in keywords:
                keyword_reports[keyword] = self.generate_keyword_focused_report(
                    db, keyword, days_back
                )
            report_sections['keywords'] = keyword_reports
        
        # 채널별 분석
        if channels:
            channel_reports = {}
            for channel in channels:
                channel_reports[channel] = self.generate_channel_focused_report(
                    db, channel, days_back
                )
            report_sections['channels'] = channel_reports
        
        # 인플루언서별 분석
        if influencers:
            influencer_reports = {}
            for influencer in influencers:
                influencer_reports[influencer] = self.generate_influencer_focused_report(
                    db, influencer, days_back
                )
            report_sections['influencers'] = influencer_reports
        
        # 종합 인사이트 생성
        overall_insights = self._generate_overall_insights(report_sections)
        
        return {
            "report_type": "multi_dimension",
            "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            "sections": report_sections,
            "overall_insights": overall_insights,
            "generated_at": datetime.now().isoformat()
        }
    
    def _analyze_influencer_mentions(self, analysis_data: List[Dict], 
                                   influencer_name: str) -> Dict:
        """인플루언서 언급 분석"""
        
        mention_contexts = []
        sentiment_scores = []
        
        for data in analysis_data:
            # 인플루언서가 언급된 맥락 분석
            for insight in data['key_insights']:
                if influencer_name in insight:
                    mention_contexts.append({
                        'context': insight,
                        'sentiment': data['sentiment_score'],
                        'video_title': data['video_title'],
                        'channel': data['channel_name']
                    })
            
            sentiment_scores.append(data['sentiment_score'])
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return {
            "mention_contexts": mention_contexts[:10],  # 상위 10개만
            "avg_sentiment_when_mentioned": avg_sentiment,
            "sentiment_interpretation": self._get_sentiment_interpretation(avg_sentiment),
            "total_mentions": len(analysis_data)
        }
    
    def _get_top_entities(self, analyses: List[Dict], limit: int = 10) -> List[Dict]:
        """가장 많이 언급된 엔티티들을 반환합니다."""
        
        entity_counts = {}
        for analysis in analyses:
            for entity in analysis.get('mentioned_entities', []):
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"entity": entity, "count": count} for entity, count in sorted_entities[:limit]]
    
    def _get_sentiment_interpretation(self, sentiment_score: float) -> str:
        """감정 점수 해석"""
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
    
    def _generate_overall_insights(self, report_sections: Dict) -> Dict:
        """종합 인사이트 생성"""
        
        insights = {
            "key_themes": [],
            "sentiment_summary": {},
            "trending_topics": [],
            "recommendations": []
        }
        
        # 각 섹션에서 주요 테마 추출
        all_themes = []
        all_sentiments = []
        
        for section_type, section_data in report_sections.items():
            for item_name, item_data in section_data.items():
                if 'statistics' in item_data:
                    if 'avg_sentiment' in item_data['statistics']:
                        all_sentiments.append(item_data['statistics']['avg_sentiment'])
                
                # 각 섹션의 키 인사이트 수집
                if section_type == 'keywords' and 'keyword_trend' in item_data:
                    themes = item_data['keyword_trend'].get('key_themes', [])
                    all_themes.extend(themes)
                elif section_type == 'channels' and 'channel_trend' in item_data:
                    themes = item_data['channel_trend'].get('key_themes', [])
                    all_themes.extend(themes)
        
        # 가장 자주 언급되는 테마들
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        insights['key_themes'] = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 전체 감정 요약
        if all_sentiments:
            avg_sentiment = sum(all_sentiments) / len(all_sentiments)
            insights['sentiment_summary'] = {
                "overall_sentiment": avg_sentiment,
                "interpretation": self._get_sentiment_interpretation(avg_sentiment)
            }
        
        return insights
    
    def send_personalized_notification(self, report_data: Dict, notification_type: str = "email") -> bool:
        """개인화된 리포트 알림 발송"""
        
        try:
            if notification_type == "email":
                subject, html_body = self._format_personalized_email(report_data)
                return self.notification_service.send_email(subject, html_body)
            elif notification_type == "slack":
                message = self._format_personalized_slack_message(report_data)
                return self.notification_service.send_slack_message(message)
            else:
                self.logger.warning(f"지원하지 않는 알림 타입: {notification_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"개인화된 알림 발송 실패: {e}")
            return False
    
    def _format_personalized_email(self, report_data: Dict) -> tuple:
        """개인화된 리포트 이메일 포맷팅"""
        
        report_type = report_data.get('report_type', 'personalized')
        period = report_data.get('period', '최근')
        
        if 'keyword' in report_data:
            # 키워드 리포트
            keyword = report_data['keyword']
            subject = f"🔍 '{keyword}' 키워드 분석 리포트 ({period})"
        elif 'channel' in report_data:
            # 채널 리포트
            channel = report_data['channel']
            subject = f"📺 '{channel}' 채널 분석 리포트 ({period})"
        elif 'influencer' in report_data:
            # 인플루언서 리포트
            influencer = report_data['influencer']
            subject = f"👤 '{influencer}' 인플루언서 언급 분석 ({period})"
        else:
            # 다차원 리포트
            subject = f"📊 개인화된 투자 인사이트 리포트 ({period})"
        
        # 간단한 HTML 본문 (실제로는 더 상세하게 구현)
        html_body = f"""
        <html>
        <body>
        <h1>{subject}</h1>
        <p>개인화된 리포트가 생성되었습니다.</p>
        <p><strong>리포트 생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        return subject, html_body
    
    def _format_personalized_slack_message(self, report_data: Dict) -> str:
        """개인화된 리포트 슬랙 메시지 포맷팅"""
        
        if 'keyword' in report_data:
            keyword = report_data['keyword']
            stats = report_data.get('statistics', {})
            return f"🔍 *{keyword} 키워드 분석 완료*\n• 분석 수: {stats.get('total_analyses', 0)}개\n• 평균 감정: {stats.get('avg_sentiment', 0):.2f}"
        
        return "📊 개인화된 리포트가 생성되었습니다." 