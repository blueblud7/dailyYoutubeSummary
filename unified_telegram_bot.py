#!/usr/bin/env python3
"""
통합 텔레그램 봇 - 모든 기능 포함
YouTube URL 요약, 채널/키워드 관리, AI 분석 등
"""

import os
import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# 데이터베이스 및 서비스 import
from app.models.database import SessionLocal, Channel, Keyword, Video, Transcript, Analysis, create_tables
from app.services.youtube_service import YouTubeService
from app.services.analysis_service import AnalysisService

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv('config.env')

class UnifiedTelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.authorized_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        
        # 서비스 초기화
        self.youtube_service = YouTubeService()
        self.analysis_service = AnalysisService()
        
        # 테이블 생성 확인
        create_tables()
        
        # YouTube URL 패턴 정의
        self.youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)',
            r'https?://(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
        ]
        
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
        
    def is_authorized(self, update: Update) -> bool:
        """인증된 사용자인지 확인"""
        chat_id = str(update.effective_chat.id)
        return chat_id == self.authorized_chat_id
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 명령어"""
        if not self.is_authorized(update):
            if update.callback_query:
                await update.callback_query.answer("❌ 인증되지 않은 사용자입니다.")
                return
            elif update.message:
                await update.message.reply_text("❌ 인증되지 않은 사용자입니다.")
                return
        
        keyboard = [
            [InlineKeyboardButton("📺 채널 관리", callback_data="channels")],
            [InlineKeyboardButton("🔍 키워드 관리", callback_data="keywords")],
            [InlineKeyboardButton("🔎 키워드 검색", callback_data="keyword_search")],
            [InlineKeyboardButton("📊 분석 실행", callback_data="analyze")],
            [InlineKeyboardButton("📈 통계 보기", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🤖 **투자 분석 봇에 오신 것을 환영합니다!**\n\n"
            "🔥 **새로운 기능:** YouTube URL을 보내주시면 자동으로 AI가 요약해드립니다!\n\n"
            "**사용 가능한 기능:**\n"
            "• 📺 채널 구독 관리 (추가/삭제)\n"
            "• 🔍 키워드 관리 (추가/삭제)\n"
            "• 🔎 키워드 검색 (등록 안 된 것도 검색 가능)\n"
            "• 📊 정기 분석 실행\n"
            "• 🎬 YouTube URL 즉시 요약\n\n"
            "**YouTube URL 지원 형식:**\n"
            "• `https://youtube.com/watch?v=VIDEO_ID`\n"
            "• `https://youtu.be/VIDEO_ID`\n"
            "• `https://youtube.com/shorts/VIDEO_ID`\n\n"
            "💡 **사용법:** 버튼을 클릭하거나 YouTube URL을 그냥 보내주세요!"
        )
        
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            elif update.message:
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"start 메서드에서 오류 발생: {e}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """인라인 키보드 버튼 처리"""
        if not self.is_authorized(update):
            await update.callback_query.answer("❌ 인증되지 않은 사용자입니다.")
            return
        
        query = update.callback_query
        await query.answer()
        
        if query.data == "channels":
            await self.show_channel_menu(update, context)
        elif query.data == "keywords":
            await self.show_keyword_menu(update, context)
        elif query.data == "keyword_search":
            await self.show_keyword_search_prompt(update, context)
        elif query.data == "analyze":
            await self.run_analysis(update, context)
        elif query.data == "stats":
            await self.show_stats(update, context)
        elif query.data.startswith("add_channel"):
            await self.add_channel_prompt(update, context)
        elif query.data.startswith("remove_channel"):
            await self.show_remove_channel_list(update, context)
        elif query.data.startswith("del_ch_"):
            await self.remove_channel(update, context)
        elif query.data.startswith("add_keyword"):
            await self.add_keyword_prompt(update, context)
        elif query.data.startswith("remove_keyword"):
            await self.show_remove_keyword_list(update, context)
        elif query.data.startswith("del_kw_"):
            await self.remove_keyword(update, context)
        elif query.data == "back_main":
            await self.start(update, context)
    
    async def show_channel_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 관리 메뉴 표시"""
        db = SessionLocal()
        channels = db.query(Channel).all()
        db.close()
        
        if channels:
            channel_list = "\n".join([f"• {ch.channel_name}" for ch in channels])
        else:
            channel_list = "등록된 채널이 없습니다."
        
        keyboard = [
            [InlineKeyboardButton("➕ 채널 추가", callback_data="add_channel")],
            [InlineKeyboardButton("➖ 채널 제거", callback_data="remove_channel")],
            [InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"📺 **현재 구독 채널 ({len(channels)}개)**\n\n{channel_list}\n\n관리할 작업을 선택하세요:"
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_keyword_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 관리 메뉴 표시"""
        db = SessionLocal()
        keywords = db.query(Keyword).all()
        db.close()
        
        if keywords:
            keyword_list = "\n".join([f"• {kw.keyword} ({kw.category})" for kw in keywords])
        else:
            keyword_list = "등록된 키워드가 없습니다."
        
        keyboard = [
            [InlineKeyboardButton("➕ 키워드 추가", callback_data="add_keyword")],
            [InlineKeyboardButton("➖ 키워드 제거", callback_data="remove_keyword")],
            [InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"🔍 **현재 키워드 ({len(keywords)}개)**\n\n{keyword_list}\n\n관리할 작업을 선택하세요:"
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_keyword_search_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 검색 프롬프트 표시"""
        text = (
            "🔎 **키워드 검색**\n\n"
            "검색할 키워드를 입력해주세요.\n"
            "등록되지 않은 키워드도 검색 가능합니다!\n\n"
            "**예시:**\n"
            "• `비트코인`\n"
            "• `부동산`\n"
            "• `금리`\n"
            "• `삼성전자`\n\n"
            "💡 **기능:** 최근 영상 중 해당 키워드가 포함된 영상을 AI가 분석하여 결과를 제공합니다."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        context.user_data['action'] = 'keyword_search'
    
    async def add_channel_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 추가 안내"""
        text = (
            "📺 **채널 추가**\n\n"
            "추가할 채널명이나 YouTube URL을 보내주세요.\n\n"
            "예시:\n"
            "• `체슬리TV`\n"
            "• `https://www.youtube.com/@chesleytv`\n"
            "• `@chesleytv`\n"
            "• `UCxxxxxxxxxxxx` (채널 ID)"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 채널 메뉴", callback_data="channels")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        context.user_data['action'] = 'add_channel'
    
    async def show_remove_channel_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """제거할 채널 목록 표시"""
        db = SessionLocal()
        channels = db.query(Channel).all()
        db.close()
        
        if not channels:
            keyboard = [[InlineKeyboardButton("🔙 채널 메뉴", callback_data="channels")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "📺 등록된 채널이 없습니다.",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for channel in channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {channel.channel_name}", 
                    callback_data=f"del_ch_{channel.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 채널 메뉴", callback_data="channels")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text="📺 **제거할 채널을 선택하세요:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def remove_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 제거"""
        try:
            channel_id = int(update.callback_query.data.split('_')[2])
            
            db = SessionLocal()
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            
            if channel:
                channel_name = channel.channel_name
                db.delete(channel)
                db.commit()
                
                keyboard = [[InlineKeyboardButton("🔙 채널 메뉴", callback_data="channels")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    f"✅ **{channel_name}** 채널이 제거되었습니다.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.callback_query.edit_message_text("❌ 채널을 찾을 수 없습니다.")
            
            db.close()
            
        except Exception as e:
            logger.error(f"채널 제거 중 오류: {e}")
            await update.callback_query.edit_message_text(f"❌ 채널 제거 중 오류 발생: {str(e)}")
    
    async def add_keyword_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 추가 안내"""
        text = (
            "🔍 **키워드 추가**\n\n"
            "추가할 키워드와 카테고리를 다음 형식으로 보내주세요:\n\n"
            "`키워드 카테고리`\n\n"
            "예시:\n"
            "• `비트코인 암호화폐`\n"
            "• `부동산 투자`\n"
            "• `금리 경제`\n"
            "• `삼성전자 기업`"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 키워드 메뉴", callback_data="keywords")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        context.user_data['action'] = 'add_keyword'
    
    async def show_remove_keyword_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """제거할 키워드 목록 표시"""
        db = SessionLocal()
        keywords = db.query(Keyword).all()
        db.close()
        
        if not keywords:
            keyboard = [[InlineKeyboardButton("🔙 키워드 메뉴", callback_data="keywords")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "🔍 등록된 키워드가 없습니다.",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for keyword in keywords:
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {keyword.keyword} ({keyword.category})", 
                    callback_data=f"del_kw_{keyword.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 키워드 메뉴", callback_data="keywords")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text="🔍 **제거할 키워드를 선택하세요:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def remove_keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 제거"""
        try:
            keyword_id = int(update.callback_query.data.split('_')[2])
            
            db = SessionLocal()
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            
            if keyword:
                keyword_name = keyword.keyword
                db.delete(keyword)
                db.commit()
                
                keyboard = [[InlineKeyboardButton("🔙 키워드 메뉴", callback_data="keywords")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    f"✅ **{keyword_name}** 키워드가 제거되었습니다.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.callback_query.edit_message_text("❌ 키워드를 찾을 수 없습니다.")
            
            db.close()
            
        except Exception as e:
            logger.error(f"키워드 제거 중 오류: {e}")
            await update.callback_query.edit_message_text(f"❌ 키워드 제거 중 오류 발생: {str(e)}")
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """텍스트 메시지 처리"""
        if not self.is_authorized(update):
            await update.message.reply_text("❌ 인증되지 않은 사용자입니다.")
            return
        
        message_text = update.message.text.strip()
        action = context.user_data.get('action')
        
        # YouTube URL 감지 및 처리
        video_id = self.extract_video_id(message_text)
        if video_id:
            await self.process_youtube_url(update, context, video_id, message_text)
            return
        
        # 기존 액션 처리
        if action == 'add_channel':
            await self.process_add_channel(update, context)
        elif action == 'add_keyword':
            await self.process_add_keyword(update, context)
        elif action == 'keyword_search':
            await self.process_keyword_search(update, context)
        else:
            await update.message.reply_text(
                "❓ 알 수 없는 명령입니다.\n\n"
                "💡 **사용 가능한 기능:**\n"
                "• /start - 메뉴 보기\n"
                "• YouTube URL 공유 - 영상 요약\n"
                "• 채널명/키워드 입력 (메뉴에서 선택 후)"
            )
    
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
            video_data = await self.get_video_info(video_id)
            
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
            transcript = self.youtube_service.get_video_transcript(video_id)
            transcript_text = transcript.get('text', '') if transcript else ''
            
            if not transcript_text:
                await progress_msg.edit_text(
                    f"⚠️ **자막을 찾을 수 없습니다**\n\n"
                    f"📹 **{video_data['title']}**\n"
                    f"👤 채널: {video_data['channel_name']}\n"
                    f"👀 조회수: {video_data['view_count']:,}회\n"
                    f"🔗 {url}\n\n"
                    "자막이 없거나 비활성화된 영상입니다.",
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
            analysis_result = self.analysis_service.analyze_transcript(
                transcript_text=transcript_text,
                video_title=video_data['title'],
                channel_name=video_data['channel_name']
            )
            
            # 결과 전송
            await self.send_analysis_result(update, video_data, analysis_result, url, progress_msg)
            
        except Exception as e:
            logger.error(f"YouTube URL 처리 중 오류: {e}")
            await progress_msg.edit_text(
                f"❌ **처리 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {str(e)}"
            )
    
    async def get_video_info(self, video_id: str) -> Optional[Dict]:
        """YouTube 영상 정보 가져오기"""
        try:
            # YouTube API로 영상 정보 가져오기
            video_request = self.youtube_service.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            video_response = video_request.execute()
            
            if not video_response['items']:
                return None
            
            video_info = video_response['items'][0]
            snippet = video_info['snippet']
            
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
            logger.error(f"영상 정보 가져오기 실패: {e}")
            return None
    
    async def send_analysis_result(self, update: Update, video_data: dict, analysis: dict, url: str, progress_msg):
        """분석 결과 전송"""
        try:
            # 기본 영상 정보
            basic_info = (
                f"🎬 **YouTube 영상 AI 요약 완료**\n\n"
                f"📹 **제목:** {video_data['title']}\n"
                f"👤 **채널:** {video_data['channel_name']}\n"
                f"👀 **조회수:** {video_data['view_count']:,}회\n"
                f"👍 **좋아요:** {video_data['like_count']:,}개\n"
                f"🔗 **링크:** {url}\n"
            )
            
            # 요약 정보
            summary = analysis.get('summary', '요약 정보가 없습니다.')
            market_outlook = analysis.get('market_outlook', '')
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
            
            if market_outlook:
                summary_text += f"🔮 **시장 관점:** {market_outlook}\n"
            
            # 메인 요약 전송
            await progress_msg.edit_text(
                summary_text,
                parse_mode='Markdown'
            )
            
            # 주요 인사이트
            key_insights = analysis.get('key_insights', [])
            if key_insights:
                insights_text = "💡 **주요 인사이트:**\n"
                for i, insight in enumerate(key_insights[:5], 1):
                    insights_text += f"{i}. {insight}\n"
                
                await update.message.reply_text(
                    insights_text,
                    parse_mode='Markdown'
                )
            
            # 투자 테마 및 실행 가능한 조언
            investment_themes = analysis.get('investment_themes', [])
            actionable_insights = analysis.get('actionable_insights', [])
            
            if investment_themes or actionable_insights:
                investment_text = ""
                
                if investment_themes:
                    investment_text += "🏷️ **투자 테마:**\n"
                    investment_text += "• " + "\n• ".join(investment_themes[:3]) + "\n\n"
                
                if actionable_insights:
                    investment_text += "⚡ **실행 가능한 조언:**\n"
                    for i, advice in enumerate(actionable_insights[:3], 1):
                        investment_text += f"{i}. {advice}\n"
                
                await update.message.reply_text(
                    investment_text,
                    parse_mode='Markdown'
                )
            
            # 언급된 주요 기업/인물
            mentioned_entities = analysis.get('mentioned_entities', [])
            if mentioned_entities:
                entities_text = f"🏢 **언급된 주요 기업/인물:**\n"
                entities_text += "• " + "\n• ".join(mentioned_entities[:5])
                
                await update.message.reply_text(
                    entities_text,
                    parse_mode='Markdown'
                )
                    
        except Exception as e:
            logger.error(f"결과 전송 실패: {e}")
            await update.message.reply_text(f"❌ 결과 전송 중 오류: {str(e)}")
    
    async def process_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 추가 처리"""
        text = update.message.text.strip()
        
        try:
            # 채널 검색
            channels = self.youtube_service.search_channels(text, max_results=1)
            
            if not channels:
                await update.message.reply_text(
                    f"❌ '{text}' 채널을 찾을 수 없습니다.\n"
                    "다른 검색어를 시도해보세요."
                )
                return
            
            channel_info = channels[0]
            channel_id = channel_info['channel_id']
            
            # 상세 정보 가져오기
            detailed_info = self.youtube_service.get_channel_details(channel_id)
            
            if not detailed_info:
                await update.message.reply_text("❌ 채널 정보를 가져올 수 없습니다.")
                return
            
            # 데이터베이스에 추가
            db = SessionLocal()
            
            # 중복 확인
            existing = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            if existing:
                await update.message.reply_text(f"⚠️ **{detailed_info['channel_name']}**은 이미 구독 중인 채널입니다.")
                db.close()
                return
            
            channel = Channel(
                channel_id=channel_id,
                channel_name=detailed_info['channel_name'],
                channel_url=detailed_info['channel_url'],
                description=detailed_info['description'][:500] if detailed_info['description'] else '',
                subscriber_count=detailed_info['subscriber_count'],
                video_count=detailed_info['video_count']
            )
            
            db.add(channel)
            db.commit()
            db.close()
            
            await update.message.reply_text(
                f"✅ **{detailed_info['channel_name']}** 채널이 추가되었습니다!\n\n"
                f"📊 **채널 정보:**\n"
                f"• 구독자: {detailed_info['subscriber_count']:,}명\n"
                f"• 영상 수: {detailed_info['video_count']:,}개\n"
                f"• 설명: {detailed_info['description'][:100]}...\n\n"
                f"🔗 {detailed_info['channel_url']}",
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"채널 추가 중 오류: {e}")
            await update.message.reply_text(f"❌ 채널 추가 중 오류 발생: {str(e)}")
        
        context.user_data.pop('action', None)
    
    async def process_add_keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 추가 처리"""
        text = update.message.text.strip()
        parts = text.split()
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ 형식이 올바르지 않습니다.\n`키워드 카테고리` 형식으로 입력해주세요.\n\n"
                "예: `비트코인 암호화폐`"
            )
            return
        
        keyword = parts[0]
        category = " ".join(parts[1:])
        
        try:
            db = SessionLocal()
            
            # 중복 확인
            existing = db.query(Keyword).filter(Keyword.keyword == keyword).first()
            if existing:
                await update.message.reply_text(f"⚠️ **{keyword}**는 이미 등록된 키워드입니다.")
                db.close()
                return
            
            new_keyword = Keyword(
                keyword=keyword,
                category=category
            )
            
            db.add(new_keyword)
            db.commit()
            db.close()
            
            await update.message.reply_text(
                f"✅ **{keyword}** ({category}) 키워드가 추가되었습니다!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"키워드 추가 중 오류: {e}")
            await update.message.reply_text(f"❌ 키워드 추가 중 오류 발생: {str(e)}")
        
        context.user_data.pop('action', None)
    
    async def process_keyword_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 검색 처리"""
        keyword = update.message.text.strip()
        
        if not keyword:
            await update.message.reply_text("❌ 키워드를 입력해주세요.")
            return
        
        progress_msg = await update.message.reply_text(
            f"🔍 **'{keyword}' 키워드 검색 중...**\n\n"
            "📹 YouTube에서 관련 영상을 검색하고 있습니다...\n"
            "⏳ 잠시만 기다려주세요."
        )
        
        try:
            # YouTube에서 키워드 검색
            recent_date = datetime.now() - timedelta(days=7)
            videos = self.youtube_service.search_videos_by_keyword(
                keyword=keyword,
                max_results=5,
                published_after=recent_date
            )
            
            if not videos:
                await progress_msg.edit_text(
                    f"🔍 **'{keyword}' 검색 결과**\n\n"
                    f"❌ 최근 7일 내 '{keyword}' 관련 영상을 찾을 수 없습니다.\n\n"
                    "💡 **제안:**\n"
                    "• 다른 키워드로 검색해보세요\n"
                    "• 더 일반적인 용어를 사용해보세요"
                )
                return
            
            # 검색 결과 표시
            results_text = f"🔍 **'{keyword}' 검색 결과 ({len(videos)}개)**\n\n"
            
            for i, video in enumerate(videos, 1):
                results_text += f"**{i}. {video['title'][:60]}...**\n"
                results_text += f"👤 {video['channel_name']}\n"
                results_text += f"👀 {video['view_count']:,}회 | 📅 {video['published_at'].strftime('%m-%d')}\n"
                results_text += f"🔗 https://www.youtube.com/watch?v={video['video_id']}\n\n"
            
            await progress_msg.edit_text(
                results_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"키워드 검색 중 오류: {e}")
            await progress_msg.edit_text(
                f"❌ **키워드 검색 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {str(e)}"
            )
        
        context.user_data.pop('action', None)
    
    async def run_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """분석 실행"""
        await update.callback_query.edit_message_text(
            "📊 **정기 분석을 시작합니다...**\n\n"
            "⏳ 구독된 채널의 최신 영상들을 분석 중입니다...\n"
            "이 작업은 몇 분이 소요될 수 있습니다."
        )
        
        try:
            db = SessionLocal()
            channels = db.query(Channel).all()
            
            if not channels:
                await update.callback_query.edit_message_text(
                    "❌ **분석할 채널이 없습니다.**\n\n"
                    "먼저 채널을 추가해주세요."
                )
                db.close()
                return
            
            total_videos = 0
            analyzed_videos = 0
            
            # 최근 24시간 영상 분석
            recent_date = datetime.now() - timedelta(hours=24)
            
            for channel in channels:
                videos = self.youtube_service.get_channel_videos(
                    channel_id=channel.channel_id,
                    max_results=10,
                    published_after=recent_date
                )
                
                total_videos += len(videos)
                
                for video in videos:
                    # 자막 가져오기 및 분석
                    transcript = self.youtube_service.get_video_transcript(video['video_id'])
                    if transcript and transcript.get('text'):
                        analysis = self.analysis_service.analyze_transcript(
                            transcript_text=transcript['text'],
                            video_title=video['title'],
                            channel_name=channel.channel_name
                        )
                        if analysis.get('summary'):
                            analyzed_videos += 1
            
            db.close()
            
            await update.callback_query.edit_message_text(
                f"✅ **분석 완료!**\n\n"
                f"📺 총 채널: {len(channels)}개\n"
                f"📹 발견된 영상: {total_videos}개\n"
                f"🤖 분석 완료: {analyzed_videos}개\n\n"
                f"📊 자세한 분석 결과는 개별적으로 확인하실 수 있습니다."
            )
                
        except Exception as e:
            logger.error(f"분석 실행 중 오류: {e}")
            await update.callback_query.edit_message_text(f"❌ 분석 실행 중 오류: {str(e)}")
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """통계 표시"""
        try:
            db = SessionLocal()
            
            # 기본 통계
            total_channels = db.query(Channel).count()
            total_keywords = db.query(Keyword).count()
            total_videos = db.query(Video).count()
            total_analyses = db.query(Analysis).count()
            
            # 최근 7일 분석
            recent_date = datetime.now() - timedelta(days=7)
            recent_analyses = db.query(Analysis).filter(Analysis.created_at >= recent_date).count()
            
            db.close()
            
            text = (
                f"📊 **시스템 통계**\n\n"
                f"📺 **구독 채널**: {total_channels}개\n"
                f"🔍 **키워드**: {total_keywords}개\n"
                f"📹 **총 영상**: {total_videos}개\n"
                f"🤖 **총 분석**: {total_analyses}개\n"
                f"🆕 **최근 7일 분석**: {recent_analyses}개\n\n"
                f"🎬 **주요 기능:**\n"
                f"• YouTube URL 즉시 AI 요약\n"
                f"• 키워드/채널 관리 (추가/삭제)\n"
                f"• 정기 분석 및 트렌드 보고서\n"
                f"• 실시간 키워드 검색"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"통계 조회 중 오류: {e}")
            await update.callback_query.edit_message_text(f"❌ 통계 조회 중 오류: {str(e)}")
    
    def run(self):
        """봇 실행"""
        application = Application.builder().token(self.token).build()
        
        # 핸들러 등록
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        logger.info("🤖 통합 텔레그램 봇이 시작되었습니다!")
        logger.info("="*50)
        logger.info("📱 주요 기능:")
        logger.info("• 🎬 YouTube URL 즉시 AI 요약")
        logger.info("• 📺 채널 구독 관리 (추가/삭제)")
        logger.info("• 🔍 키워드 관리 (추가/삭제)")
        logger.info("• 🔎 실시간 키워드 검색")
        logger.info("• 📊 정기 분석 및 통계")
        logger.info("="*50)
        
        application.run_polling()

if __name__ == "__main__":
    bot = UnifiedTelegramBot()
    bot.run() 