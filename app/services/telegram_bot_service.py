import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import re

from app.models.database import SessionLocal
from app.services.personalized_report_service import PersonalizedReportService
from app.services.report_service import ReportService

load_dotenv('config.env')

class TelegramBotService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.authorized_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.personalized_service = PersonalizedReportService()
        self.report_service = ReportService()
        
        if not self.bot_token:
            self.logger.warning("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
            return
        
        # YouTube URL 패턴 정의
        self.youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)',
            r'https?://(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
        ]
        
        # 봇 애플리케이션 초기화
        self.application = Application.builder().token(self.bot_token).build()
        self._setup_handlers()
    
    def extract_video_id(self, url: str) -> str:
        """YouTube URL에서 영상 ID 추출"""
        # @ 기호나 기타 문자가 앞에 붙은 경우 제거
        clean_url = url.strip()
        
        # @ 기호로 시작하는 경우 제거
        if clean_url.startswith('@'):
            clean_url = clean_url[1:]
        
        # 공백이나 기타 문자 제거
        clean_url = clean_url.strip()
        
        for pattern in self.youtube_patterns:
            match = re.search(pattern, clean_url)
            if match:
                # URL 파라미터에서 video ID만 추출 (? 이후 제거)
                video_id = match.group(1)
                if '&' in video_id:
                    video_id = video_id.split('&')[0]
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
                return video_id
        return None
    
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
        
        # 🔍 새로운 키워드 검색 명령어
        self.application.add_handler(CommandHandler("search", self.search_command))
        
        # 🎛️ 새로운 관리 명령어들
        self.application.add_handler(CommandHandler("list_keywords", self.list_keywords_command))
        self.application.add_handler(CommandHandler("list_channels", self.list_channels_command))
        self.application.add_handler(CommandHandler("add_keyword", self.add_keyword_command))
        self.application.add_handler(CommandHandler("remove_keyword", self.remove_keyword_command))
        self.application.add_handler(CommandHandler("add_channel", self.add_channel_command))
        self.application.add_handler(CommandHandler("remove_channel", self.remove_channel_command))
        self.application.add_handler(CommandHandler("confirm_remove_channel", self.confirm_remove_channel_command))
        
        # 텍스트 메시지 핸들러 (자연어 처리 + YouTube URL)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def send_startup_notification(self):
        """봇 시작 알림 메시지 전송"""
        if not self.authorized_chat_id:
            return
            
        startup_message = f"""
🤖 **투자 분석 봇이 시작되었습니다!**

🕐 **시작 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 **분석 명령어:**
• `/search [키워드]` - 🔥 실시간 YouTube 검색
• `/keyword [키워드]` - 키워드 분석
• `/channel [채널명]` - 채널 분석
• `/influencer [인물명]` - 인물 언급 분석
• `/daily` - 일일 리포트
• `/weekly` - 주간 리포트
• `/hot` - 핫 키워드 TOP 10
• `/trend` - 최근 트렌드 분석
• `/multi` - 다차원 분석

🎛️ **관리 명령어:**
• `/list_keywords` - 등록된 키워드 목록
• `/list_channels` - 등록된 채널 목록
• `/add_keyword [키워드] [카테고리]` - 키워드 추가
• `/add_channel [채널명/URL]` - 채널 추가
• `/remove_keyword [ID]` - 키워드 제거
• `/remove_channel [ID]` - 채널 제거

🎬 **기타:**
• YouTube URL 전송 - 자동 영상 요약

💡 **새로운 기능**: 키워드/채널 관리 기능이 추가되었습니다!

봇이 정상적으로 작동 중입니다. 🚀
        """
        
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.authorized_chat_id,
                text=startup_message,
                parse_mode='Markdown'
            )
            self.logger.info("✅ 봇 시작 알림 메시지 전송 완료")
        except Exception as e:
            self.logger.error(f"❌ 봇 시작 알림 전송 실패: {e}")
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """실시간 키워드 검색 명령어"""
        if not context.args:
            await update.message.reply_text(
                "🔍 **키워드 검색 사용법**\n\n"
                "사용법: `/search [키워드]`\n\n"
                "예시:\n"
                "• `/search 삼성전자` - 삼성전자 관련 최신 영상 검색\n"
                "• `/search 부동산` - 부동산 관련 영상 검색\n"
                "• `/search 금리 인상` - 금리 인상 관련 영상 검색\n\n"
                "💡 YouTube에서 최신 영상을 검색하고 AI 요약을 제공합니다!",
                parse_mode='Markdown'
            )
            return
        
        keyword = ' '.join(context.args)
        progress_msg = await update.message.reply_text(
            f"🔍 **'{keyword}' 검색 중...**\n\n"
            "📹 YouTube에서 관련 영상을 검색하고 있습니다...\n"
            "⏳ 잠시만 기다려주세요."
        )
        
        try:
            # YouTube에서 키워드 검색
            search_results = await self._search_youtube_videos(keyword)
            
            if not search_results:
                await progress_msg.edit_text(
                    f"🔍 **'{keyword}' 검색 결과**\n\n"
                    f"❌ 최근 7일 내 '{keyword}' 관련 영상을 찾을 수 없습니다.\n\n"
                    "💡 **제안:**\n"
                    "• 다른 키워드로 검색해보세요\n"
                    "• 더 일반적인 용어를 사용해보세요"
                )
                return
            
            # 검색 결과 포맷팅
            results_message = self._format_search_results(keyword, search_results)
            await progress_msg.edit_text(results_message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"키워드 검색 오류: {e}")
            await progress_msg.edit_text(
                "❌ **검색 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {str(e)}"
            )
    
    async def _search_youtube_videos(self, keyword: str, max_results: int = 5) -> List[Dict]:
        """YouTube에서 키워드 검색"""
        try:
            from app.services.youtube_service import YouTubeService
            youtube_service = YouTubeService()
            
            # 최근 7일 내 영상 검색
            recent_date = datetime.now() - timedelta(days=7)
            results = youtube_service.search_videos_by_keyword(
                keyword=keyword,
                max_results=max_results,
                published_after=recent_date
            )
            
            return results
        except Exception as e:
            self.logger.error(f"YouTube 검색 실패: {e}")
            return []
    
    def _format_search_results(self, keyword: str, results: List[Dict]) -> str:
        """검색 결과 포맷팅"""
        def escape_markdown(text: str) -> str:
            """마크다운 특수 문자 이스케이프"""
            if not text:
                return ""
            special_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        message = f"🔍 **'{escape_markdown(keyword)}' 검색 결과 ({len(results)}개)**\n\n"
        message += f"📅 **검색 범위:** 최근 7일\n"
        message += f"📊 **찾은 영상:** {len(results)}개\n\n"
        
        for i, video in enumerate(results, 1):
            published_date = video.get('published_at', datetime.now())
            if isinstance(published_date, str):
                try:
                    published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                except:
                    published_date = datetime.now()
            
            title = escape_markdown(video['title'][:60])
            channel_name = escape_markdown(video['channel_name'])
            
            message += f"**{i}\\. {title}\\.\\.\\.**\n"
            message += f"👤 {channel_name}\n"
            message += f"👀 {video.get('view_count', 0):,}회 | 📅 {published_date.strftime('%m-%d')}\n"
            message += f"🔗 [링크](https://www.youtube.com/watch?v={video['video_id']})\n\n"
        
        message += "💡 **YouTube URL을 보내주시면 AI가 자동으로 요약해드립니다\\!**"
        
        return message
    
    async def process_youtube_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str, url: str):
        """YouTube URL 처리 및 요약"""
        
        progress_msg = await update.message.reply_text(
            "🎬 **YouTube 영상 분석 중...**\n\n"
            f"📹 영상 ID: `{video_id}`\n"
            "⏳ 영상 정보를 가져오는 중...",
            parse_mode='Markdown'
        )
        
        try:
            # 영상 정보 가져오기
            video_data = await self._get_youtube_video_data(video_id)
            
            if not video_data:
                await progress_msg.edit_text(
                    "❌ **영상 정보를 가져올 수 없습니다.**\n\n"
                    "가능한 원인:\n"
                    "• 비공개 영상\n"
                    "• 삭제된 영상\n"
                    "• 지역 제한\n"
                    "• 잘못된 URL"
                )
                return
            
            await progress_msg.edit_text(
                "🎬 **YouTube 영상 분석 중...**\n\n"
                f"📹 **{video_data['title'][:50]}...**\n"
                f"👤 채널: {video_data['channel_name']}\n"
                f"👀 조회수: {video_data['view_count']:,}회\n\n"
                "📝 자막을 가져오는 중...",
                parse_mode='Markdown'
            )
            
            # 자막 가져오기
            transcript_text = video_data.get('transcript', '')
            
            if not transcript_text:
                # 자막 정보에 따라 다른 메시지 제공
                if video_data.get('is_auto_generated') is not None:
                    # 자막 시도했지만 텍스트가 없는 경우
                    subtitle_info = (
                        f"🔍 자막 상태: {'자동생성 자막' if video_data.get('is_auto_generated') else '수동 자막'} "
                        f"({video_data.get('transcript_language', 'ko')})\n"
                        "⚠️ 자막 텍스트를 가져올 수 없습니다."
                    )
                else:
                    # 자막 자체가 없는 경우
                    subtitle_info = "자막이 없거나 비활성화된 영상입니다."
                
                await progress_msg.edit_text(
                    f"⚠️ **자막을 찾을 수 없습니다**\n\n"
                    f"📹 **{video_data['title']}**\n"
                    f"👤 채널: {video_data['channel_name']}\n"
                    f"👀 조회수: {video_data['view_count']:,}회\n"
                    f"🔗 {url}\n\n"
                    f"{subtitle_info}",
                    parse_mode='Markdown'
                )
                return
            
            await progress_msg.edit_text(
                "🎬 **YouTube 영상 분석 중...**\n\n"
                f"📹 **{video_data['title'][:50]}...**\n"
                f"👤 채널: {video_data['channel_name']}\n\n"
                "🤖 AI 분석 진행 중... (30초~1분 소요)",
                parse_mode='Markdown'
            )
            
            # AI 분석 실행
            analysis_result = await self._analyze_youtube_content(video_data)
            
            # 결과 전송
            await self._send_youtube_analysis_result(update, video_data, analysis_result, url, progress_msg)
            
        except Exception as e:
            self.logger.error(f"YouTube URL 처리 중 오류: {e}")
            await progress_msg.edit_text(
                f"❌ **처리 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {str(e)}"
            )
    
    async def _get_youtube_video_data(self, video_id: str) -> Optional[Dict]:
        """YouTube 영상 데이터 가져오기"""
        try:
            from app.services.youtube_service import YouTubeService
            youtube_service = YouTubeService()
            
            # 영상 정보 가져오기
            video_info = youtube_service.get_video_info(video_id)
            if not video_info:
                return None
            
            # 자막 가져오기
            transcript = youtube_service.get_video_transcript(video_id)
            transcript_text = ''
            transcript_language = 'ko'
            is_auto_generated = False
            
            if transcript:
                transcript_text = transcript.get('transcript_text', '')
                transcript_language = transcript.get('language', 'ko') 
                is_auto_generated = transcript.get('is_auto_generated', False)
                
                # 자막 타입 로깅
                if transcript_text:
                    if is_auto_generated:
                        self.logger.info(f"✅ 자동생성 자막 발견: {transcript_language}")
                    else:
                        self.logger.info(f"✅ 수동 자막 발견: {transcript_language}")
                else:
                    self.logger.warning(f"⚠️ 자막 텍스트가 비어있음")
            else:
                self.logger.warning(f"⚠️ 자막을 찾을 수 없음: video_id={video_id}")
            
            return {
                'video_id': video_id,
                'title': video_info['title'],
                'channel_name': video_info['channel_name'],
                'view_count': video_info['view_count'],
                'like_count': video_info.get('like_count', 0),
                'published_at': video_info['published_at'],
                'transcript': transcript_text,
                'transcript_language': transcript_language,
                'is_auto_generated': is_auto_generated,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
            
        except Exception as e:
            self.logger.error(f"YouTube 영상 데이터 가져오기 실패: {e}")
            return None
    
    async def _analyze_youtube_content(self, video_data: Dict) -> Dict:
        """YouTube 콘텐츠 AI 분석"""
        try:
            from app.services.analysis_service import AnalysisService
            analysis_service = AnalysisService()
            
            analysis_result = analysis_service.analyze_transcript(
                transcript_text=video_data['transcript'],
                video_title=video_data['title'],
                channel_name=video_data['channel_name']
            )
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"YouTube 콘텐츠 분석 실패: {e}")
            return {
                'summary': f"'{video_data['title']}' - 분석 중 오류가 발생했습니다.",
                'key_insights': ['분석 실패'],
                'sentiment': 'neutral',
                'importance': 0.5
            }
    
    async def _send_youtube_analysis_result(self, update: Update, video_data: dict, analysis: dict, url: str, progress_msg):
        """YouTube 분석 결과 전송"""
        try:
            # 기본 영상 정보
            basic_info = (
                f"🎬 **YouTube 영상 AI 요약 완료**\n\n"
                f"📹 **제목:** {video_data['title']}\n"
                f"👤 **채널:** {video_data['channel_name']}\n"
                f"👀 **조회수:** {video_data['view_count']:,}회\n"
                f"👍 **좋아요:** {video_data.get('like_count', 0):,}개\n"
                f"🔗 **링크:** {url}\n"
            )
            
            # 요약 정보
            summary = analysis.get('summary', '요약 정보가 없습니다.')
            sentiment_score = analysis.get('sentiment_score', 0)
            
            # 감정 점수를 이모지로 변환
            if sentiment_score > 0.3:
                sentiment_emoji = "📈 긍정적"
            elif sentiment_score < -0.3:
                sentiment_emoji = "📉 부정적"
            else:
                sentiment_emoji = "⚖️ 중립적"
            
            summary_text = (
                f"{basic_info}\n"
                f"📋 **AI 요약:**\n{summary}\n\n"
                f"📊 **시장 전망:** {sentiment_emoji} ({sentiment_score:.2f})\n"
            )
            
            # 메인 요약 전송
            await progress_msg.edit_text(
                summary_text,
                parse_mode='Markdown'
            )
            
            # 주요 인사이트
            key_insights = analysis.get('key_insights', [])
            if key_insights:
                insights_text = "💡 **주요 인사이트:**\n\n"
                for i, insight in enumerate(key_insights[:5], 1):
                    insights_text += f"{i}. {insight}\n"
                
                await update.message.reply_text(insights_text, parse_mode='Markdown')
            
            # 투자 테마
            topics = analysis.get('topics', [])
            if topics:
                topics_text = f"🏷️ **투자 테마:** {', '.join(topics[:5])}"
                await update.message.reply_text(topics_text, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"YouTube 분석 결과 전송 실패: {e}")
            await update.message.reply_text(f"❌ 결과 전송 중 오류: {str(e)}")
    
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

