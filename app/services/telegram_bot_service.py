import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models.database import SessionLocal
from app.services.personalized_report_service import PersonalizedReportService
from app.services.report_service import ReportService

load_dotenv('config.env')

class TelegramBotService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.personalized_service = PersonalizedReportService()
        self.report_service = ReportService()
        
        if not self.bot_token:
            self.logger.warning("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
            return
        
        # 봇 애플리케이션 초기화
        self.application = Application.builder().token(self.bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """명령어 핸들러들을 설정합니다."""
        
        # 기본 명령어들
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # 리포트 명령어들
        self.application.add_handler(CommandHandler("keyword", self.keyword_command))
        self.application.add_handler(CommandHandler("channel", self.channel_command))
        self.application.add_handler(CommandHandler("influencer", self.influencer_command))
        self.application.add_handler(CommandHandler("multi", self.multi_command))
        self.application.add_handler(CommandHandler("daily", self.daily_command))
        self.application.add_handler(CommandHandler("weekly", self.weekly_command))
        
        # 빠른 분석 명령어들
        self.application.add_handler(CommandHandler("trend", self.trend_command))
        self.application.add_handler(CommandHandler("hot", self.hot_keywords_command))
        
        # 텍스트 메시지 핸들러 (자연어 처리)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 명령어"""
        welcome_message = """
🤖 **투자 인사이트 분석 봇에 오신 것을 환영합니다!**

이 봇을 통해 실시간으로 투자 관련 인사이트를 받아보실 수 있습니다.

📋 **주요 기능:**
• `/keyword [키워드]` - 특정 키워드 분석
• `/channel [채널명]` - 특정 채널 분석  
• `/influencer [인물명]` - 특정 인물 언급 분석
• `/daily` - 오늘의 일일 리포트
• `/weekly` - 주간 리포트
• `/help` - 상세 사용법

시작하려면 `/help`를 입력하세요! 💡
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        help_message = """
📚 **사용법 가이드**

🔍 **키워드 분석**
`/keyword 주식` - '주식' 키워드 관련 최신 분석
`/keyword 부동산` - '부동산' 키워드 분석

📺 **채널 분석**  
`/channel 체슬리TV` - 체슬리TV 채널 최신 분석
`/channel Understanding` - Understanding 채널 분석
`/channel 홍춘욱` - 홍춘욱의 경제강의노트 분석

👤 **인플루언서 분석**
`/influencer 박세익` - 박세익 언급 분석
`/influencer 오건영` - 오건영 언급 분석
`/influencer 홍춘욱` - 홍춘욱 언급 분석
`/influencer 이선엽` - 이선엽 언급 분석
`/influencer 윤지호` - 윤지호 언급 분석

📊 **종합 리포트**
`/daily` - 오늘의 일일 요약 리포트
`/weekly` - 주간 종합 리포트

🔥 **빠른 분석**
`/hot` - 현재 핫한 키워드 TOP 10
`/trend` - 최근 3일 트렌드 분석

💬 **자연어 질문**
"오늘 주식 시장 어때?" 같은 자연어로도 질문 가능!

❓ 더 궁금한 것이 있으면 언제든 메시지를 보내주세요!
        """
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def keyword_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 분석 명령어"""
        if not context.args:
            await update.message.reply_text(
                "❌ 키워드를 입력해주세요!\n예: `/keyword 주식`", 
                parse_mode='Markdown'
            )
            return
        
        keyword = ' '.join(context.args)
        await update.message.reply_text(f"🔍 '{keyword}' 키워드 분석 중...")
        
        try:
            db = SessionLocal()
            report = self.personalized_service.generate_keyword_focused_report(
                db, keyword, days_back=3
            )
            
            if report.get('message'):
                await update.message.reply_text(f"ℹ️ {report['message']}")
            else:
                message = self._format_keyword_report(report)
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"키워드 분석 오류: {e}")
            await update.message.reply_text("❌ 분석 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 분석 명령어"""
        if not context.args:
            await update.message.reply_text(
                "❌ 채널명을 입력해주세요!\n예: `/channel 체슬리TV`", 
                parse_mode='Markdown'
            )
            return
        
        channel_name = ' '.join(context.args)
        await update.message.reply_text(f"📺 '{channel_name}' 채널 분석 중...")
        
        try:
            db = SessionLocal()
            report = self.personalized_service.generate_channel_focused_report(
                db, channel_name, days_back=7
            )
            
            if report.get('message'):
                await update.message.reply_text(f"ℹ️ {report['message']}")
            else:
                message = self._format_channel_report(report)
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"채널 분석 오류: {e}")
            await update.message.reply_text("❌ 분석 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def influencer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """인플루언서 분석 명령어"""
        if not context.args:
            await update.message.reply_text(
                "❌ 인물명을 입력해주세요!\n예: `/influencer 박세익`", 
                parse_mode='Markdown'
            )
            return
        
        influencer_name = ' '.join(context.args)
        await update.message.reply_text(f"👤 '{influencer_name}' 언급 분석 중...")
        
        try:
            db = SessionLocal()
            report = self.personalized_service.generate_influencer_focused_report(
                db, influencer_name, days_back=7
            )
            
            if report.get('message'):
                await update.message.reply_text(f"ℹ️ {report['message']}")
            else:
                message = self._format_influencer_report(report)
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"인플루언서 분석 오류: {e}")
            await update.message.reply_text("❌ 분석 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def multi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """다차원 분석 명령어"""
        if not context.args:
            await update.message.reply_text(
                "❌ 분석 대상을 입력해주세요!\n예: `/multi 주식 체슬리TV 박세익`\n형식: `/multi [키워드] [채널명] [인물명]`", 
                parse_mode='Markdown'
            )
            return
        
        args = context.args
        keywords = []
        channels = []
        influencers = []
        
        # 간단한 파싱 (실제로는 더 정교하게 구현 가능)
        known_channels = ["체슬리TV", "Understanding", "오종태의 투자병법", "김준송TV", "소수몽키", "Mkinvest", "한경", "홍춘욱"]
        known_influencers = ["박세익", "오건영", "김준송", "오종태", "성상현", "문홍철", "홍춘욱", "이선엽", "윤지호"]
        
        for arg in args:
            if arg in known_channels:
                channels.append(arg)
            elif arg in known_influencers:
                influencers.append(arg)
            else:
                keywords.append(arg)
        
        if not (keywords or channels or influencers):
            await update.message.reply_text("❌ 인식할 수 있는 키워드, 채널명, 인물명을 입력해주세요!")
            return
        
        await update.message.reply_text("📊 다차원 분석 중...")
        
        try:
            db = SessionLocal()
            report = self.personalized_service.generate_multi_dimension_report(
                db, 
                keywords=keywords if keywords else None,
                channels=channels if channels else None,
                influencers=influencers if influencers else None,
                days_back=7
            )
            
            if report:
                message = self._format_multi_report(report)
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ 다차원 리포트 생성에 실패했습니다.")
                
        except Exception as e:
            self.logger.error(f"다차원 분석 오류: {e}")
            await update.message.reply_text("❌ 분석 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일일 리포트 명령어"""
        await update.message.reply_text("📊 오늘의 일일 리포트 생성 중...")
        
        try:
            db = SessionLocal()
            report = self.report_service.generate_daily_report(db)
            
            if report.get('error'):
                await update.message.reply_text(f"❌ {report['error']}")
            else:
                message = self._format_daily_report(report)
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"일일 리포트 오류: {e}")
            await update.message.reply_text("❌ 리포트 생성 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def weekly_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """주간 리포트 명령어"""
        await update.message.reply_text("📈 주간 리포트 생성 중...")
        
        try:
            db = SessionLocal()
            report = self.report_service.generate_weekly_report(db)
            
            if report.get('error'):
                await update.message.reply_text(f"❌ {report['error']}")
            else:
                message = self._format_weekly_report(report)
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"주간 리포트 오류: {e}")
            await update.message.reply_text("❌ 리포트 생성 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def hot_keywords_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """핫 키워드 명령어"""
        await update.message.reply_text("🔥 현재 핫한 키워드 분석 중...")
        
        try:
            db = SessionLocal()
            # 최근 3일간 핫한 키워드 분석
            from app.models.database import Analysis, Video, Keyword
            from datetime import timedelta
            
            recent_date = datetime.now() - timedelta(days=3)
            
            # 최근 분석들에서 키워드별 언급 빈도 계산
            analyses = db.query(Analysis).join(Video).filter(
                Video.published_at >= recent_date
            ).all()
            
            keyword_counts = {}
            for analysis in analyses:
                keyword = db.query(Keyword).filter(Keyword.id == analysis.keyword_id).first()
                if keyword:
                    keyword_counts[keyword.keyword] = keyword_counts.get(keyword.keyword, 0) + 1
            
            # 상위 10개 키워드
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            message = "🔥 **현재 핫한 키워드 TOP 10**\n\n"
            for i, (keyword, count) in enumerate(top_keywords, 1):
                message += f"{i}. **{keyword}** ({count}회 분석)\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"핫 키워드 분석 오류: {e}")
            await update.message.reply_text("❌ 분석 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def trend_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """트렌드 분석 명령어"""
        await update.message.reply_text("📈 최근 트렌드 분석 중...")
        
        try:
            db = SessionLocal()
            from datetime import timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)
            
            analyses = self.report_service.get_period_analyses(db, start_date, end_date)
            
            if not analyses:
                await update.message.reply_text("ℹ️ 분석할 데이터가 없습니다.")
                return
            
            from app.services.analysis_service import AnalysisService
            analysis_service = AnalysisService()
            
            trend_analysis = analysis_service.generate_trend_analysis(
                analyses, [], "최근 3일"
            )
            
            message = self._format_trend_analysis(trend_analysis)
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"트렌드 분석 오류: {e}")
            await update.message.reply_text("❌ 분석 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """자연어 텍스트 처리"""
        user_text = update.message.text.lower()
        
        # 간단한 키워드 매칭으로 의도 파악
        if any(word in user_text for word in ['주식', '증시', '코스피', '나스닥']):
            await self.keyword_command(update, type('Args', (), {'args': ['주식']})())
        elif any(word in user_text for word in ['부동산', '집값', '아파트']):
            await self.keyword_command(update, type('Args', (), {'args': ['부동산']})())
        elif any(word in user_text for word in ['금리', '기준금리', '금융통화위원회']):
            await self.keyword_command(update, type('Args', (), {'args': ['금리']})())
        elif any(word in user_text for word in ['오늘', '일일', '데일리']):
            await self.daily_command(update, context)
        elif any(word in user_text for word in ['주간', '위클리', '이번주']):
            await self.weekly_command(update, context)
        elif any(word in user_text for word in ['핫', '인기', '트렌드']):
            await self.hot_keywords_command(update, context)
        else:
            # 일반적인 응답
            suggestions = [
                "💡 다음 명령어들을 사용해보세요:",
                "• `/keyword 주식` - 주식 관련 분석",
                "• `/daily` - 오늘의 리포트", 
                "• `/hot` - 핫한 키워드",
                "• `/help` - 전체 사용법"
            ]
            await update.message.reply_text('\n'.join(suggestions), parse_mode='Markdown')
    
    def _format_keyword_report(self, report: Dict) -> str:
        """키워드 리포트 포맷팅"""
        keyword = report['keyword']
        stats = report['statistics']
        
        message = f"🔍 **'{keyword}' 키워드 분석 리포트**\n\n"
        message += f"📊 **분석 통계**\n"
        message += f"• 분석 수: {stats['total_analyses']}개\n"
        message += f"• 채널 수: {stats['total_channels']}개\n"
        message += f"• 평균 감정: {stats['avg_sentiment']:.2f}\n\n"
        
        # 감정 분포
        sentiment_dist = stats['sentiment_distribution']
        message += f"😊 **감정 분포**\n"
        message += f"• 긍정: {sentiment_dist['positive']}개\n"
        message += f"• 중립: {sentiment_dist['neutral']}개\n"
        message += f"• 부정: {sentiment_dist['negative']}개\n\n"
        
        # 주요 비디오
        if 'top_videos' in report:
            message += f"🎯 **주요 분석 영상 (상위 3개)**\n"
            for i, video in enumerate(report['top_videos'][:3], 1):
                message += f"{i}. **{video['video_title'][:50]}...**\n"
                message += f"   📺 {video['channel_name']} | 중요도: {video['importance_score']:.2f}\n\n"
        
        return message
    
    def _format_channel_report(self, report: Dict) -> str:
        """채널 리포트 포맷팅"""
        channel = report['channel']
        stats = report['statistics']
        
        message = f"📺 **'{channel}' 채널 분석 리포트**\n\n"
        message += f"👥 구독자: {report.get('subscriber_count', 0):,}명\n"
        message += f"📹 분석 영상: {stats['total_videos']}개\n"
        message += f"📊 총 분석: {stats['total_analyses']}개\n"
        message += f"👀 평균 조회수: {stats['avg_views']:,.0f}회\n"
        message += f"😊 평균 감정: {stats['avg_sentiment']:.2f}\n\n"
        
        # 최근 영상
        if 'recent_videos' in report:
            message += f"🆕 **최신 영상 (상위 3개)**\n"
            for i, video in enumerate(report['recent_videos'][:3], 1):
                try:
                    if isinstance(video['published_at'], str):
                        pub_date = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
                    else:
                        pub_date = video['published_at']
                    date_str = pub_date.strftime('%m/%d')
                except:
                    date_str = "날짜미상"
                
                message += f"{i}. **{video['video_title'][:50]}...**\n"
                message += f"   📅 {date_str} | 중요도: {video['importance_score']:.2f}\n\n"
        
        return message
    
    def _format_influencer_report(self, report: Dict) -> str:
        """인플루언서 리포트 포맷팅"""
        influencer = report['influencer']
        stats = report['statistics']
        
        message = f"👤 **'{influencer}' 언급 분석 리포트**\n\n"
        message += f"💬 총 언급: {stats['total_mentions']}회\n"
        message += f"📺 언급 채널: {stats['channels_mentioned']}개\n"
        message += f"😊 평균 감정: {stats['avg_sentiment']:.2f}\n\n"
        
        if 'mention_analysis' in report:
            mention_analysis = report['mention_analysis']
            message += f"🎯 **언급 맥락 분석**\n"
            message += f"• 언급 시 평균 감정: {mention_analysis['avg_sentiment_when_mentioned']:.2f}\n"
            message += f"• 감정 해석: {mention_analysis['sentiment_interpretation']}\n\n"
            
            # 주요 언급 맥락
            if mention_analysis['mention_contexts']:
                message += f"💭 **주요 언급 맥락 (상위 2개)**\n"
                for i, context in enumerate(mention_analysis['mention_contexts'][:2], 1):
                    message += f"{i}. {context['context'][:100]}...\n"
                    message += f"   📺 {context['channel']} | 감정: {context['sentiment']:.2f}\n\n"
        
        return message
    
    def _format_daily_report(self, report: Dict) -> str:
        """일일 리포트 포맷팅"""
        daily_report = report.get('daily_report', {})
        stats = report.get('statistics', {})
        
        message = f"📊 **오늘의 투자 인사이트**\n\n"
        
        # 핵심 요약
        if 'executive_summary' in daily_report:
            message += f"💡 **핵심 요약**\n{daily_report['executive_summary']}\n\n"
        
        # 통계
        message += f"📈 **오늘의 통계**\n"
        message += f"• 분석 영상: {stats.get('total_videos_analyzed', 0)}개\n"
        message += f"• 분석 채널: {stats.get('total_channels', 0)}개\n"
        message += f"• 평균 감정: {stats.get('avg_sentiment', 0):.2f}\n\n"
        
        # 주요 하이라이트
        if 'market_highlights' in daily_report:
            message += f"🎯 **주요 하이라이트**\n"
            for highlight in daily_report['market_highlights'][:3]:
                message += f"• {highlight}\n"
            message += "\n"
        
        # 내일 전망
        if 'tomorrow_outlook' in daily_report:
            message += f"🔮 **내일 전망**\n{daily_report['tomorrow_outlook']}\n"
        
        return message
    
    def _format_weekly_report(self, report: Dict) -> str:
        """주간 리포트 포맷팅"""
        trend_analysis = report.get('trend_analysis', {})
        stats = report.get('weekly_statistics', {})
        
        message = f"📈 **주간 투자 인사이트**\n\n"
        
        # 주간 요약
        if 'summary' in trend_analysis:
            message += f"📝 **주간 요약**\n{trend_analysis['summary']}\n\n"
        
        # 핫 키워드
        if 'top_entities' in stats:
            message += f"🔥 **핫 키워드 TOP 5**\n"
            for i, entity in enumerate(stats['top_entities'][:5], 1):
                message += f"{i}. {entity['entity']} ({entity['count']}회)\n"
            message += "\n"
        
        # 주요 테마
        if 'key_themes' in trend_analysis:
            message += f"🎯 **주요 테마**\n"
            for theme in trend_analysis['key_themes'][:3]:
                message += f"• {theme}\n"
        
        return message
    
    def _format_trend_analysis(self, trend_analysis: Dict) -> str:
        """트렌드 분석 포맷팅"""
        message = f"📈 **최근 3일 트렌드 분석**\n\n"
        
        if 'market_sentiment' in trend_analysis:
            sentiment = trend_analysis['market_sentiment']
            if isinstance(sentiment, (int, float)):
                if sentiment > 0.1:
                    sentiment_emoji = "😊"
                    sentiment_text = "긍정적"
                elif sentiment < -0.1:
                    sentiment_emoji = "😰"
                    sentiment_text = "부정적"
                else:
                    sentiment_emoji = "😐"
                    sentiment_text = "중립적"
                
                message += f"💭 **시장 감정**: {sentiment_emoji} {sentiment_text} ({sentiment:.2f})\n\n"
        
        if 'key_themes' in trend_analysis:
            message += f"🎯 **주요 테마**\n"
            for theme in trend_analysis['key_themes'][:5]:
                message += f"• {theme}\n"
            message += "\n"
        
        if 'summary' in trend_analysis:
            message += f"📝 **트렌드 요약**\n{trend_analysis['summary']}"
        
        return message
    
    def _format_multi_report(self, report: Dict) -> str:
        """다차원 리포트 포맷팅"""
        message = f"📊 **다차원 투자 인사이트 분석**\n\n"
        message += f"📅 기간: {report['period']}\n\n"
        
        sections = report.get('sections', {})
        
        # 키워드 섹션
        if 'keywords' in sections:
            message += f"🔍 **키워드 분석**\n"
            for keyword, data in sections['keywords'].items():
                if not data.get('message'):
                    stats = data.get('statistics', {})
                    message += f"• **{keyword}**: {stats.get('total_analyses', 0)}개 분석, 감정 {stats.get('avg_sentiment', 0):.2f}\n"
            message += "\n"
        
        # 채널 섹션
        if 'channels' in sections:
            message += f"📺 **채널 분석**\n"
            for channel, data in sections['channels'].items():
                if not data.get('message'):
                    stats = data.get('statistics', {})
                    message += f"• **{channel}**: {stats.get('total_videos', 0)}개 영상, 감정 {stats.get('avg_sentiment', 0):.2f}\n"
            message += "\n"
        
        # 인플루언서 섹션
        if 'influencers' in sections:
            message += f"👤 **인플루언서 분석**\n"
            for influencer, data in sections['influencers'].items():
                if not data.get('message'):
                    stats = data.get('statistics', {})
                    message += f"• **{influencer}**: {stats.get('total_mentions', 0)}회 언급, 감정 {stats.get('avg_sentiment', 0):.2f}\n"
            message += "\n"
        
        # 종합 인사이트
        if 'overall_insights' in report:
            insights = report['overall_insights']
            
            if 'sentiment_summary' in insights:
                sentiment_info = insights['sentiment_summary']
                message += f"💭 **종합 감정**: {sentiment_info.get('interpretation', '중립적')} ({sentiment_info.get('overall_sentiment', 0):.2f})\n\n"
            
            if 'key_themes' in insights and insights['key_themes']:
                message += f"🎯 **주요 테마**\n"
                for theme, count in insights['key_themes'][:3]:
                    message += f"• {theme} ({count}회)\n"
        
        return message
    
    def run_bot(self):
        """봇을 실행합니다."""
        if not self.bot_token:
            self.logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
            return
        
        self.logger.info("텔레그램 봇 시작...")
        self.application.run_polling()
    
    async def send_notification(self, message: str, chat_id: str = None) -> bool:
        """특정 사용자에게 알림을 발송합니다."""
        if not self.bot_token:
            return False
        
        try:
            bot = Bot(token=self.bot_token)
            target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
            
            if not target_chat_id:
                self.logger.warning("TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
                return False
            
            await bot.send_message(chat_id=target_chat_id, text=message, parse_mode='Markdown')
            return True
            
        except Exception as e:
            self.logger.error(f"텔레그램 알림 발송 실패: {e}")
            return False

# 봇 인스턴스
telegram_bot = TelegramBotService()

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 봇 실행
    telegram_bot.run_bot() 