🔍 **실시간 검색**
`/search 삼성전자` - YouTube에서 실시간 검색
`/search 부동산` - 최신 부동산 관련 영상 검색
`/search 금리 인상` - 금리 관련 최신 영상 검색

🎬 **YouTube URL 요약**
YouTube URL을 그냥 보내주세요! AI가 자동으로 요약해드립니다.
지원 형식: youtube.com, youtu.be, shorts 등

📊 **분석 명령어**
`/keyword 주식` - '주식' 키워드 관련 최신 분석
`/channel 체슬리TV` - 체슬리TV 채널 최신 분석
`/influencer 박세익` - 박세익 언급 분석
`/daily` - 오늘의 일일 요약 리포트
`/weekly` - 주간 종합 리포트
`/hot` - 현재 핫한 키워드 TOP 10
`/trend` - 최근 3일 트렌드 분석
`/multi` - 다차원 분석

🎛️ **관리 명령어**
`/list_keywords` - 등록된 키워드 목록 보기
`/list_channels` - 등록된 채널 목록 보기
`/add_keyword [키워드] [카테고리]` - 키워드 추가
`/add_channel [채널명/URL]` - 채널 추가
`/remove_keyword [ID]` - 키워드 제거 (ID는 목록에서 확인)
`/remove_channel [ID]` - 채널 제거 (ID는 목록에서 확인)

💬 **자연어 질문**
"오늘 주식 시장 어때?" 같은 자연어로도 질문 가능!

💡 **관리 예시:**
• `/add_keyword 삼성전자 주식` - 삼성전자 키워드를 주식 카테고리로 추가
• `/add_channel 체슬리TV` - 체슬리TV 채널 추가
• `/add_channel @chesleytv` - 핸들로 채널 추가
• `/add_channel https://www.youtube.com/@chesleytv` - URL로 채널 추가

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
            elif report.get('message'):
                # 데이터가 없는 경우
                await update.message.reply_text(
                    f"ℹ️ {report['message']}\n\n"
                    "💡 새로운 비디오가 분석되면 리포트를 생성할 수 있습니다."
                )
            else:
                message = self._format_daily_report(report)
                # 메시지가 너무 길면 나누어서 전송
                if len(message) > 4000:
                    parts = self._split_message(message, 4000)
                    for part in parts:
                        await update.message.reply_text(part, parse_mode='Markdown')
                else:
                    await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"일일 리포트 오류: {e}")
            await update.message.reply_text(
                "❌ 리포트 생성 중 오류가 발생했습니다.\n"
                "잠시 후 다시 시도해주세요."
            )
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
            elif report.get('message'):
                # 데이터가 없는 경우
                await update.message.reply_text(
                    f"ℹ️ {report['message']}\n\n"
                    "💡 지난 7일간 분석된 비디오가 있어야 주간 리포트를 생성할 수 있습니다."
                )
            else:
                message = self._format_weekly_report(report)
                # 메시지가 너무 길면 나누어서 전송
                if len(message) > 4000:
                    parts = self._split_message(message, 4000)
                    for part in parts:
                        await update.message.reply_text(part, parse_mode='Markdown')
                else:
                    await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"주간 리포트 오류: {e}")
            await update.message.reply_text(
                "❌ 리포트 생성 중 오류가 발생했습니다.\n"
                "잠시 후 다시 시도해주세요."
            )
        finally:
            db.close()
    
    async def hot_keywords_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """핫 키워드 명령어"""
        await update.message.reply_text("🔥 현재 핫한 키워드 분석 중...")
        
        try:
            db = SessionLocal()
            # 최근 3일간 핫한 키워드 분석
            from app.models.database import Analysis, Video, Keyword
            
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
        """자연어 텍스트 처리 + YouTube URL 처리"""
        user_text = update.message.text.strip()
        
        self.logger.info(f"텍스트 처리: '{user_text}'")
        
        try:
            # 🎬 YouTube URL 감지 및 처리
            video_id = self.extract_video_id(user_text)
            if video_id:
                await self.process_youtube_url(update, context, video_id, user_text)
                return
            
            # 자연어 처리
            user_text_lower = user_text.lower()
            
            # 간단한 키워드 매칭으로 의도 파악
            if any(word in user_text_lower for word in ['주식', '증시', '코스피', '나스닥', '주식시장']):
                # context 객체 생성하여 전달
                mock_context = type('Context', (), {'args': ['주식']})()
                await self.keyword_command(update, mock_context)
                return
                
            elif any(word in user_text_lower for word in ['부동산', '집값', '아파트', '부동산시장']):
                mock_context = type('Context', (), {'args': ['부동산']})()
                await self.keyword_command(update, mock_context)
                return
                
            elif any(word in user_text_lower for word in ['금리', '기준금리', '금융통화위원회', '금리인상', '금리인하']):
                mock_context = type('Context', (), {'args': ['금리']})()
                await self.keyword_command(update, mock_context)
                return
                
            elif any(word in user_text_lower for word in ['달러', '환율', '원달러', '달러강세', '달러약세']):
                mock_context = type('Context', (), {'args': ['달러']})()
                await self.keyword_command(update, mock_context)
                return
                
            elif any(word in user_text_lower for word in ['오늘', '일일', '데일리', '투자', '시장']):
                await self.daily_command(update, context)
                return
                
            elif any(word in user_text_lower for word in ['주간', '위클리', '이번주', '일주일']):
                await self.weekly_command(update, context)
                return
                
            elif any(word in user_text_lower for word in ['핫', '인기', '트렌드', '화제']):
                await self.hot_keywords_command(update, context)
                return
                
            elif any(word in user_text_lower for word in ['트렌드', '최근', '추세']):
                await self.trend_command(update, context)
                return
                
            # 채널 관련 질문
            elif any(word in user_text_lower for word in ['체슬리', '체슬리tv']):
                mock_context = type('Context', (), {'args': ['체슬리TV']})()
                await self.channel_command(update, mock_context)
                return
                
            # 인물 관련 질문
            elif any(word in user_text_lower for word in ['박세익', '오건영', '홍춘욱', '김준송']):
                for name in ['박세익', '오건영', '홍춘욱', '김준송']:
                    if name in user_text_lower:
                        mock_context = type('Context', (), {'args': [name]})()
                        await self.influencer_command(update, mock_context)
                        return
            
            # 기본 응답
            suggestions = [
                "💡 **자연어로 이렇게 질문해보세요:**",
                "",
                "🔍 **키워드 분석:**",
                "• '오늘 주식 시장 어때?'",
                "• '부동산 소식 알려줘'", 
                "• '금리 관련 분석해줘'",
                "",
                "📊 **리포트 요청:**",
                "• '오늘 리포트 보여줘'",
                "• '핫한 키워드 알려줘'",
                "• '최근 트렌드는?'",
                "",
                "📺 **채널 분석:**",
                "• '체슬리TV 최근 영상은?'",
                "",
                "👤 **인물 분석:**",
                "• '박세익 최근 언급은?'",
                "",
                "❓ **명령어:** `/help`"
            ]
            await update.message.reply_text('\n'.join(suggestions), parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"자연어 처리 오류: {e}")
            await update.message.reply_text("❌ 처리 중 오류가 발생했습니다. `/help`를 참고해주세요.")
    
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
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        daily_report = report.get('daily_report', {})
        trend_analysis = report.get('trend_analysis', {})
        stats = report.get('statistics', {})
        
        message = f"📊 **일일 투자 인사이트** ({date})\n\n"
        
        # 핵심 요약
        if daily_report.get('executive_summary'):
            message += f"💡 **핵심 요약**\n{daily_report['executive_summary']}\n\n"
        elif trend_analysis.get('summary'):
            message += f"💡 **핵심 요약**\n{trend_analysis['summary']}\n\n"
        
        # 통계
        message += f"📈 **오늘의 통계**\n"
        message += f"• 분석 영상: {stats.get('total_videos_analyzed', 0)}개\n"
        message += f"• 분석 채널: {stats.get('total_channels', 0)}개\n"
        message += f"• 평균 감정: {stats.get('avg_sentiment', 0):.2f}\n\n"
        
        # 시장 감정
        sentiment = trend_analysis.get('market_sentiment', 'neutral')
        if isinstance(sentiment, str):
            sentiment_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➖"}.get(sentiment, "➖")
            message += f"💭 **시장 감정**: {sentiment_emoji} {sentiment.title()}\n\n"
        
        # 주요 하이라이트 또는 테마
        if daily_report.get('market_highlights'):
            message += f"🎯 **주요 하이라이트**\n"
            for highlight in daily_report['market_highlights'][:3]:
                message += f"• {highlight}\n"
            message += "\n"
        elif trend_analysis.get('key_themes'):
            message += f"🎯 **주요 테마**\n"
            for theme in trend_analysis['key_themes'][:3]:
                message += f"• {theme}\n"
            message += "\n"
        
        # 내일 전망
        if daily_report.get('tomorrow_outlook'):
            message += f"🔮 **내일 전망**\n{daily_report['tomorrow_outlook']}\n\n"
        
        # 실행 가능한 인사이트
        if daily_report.get('action_items'):
            message += f"📋 **실행 포인트**\n"
            for action in daily_report['action_items'][:2]:
                message += f"• {action}\n"
        
        return message
    
    def _format_weekly_report(self, report: Dict) -> str:
        """주간 리포트 포맷팅"""
        period = report.get('period', '최근 7일')
        trend_analysis = report.get('trend_analysis', {})
        stats = report.get('weekly_statistics', {})
        
        message = f"📈 **주간 투자 인사이트**\n📅 {period}\n\n"
        
        # 주간 요약
        if trend_analysis.get('summary'):
            message += f"📝 **주간 요약**\n{trend_analysis['summary']}\n\n"
        
        # 주간 통계
        message += f"📊 **주간 통계**\n"
        message += f"• 분석 영상: {stats.get('total_videos', 0)}개\n"
        message += f"• 분석 채널: {stats.get('total_channels', 0)}개\n"
        message += f"• 평균 감정: {stats.get('avg_sentiment', 0):.2f}\n\n"
        
        # 감정 분포
        if stats.get('sentiment_distribution'):
            sentiment_dist = stats['sentiment_distribution']
            message += f"💭 **감정 분포**\n"
            message += f"• 긍정적: {sentiment_dist.get('positive', 0)}개\n"
            message += f"• 중립적: {sentiment_dist.get('neutral', 0)}개\n"
            message += f"• 부정적: {sentiment_dist.get('negative', 0)}개\n\n"
        
        # 핫 엔티티
        if stats.get('top_entities'):
            message += f"🔥 **핫 키워드 TOP 5**\n"
            for i, entity in enumerate(stats['top_entities'][:5], 1):
                message += f"{i}. {entity['entity']} ({entity['count']}회)\n"
            message += "\n"
        
        # 주요 테마
        if trend_analysis.get('key_themes'):
            message += f"🎯 **주요 테마**\n"
            for theme in trend_analysis['key_themes'][:4]:
                message += f"• {theme}\n"
            message += "\n"
        
        # 시장 전망
        if trend_analysis.get('market_sentiment'):
            sentiment = trend_analysis['market_sentiment']
            if isinstance(sentiment, str):
                sentiment_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➖"}.get(sentiment, "➖")
                message += f"🔮 **시장 전망**: {sentiment_emoji} {sentiment.title()}\n"
        
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
    
    def _split_message(self, message: str, max_length: int = 4000) -> List[str]:
        """긴 메시지를 여러 부분으로 나눕니다."""
        if len(message) <= max_length:
            return [message]
        
        parts = []
        lines = message.split('\n')
        current_part = ""
        
        for line in lines:
            # 현재 줄을 추가했을 때 길이가 초과하는지 확인
            if len(current_part + line + '\n') > max_length:
                if current_part:  # 현재 파트가 비어있지 않으면 저장
                    parts.append(current_part.rstrip())
                    current_part = ""
                
                # 한 줄이 너무 긴 경우 강제로 자름
                if len(line) > max_length:
                    while line:
                        parts.append(line[:max_length])
                        line = line[max_length:]
                else:
                    current_part = line + '\n'
            else:
                current_part += line + '\n'
        
        # 마지막 파트 추가
        if current_part:
            parts.append(current_part.rstrip())
        
        return parts
    
    def run_bot(self):
        """봇을 실행합니다."""
        if not self.bot_token:
            self.logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
            return
        
        self.logger.info("텔레그램 봇 시작...")
        
        # 봇 시작 알림 전송
        async def startup_callback():
            await self.send_startup_notification()
        
        # 시작 알림을 백그라운드에서 실행
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 봇 시작과 함께 알림 전송
        async def run_with_notification():
            # 시작 알림 전송
            await self.send_startup_notification()
            # 봇 실행
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            await asyncio.Event().wait()  # 무한 대기
        
        try:
            loop.run_until_complete(run_with_notification())
        except KeyboardInterrupt:
            self.logger.info("🛑 봇이 중지되었습니다.")
        finally:
            loop.close()
    
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

    async def list_keywords_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """등록된 키워드 목록 보기"""
        try:
            db = SessionLocal()
            from app.models.database import Keyword
            
            keywords = db.query(Keyword).order_by(Keyword.category, Keyword.keyword).all()
            
            if not keywords:
                await update.message.reply_text(
                    "📝 **등록된 키워드가 없습니다.**\n\n"
                    "키워드를 추가하려면:\n"
                    "`/add_keyword [키워드] [카테고리]`\n\n"
                    "예시: `/add_keyword 삼성전자 주식`",
                    parse_mode='Markdown'
                )
                return
            
            # 카테고리별로 그룹화
            categories = {}
            for kw in keywords:
                if kw.category not in categories:
                    categories[kw.category] = []
                categories[kw.category].append(kw)
            
            message = f"📝 **등록된 키워드 목록 ({len(keywords)}개)**\n\n"
            
            for category, kw_list in categories.items():
                message += f"📂 **{category}** ({len(kw_list)}개)\n"
                for kw in kw_list:
                    message += f"   • {kw.keyword} (ID: {kw.id})\n"
                message += "\n"
            
            message += "🔧 **관리 명령어:**\n"
            message += "• `/add_keyword [키워드] [카테고리]` - 키워드 추가\n"
            message += "• `/remove_keyword [키워드ID]` - 키워드 제거\n"
            message += "• `/search [키워드]` - 키워드로 YouTube 검색"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"키워드 목록 조회 오류: {e}")
            await update.message.reply_text("❌ 키워드 목록을 불러오는 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def list_channels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """등록된 채널 목록 보기"""
        try:
            db = SessionLocal()
            from app.models.database import Channel
            
            channels = db.query(Channel).order_by(Channel.channel_name).all()
            
            if not channels:
                await update.message.reply_text(
                    "📺 **등록된 채널이 없습니다.**\n\n"
                    "채널을 추가하려면:\n"
                    "`/add_channel [채널명 또는 URL]`\n\n"
                    "예시:\n"
                    "• `/add_channel 체슬리TV`\n"
                    "• `/add_channel @chesleytv`\n"
                    "• `/add_channel UCxxxxxxxxxxxx`",
                    parse_mode='Markdown'
                )
                return
            
            message = f"📺 **등록된 채널 목록 ({len(channels)}개)**\n\n"
            
            for i, ch in enumerate(channels, 1):
                message += f"**{i}. {ch.channel_name}**\n"
                message += f"   🆔 ID: {ch.channel_id}\n"
                if ch.subscriber_count:
                    message += f"   👥 구독자: {ch.subscriber_count:,}명\n"
                if ch.video_count:
                    message += f"   📹 영상: {ch.video_count:,}개\n"
                if ch.channel_url:
                    message += f"   🔗 [바로가기]({ch.channel_url})\n"
                message += "\n"
            
            message += "🔧 **관리 명령어:**\n"
            message += "• `/add_channel [채널명/URL]` - 채널 추가\n"
            message += "• `/remove_channel [채널ID]` - 채널 제거\n"
            message += "• `/channel [채널명]` - 채널 분석"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"채널 목록 조회 오류: {e}")
            await update.message.reply_text("❌ 채널 목록을 불러오는 중 오류가 발생했습니다.")
        finally:
            db.close()
    
    async def add_keyword_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 추가"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ **사용법이 올바르지 않습니다.**\n\n"
                "**사용법:** `/add_keyword [키워드] [카테고리]`\n\n"
                "**예시:**\n"
                "• `/add_keyword 삼성전자 주식`\n"
                "• `/add_keyword 금리인상 경제`\n"
                "• `/add_keyword 아파트 부동산`\n"
                "• `/add_keyword 비트코인 암호화폐`",
                parse_mode='Markdown'
            )
            return
        
        keyword = context.args[0]
        category = ' '.join(context.args[1:])
        
        try:
            db = SessionLocal()
            from app.models.database import Keyword
            
            # 중복 확인
            existing = db.query(Keyword).filter(Keyword.keyword == keyword).first()
            if existing:
                await update.message.reply_text(
                    f"⚠️ **'{keyword}'는 이미 등록된 키워드입니다.**\n\n"
                    f"카테고리: {existing.category}\n"
                    f"등록일: {existing.created_at.strftime('%Y-%m-%d')}"
                )
                return
            
            # 새 키워드 추가
            new_keyword = Keyword(
                keyword=keyword,
                category=category
            )
            
            db.add(new_keyword)
            db.commit()
            db.refresh(new_keyword)
            
            await update.message.reply_text(
                f"✅ **키워드 추가 완료!**\n\n"
                f"🔍 **키워드:** {keyword}\n"
                f"📂 **카테고리:** {category}\n"
                f"🆔 **ID:** {new_keyword.id}\n\n"
                f"이제 `/search {keyword}` 명령어로 검색하거나\n"
                f"`/keyword {keyword}` 명령어로 분석할 수 있습니다!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"키워드 추가 오류: {e}")
            await update.message.reply_text(f"❌ 키워드 추가 중 오류가 발생했습니다: {str(e)}")
        finally:
            db.close()
    
    async def remove_keyword_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 제거"""
        if not context.args:
            await update.message.reply_text(
                "❌ **사용법이 올바르지 않습니다.**\n\n"
                "**사용법:** `/remove_keyword [키워드ID]`\n\n"
                "키워드 ID는 `/list_keywords` 명령어로 확인할 수 있습니다.\n\n"
                "**예시:** `/remove_keyword 5`",
                parse_mode='Markdown'
            )
            return
        
        try:
            keyword_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ **키워드 ID는 숫자여야 합니다.**\n\n"
                "키워드 ID는 `/list_keywords` 명령어로 확인할 수 있습니다."
            )
            return
        
        try:
            db = SessionLocal()
            from app.models.database import Keyword
            
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            
            if not keyword:
                await update.message.reply_text(
                    f"❌ **ID {keyword_id}에 해당하는 키워드를 찾을 수 없습니다.**\n\n"
                    "등록된 키워드 목록은 `/list_keywords`로 확인하세요."
                )
                return
            
            keyword_name = keyword.keyword
            keyword_category = keyword.category
            
            db.delete(keyword)
            db.commit()
            
            await update.message.reply_text(
                f"✅ **키워드 제거 완료!**\n\n"
                f"🗑️ **제거된 키워드:** {keyword_name}\n"
                f"📂 **카테고리:** {keyword_category}\n"
                f"🆔 **ID:** {keyword_id}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"키워드 제거 오류: {e}")
            await update.message.reply_text(f"❌ 키워드 제거 중 오류가 발생했습니다: {str(e)}")
        finally:
            db.close()
    
    async def add_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 추가"""
        if not context.args:
            await update.message.reply_text(
                "❌ **사용법이 올바르지 않습니다.**\n\n"
                "**사용법:** `/add_channel [채널명 또는 URL]`\n\n"
                "**지원 형식:**\n"
                "• 채널명: `체슬리TV`\n"
                "• 핸들: `@chesleytv`\n"
                "• URL: `https://www.youtube.com/@chesleytv`\n"
                "• 채널 ID: `UCxxxxxxxxxxxx`",
                parse_mode='Markdown'
            )
            return
        
        channel_input = ' '.join(context.args)
        
        progress_msg = await update.message.reply_text(
            f"📺 **채널 추가 중...**\n\n"
            f"🔍 '{channel_input}' 정보를 가져오는 중...\n"
            "⏳ 잠시만 기다려주세요."
        )
        
        try:
            from app.services.data_collector import DataCollector
            data_collector = DataCollector()
            
            # 채널 ID 추출/변환
            channel_id = await self._resolve_channel_id(channel_input)
            
            if not channel_id:
                await progress_msg.edit_text(
                    f"❌ **채널을 찾을 수 없습니다.**\n\n"
                    f"입력: {channel_input}\n\n"
                    "다음을 확인해주세요:\n"
                    "• 채널명이 정확한지\n"
                    "• URL이 올바른지\n"
                    "• 채널이 공개되어 있는지"
                )
                return
            
            db = SessionLocal()
            
            # 중복 확인
            from app.models.database import Channel
            existing = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            if existing:
                await progress_msg.edit_text(
                    f"⚠️ **'{existing.channel_name}'는 이미 등록된 채널입니다.**\n\n"
                    f"🆔 채널 ID: {existing.channel_id}\n"
                    f"👥 구독자: {existing.subscriber_count:,}명\n"
                    f"📅 등록일: {existing.created_at.strftime('%Y-%m-%d')}"
                )
                return
            
            # 채널 추가
            channel = data_collector.add_channel(channel_id, db)
            
            if channel:
                await progress_msg.edit_text(
                    f"✅ **채널 추가 완료!**\n\n"
                    f"📺 **채널명:** {channel.channel_name}\n"
                    f"🆔 **채널 ID:** {channel.channel_id}\n"
                    f"👥 **구독자:** {channel.subscriber_count:,}명\n"
                    f"📹 **영상 수:** {channel.video_count:,}개\n\n"
                    f"이제 `/channel {channel.channel_name}` 명령어로 분석할 수 있습니다!",
                    parse_mode='Markdown'
                )
            else:
                await progress_msg.edit_text(
                    "❌ **채널 추가에 실패했습니다.**\n\n"
                    "채널 정보를 가져올 수 없습니다. 채널이 비공개이거나 존재하지 않을 수 있습니다."
                )
            
        except Exception as e:
            self.logger.error(f"채널 추가 오류: {e}")
            await progress_msg.edit_text(f"❌ 채널 추가 중 오류가 발생했습니다: {str(e)}")
        finally:
            db.close()
    
    async def _resolve_channel_id(self, channel_input: str) -> Optional[str]:
        """채널 입력값을 채널 ID로 변환"""
        try:
            from app.services.youtube_service import YouTubeService
            youtube_service = YouTubeService()
            
            # URL에서 채널 정보 추출
            if 'youtube.com' in channel_input:
                import re
                
                # @핸들 패턴
                handle_match = re.search(r'youtube\.com/@([a-zA-Z0-9_-]+)', channel_input)
                if handle_match:
                    handle = handle_match.group(1)
                    return youtube_service.get_channel_id_by_handle(f"@{handle}")
                
                # 채널 ID 패턴
                channel_match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', channel_input)
                if channel_match:
                    return channel_match.group(1)
                
                # 사용자명 패턴 (구형)
                user_match = re.search(r'youtube\.com/user/([a-zA-Z0-9_-]+)', channel_input)
                if user_match:
                    username = user_match.group(1)
                    return youtube_service.get_channel_id_by_username(username)
            
            # @핸들 직접 입력
            elif channel_input.startswith('@'):
                return youtube_service.get_channel_id_by_handle(channel_input)
            
            # 채널 ID 직접 입력
            elif channel_input.startswith('UC') and len(channel_input) == 24:
                return channel_input
            
            # 채널명으로 검색
            else:
                return youtube_service.search_channel_by_name(channel_input)
            
        except Exception as e:
            self.logger.error(f"채널 ID 변환 오류: {e}")
            return None
    
    async def remove_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 제거"""
        if not context.args:
            await update.message.reply_text(
                "❌ **사용법이 올바르지 않습니다.**\n\n"
                "**사용법:** `/remove_channel [채널ID]`\n\n"
                "채널 ID는 `/list_channels` 명령어로 확인할 수 있습니다.\n\n"
                "**예시:** `/remove_channel UCxxxxxxxxxxxx`",
                parse_mode='Markdown'
            )
            return
        
        channel_id = context.args[0]
        
        try:
            db = SessionLocal()
            from app.models.database import Channel
            
            channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            
            if not channel:
                await update.message.reply_text(
                    f"❌ **채널 ID '{channel_id}'에 해당하는 채널을 찾을 수 없습니다.**\n\n"
                    "등록된 채널 목록은 `/list_channels`로 확인하세요."
                )
                return
            
            channel_name = channel.channel_name
            
            # 관련 데이터도 함께 삭제할지 확인
            from app.models.database import Video
            video_count = db.query(Video).filter(Video.channel_id == channel_id).count()
            
            if video_count > 0:
                await update.message.reply_text(
                    f"⚠️ **채널 제거 확인**\n\n"
                    f"📺 **채널:** {channel_name}\n"
                    f"🆔 **ID:** {channel_id}\n"
                    f"📹 **영상 수:** {video_count}개\n\n"
                    f"이 채널과 관련된 **{video_count}개의 영상 데이터**도 함께 삭제됩니다.\n\n"
                    f"정말 삭제하시겠습니까?\n"
                    f"삭제하려면: `/confirm_remove_channel {channel_id}`",
                    parse_mode='Markdown'
                )
                return
            
            # 영상이 없으면 바로 삭제
            db.delete(channel)
            db.commit()
            
            await update.message.reply_text(
                f"✅ **채널 제거 완료!**\n\n"
                f"🗑️ **제거된 채널:** {channel_name}\n"
                f"🆔 **ID:** {channel_id}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"채널 제거 오류: {e}")
            await update.message.reply_text(f"❌ 채널 제거 중 오류가 발생했습니다: {str(e)}")
        finally:
            db.close()
    
    async def confirm_remove_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 제거 확인 및 실행"""
        if not context.args:
            await update.message.reply_text(
                "❌ **사용법이 올바르지 않습니다.**\n\n"
                "이 명령어는 `/remove_channel` 명령어 실행 후에만 사용할 수 있습니다."
            )
            return
        
        channel_id = context.args[0]
        
        try:
            db = SessionLocal()
            from app.models.database import Channel, Video, Analysis, Transcript
            
            channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            
            if not channel:
                await update.message.reply_text(
                    f"❌ **채널 ID '{channel_id}'에 해당하는 채널을 찾을 수 없습니다.**"
                )
                return
            
            channel_name = channel.channel_name
            
            # 관련 데이터 카운트
            video_count = db.query(Video).filter(Video.channel_id == channel_id).count()
            analysis_count = db.query(Analysis).join(Video).filter(Video.channel_id == channel_id).count()
            transcript_count = db.query(Transcript).join(Video).filter(Video.channel_id == channel_id).count()
            
            progress_msg = await update.message.reply_text(
                f"🗑️ **채널 삭제 진행 중...**\n\n"
                f"📺 **채널:** {channel_name}\n"
                f"📹 영상: {video_count}개\n"
                f"📝 자막: {transcript_count}개\n"
                f"🔍 분석: {analysis_count}개\n\n"
                "⏳ 데이터를 삭제하는 중..."
            )
            
            # 관련 데이터 삭제 (순서 중요)
            # 1. 분석 데이터 삭제
            db.query(Analysis).filter(
                Analysis.video_id.in_(
                    db.query(Video.video_id).filter(Video.channel_id == channel_id)
                )
            ).delete(synchronize_session=False)
            
            # 2. 자막 데이터 삭제
            db.query(Transcript).filter(
                Transcript.video_id.in_(
                    db.query(Video.video_id).filter(Video.channel_id == channel_id)
                )
            ).delete(synchronize_session=False)
            
            # 3. 비디오 데이터 삭제
            db.query(Video).filter(Video.channel_id == channel_id).delete()
            
            # 4. 채널 삭제
            db.delete(channel)
            
            db.commit()
            
            await progress_msg.edit_text(
                f"✅ **채널 삭제 완료!**\n\n"
                f"🗑️ **삭제된 채널:** {channel_name}\n"
                f"🆔 **ID:** {channel_id}\n\n"
                f"📊 **삭제된 데이터:**\n"
                f"• 📹 영상: {video_count}개\n"
                f"• 📝 자막: {transcript_count}개\n"
                f"• 🔍 분석: {analysis_count}개",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"채널 확인 삭제 오류: {e}")
            await update.message.reply_text(f"❌ 채널 삭제 중 오류가 발생했습니다: {str(e)}")
        finally:
            db.close()

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