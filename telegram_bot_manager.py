#!/usr/bin/env python3
"""
텔레그램 봇을 통한 구독 채널 및 키워드 관리 + YouTube URL 요약 + 키워드 검색
"""

import os
import logging
import json
import re
from typing import Dict, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

from app.models.database import SessionLocal, Channel, Keyword, create_tables
# from smart_subscription_reporter_v2 import SmartSubscriptionReporterV2  # 임시 비활성화

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv('config.env')

class TelegramBotManager:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.authorized_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        # self.reporter = SmartSubscriptionReporterV2()  # 임시 비활성화
        self.reporter = None
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        
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
            # 메시지 타입에 따라 적절한 응답 방법 선택
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
            "🔥 **새로운 기능:** YouTube URL을 보내주시면 자동으로 요약해드립니다!\n\n"
            "**사용 가능한 기능:**\n"
            "• 📺 채널 구독 관리\n"
            "• 🔍 키워드 관리\n"
            "• 🔎 키워드 검색 (등록 안 된 것도 검색 가능)\n"
            "• 📊 정기 분석 실행\n"
            "• 🎬 YouTube URL 즉시 요약\n\n"
            "**YouTube URL 지원 형식:**\n"
            "• `https://youtube.com/watch?v=VIDEO_ID`\n"
            "• `https://youtu.be/VIDEO_ID`\n"
            "• `https://youtube.com/shorts/VIDEO_ID`"
        )
        
        # 메시지 타입에 따라 적절한 응답 방법 선택
        try:
            if update.callback_query:
                # 인라인 키보드에서 호출된 경우
                await update.callback_query.edit_message_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            elif update.message:
                # 일반 메시지에서 호출된 경우
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"start 메서드에서 오류 발생: {e}")
            # fallback 응답
            if update.callback_query:
                await update.callback_query.answer("메뉴 로딩 중 오류가 발생했습니다.")
            elif update.message:
                await update.message.reply_text("메뉴 로딩 중 오류가 발생했습니다.")
    
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
            await self.start(update, context)  # 이제 정상 작동합니다
    
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
            # 카테고리별로 정리
            categories = {}
            for kw in keywords:
                if kw.category not in categories:
                    categories[kw.category] = []
                categories[kw.category].append(kw.keyword)
            
            keyword_list = ""
            for category, kw_list in categories.items():
                keyword_list += f"**{category}**: {', '.join(kw_list)}\n"
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
        
        # 다음 메시지를 키워드 검색으로 처리하도록 상태 저장
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
        
        # 다음 메시지를 채널 추가로 처리하도록 상태 저장
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
    
    async def process_keyword_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """키워드 검색 처리 - 등록되지 않은 키워드도 검색 가능"""
        keyword = update.message.text.strip()
        
        if not keyword:
            await update.message.reply_text("❌ 키워드를 입력해주세요.")
            return
        
        # 진행 상황 메시지
        progress_msg = await update.message.reply_text(
            f"🔍 **'{keyword}' 키워드 검색 중...**\n\n"
            "📹 최근 영상들에서 해당 키워드를 검색하고 있습니다...\n"
            "⏳ 잠시만 기다려주세요."
        )
        
        try:
            # 최근 영상들 검색
            search_results = await self.search_keyword_in_videos(keyword)
            
            if search_results:
                await self.send_keyword_search_results(update, keyword, search_results, progress_msg)
            else:
                await progress_msg.edit_text(
                    f"🔍 **'{keyword}' 검색 결과**\n\n"
                    f"❌ 최근 영상에서 '{keyword}' 관련 내용을 찾을 수 없습니다.\n\n"
                    "💡 **제안:**\n"
                    "• 다른 키워드로 검색해보세요\n"
                    "• 더 일반적인 용어를 사용해보세요\n"
                    "• 영어나 한글로 다시 검색해보세요"
                )
                
        except Exception as e:
            logger.error(f"키워드 검색 중 오류: {e}")
            await progress_msg.edit_text(
                f"❌ **키워드 검색 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {str(e)}"
            )
        
        # 상태 초기화
        context.user_data.pop('action', None)
    
    async def search_keyword_in_videos(self, keyword: str) -> List[Dict]:
        """최근 영상들에서 키워드 검색"""
        db = SessionLocal()
        try:
            # 최근 7일간의 영상들 가져오기
            from app.models.database import Video, VideoAnalysis
            from datetime import datetime, timedelta
            
            recent_date = datetime.now() - timedelta(days=7)
            
            # 영상과 분석 정보 조인하여 가져오기
            results = db.execute("""
                SELECT DISTINCT v.video_id, v.title, v.published_at, v.view_count, 
                       c.channel_name, va.executive_summary, va.detailed_insights, 
                       va.investment_implications, va.topics
                FROM videos v
                JOIN channels c ON v.channel_id = c.channel_id  
                LEFT JOIN video_analyses va ON v.video_id = va.video_id
                WHERE v.published_at >= ?
                ORDER BY v.published_at DESC
                LIMIT 50
            """, (recent_date,)).fetchall()
            
            matching_videos = []
            
            for row in results:
                video_data = {
                    'video_id': row[0],
                    'title': row[1],
                    'published_at': row[2],
                    'view_count': row[3] or 0,
                    'channel_name': row[4],
                    'executive_summary': row[5] or '',
                    'detailed_insights': row[6] or '',
                    'investment_implications': row[7] or '',
                    'topics': row[8] or ''
                }
                
                # 키워드 매칭 확인 (제목, 요약, 인사이트, 토픽에서)
                keyword_lower = keyword.lower()
                search_text = f"{video_data['title']} {video_data['executive_summary']} {video_data['detailed_insights']} {video_data['topics']}".lower()
                
                if keyword_lower in search_text:
                    matching_videos.append(video_data)
            
            return matching_videos[:10]  # 최대 10개 결과
            
        except Exception as e:
            logger.error(f"키워드 검색 중 데이터베이스 오류: {e}")
            return []
        finally:
            db.close()
    
    async def send_keyword_search_results(self, update: Update, keyword: str, results: List[Dict], progress_msg):
        """키워드 검색 결과 전송"""
        try:
            if not results:
                await progress_msg.edit_text(f"🔍 '{keyword}' 검색 결과가 없습니다.")
                return
            
            # 메인 결과 메시지
            main_text = (
                f"🔍 **'{keyword}' 검색 결과 ({len(results)}개)**\n\n"
                f"📅 **검색 범위:** 최근 7일\n"
                f"📊 **매칭된 영상:** {len(results)}개\n\n"
            )
            
            # 상위 3개 영상 상세 표시
            for i, video in enumerate(results[:3], 1):
                published_date = video['published_at'][:10] if video['published_at'] else 'Unknown'
                
                main_text += f"**{i}. [{video['channel_name']}] {video['title'][:60]}...**\n"
                main_text += f"📅 {published_date} | 👀 {video['view_count']:,}회\n"
                
                # 요약이 있으면 표시
                if video['executive_summary']:
                    summary = video['executive_summary'][:150] + "..." if len(video['executive_summary']) > 150 else video['executive_summary']
                    main_text += f"📝 {summary}\n"
                
                main_text += f"🔗 https://www.youtube.com/watch?v={video['video_id']}\n\n"
            
            # 진행 메시지 업데이트
            await progress_msg.edit_text(
                main_text,
                parse_mode='Markdown'
            )
            
            # 나머지 영상들 간단히 표시
            if len(results) > 3:
                remaining_text = f"📋 **기타 관련 영상 ({len(results)-3}개)**\n\n"
                
                for i, video in enumerate(results[3:], 4):
                    published_date = video['published_at'][:10] if video['published_at'] else 'Unknown'
                    remaining_text += f"{i}. **{video['title'][:50]}...**\n"
                    remaining_text += f"   📺 {video['channel_name']} | 📅 {published_date}\n"
                    remaining_text += f"   🔗 https://www.youtube.com/watch?v={video['video_id']}\n\n"
                
                await update.message.reply_text(
                    remaining_text,
                    parse_mode='Markdown'
                )
            
            # 투자 시사점이 있는 영상들 따로 표시
            investment_insights = []
            for video in results:
                if video['investment_implications']:
                    investment_insights.append(video)
            
            if investment_insights:
                investment_text = f"💰 **'{keyword}' 관련 투자 시사점**\n\n"
                
                for video in investment_insights[:3]:
                    implications = video['investment_implications'][:200] + "..." if len(video['investment_implications']) > 200 else video['investment_implications']
                    investment_text += f"**{video['title'][:40]}...**\n"
                    investment_text += f"💡 {implications}\n\n"
                
                await update.message.reply_text(
                    investment_text,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"검색 결과 전송 실패: {e}")
            await update.message.reply_text(f"❌ 결과 전송 중 오류: {str(e)}")
    
    async def process_youtube_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str, url: str):
        """YouTube URL 처리 및 요약"""
        
        # 진행 상황 메시지 전송
        progress_msg = await update.message.reply_text(
            "🎬 **YouTube 영상 분석 중...**\n\n"
            f"📹 영상 ID: `{video_id}`\n"
            "⏳ 영상 정보를 가져오는 중...",
            parse_mode='Markdown'
        )
        
        try:
            # 영상 정보 가져오기
            await progress_msg.edit_text(
                "🎬 **YouTube 영상 분석 중...**\n\n"
                f"📹 영상 ID: `{video_id}`\n"
                "📝 영상 정보 및 자막을 가져오는 중...",
                parse_mode='Markdown'
            )
            
            # 영상 정보 및 자막 가져오기
            video_data = await self.get_video_data(video_id)
            
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
            
            # AI 분석 진행
            await progress_msg.edit_text(
                "🎬 **YouTube 영상 분석 중...**\n\n"
                f"📹 **{video_data['title']}**\n"
                f"👤 채널: {video_data['channel_name']}\n"
                f"⏱️ 길이: {video_data['duration']}\n\n"
                "🤖 AI 분석 진행 중... (30초~1분 소요)",
                parse_mode='Markdown'
            )
            
            # AI 분석 실행
            analysis_result = await self.analyze_video_with_ai(video_data)
            
            if analysis_result:
                # 결과 전송
                await self.send_analysis_result(update, video_data, analysis_result, progress_msg)
            else:
                await progress_msg.edit_text(
                    "❌ **AI 분석에 실패했습니다.**\n\n"
                    "자막이 없거나 분석할 수 없는 내용입니다."
                )
            
        except Exception as e:
            logger.error(f"YouTube URL 처리 중 오류: {e}")
            await progress_msg.edit_text(
                f"❌ **처리 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {str(e)}"
            )
    
    async def get_video_data(self, video_id: str) -> dict:
        """YouTube 영상 데이터 가져오기"""
        try:
            # YouTube API로 영상 정보 가져오기
            video_response = self.reporter._execute_youtube_api_with_retry(
                lambda: self.reporter.youtube.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=video_id
                ).execute()
            )
            
            if not video_response['items']:
                return None
            
            video_info = video_response['items'][0]
            snippet = video_info['snippet']
            
            # 자막 가져오기 시도
            transcript_text = ""
            try:
                transcript_text = self.reporter.get_video_transcript(video_id)
            except Exception as e:
                logger.warning(f"자막 가져오기 실패 (video_id: {video_id}): {e}")
            
            return {
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'channel_name': snippet['channelTitle'],
                'channel_id': snippet['channelId'],
                'published_at': snippet['publishedAt'],
                'duration': video_info['contentDetails']['duration'],
                'view_count': int(video_info['statistics'].get('viewCount', 0)),
                'like_count': int(video_info['statistics'].get('likeCount', 0)),
                'transcript': transcript_text,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
            
        except Exception as e:
            logger.error(f"영상 데이터 가져오기 실패: {e}")
            return None
    
    async def analyze_video_with_ai(self, video_data: dict) -> dict:
        """AI를 사용한 영상 분석"""
        try:
            if not video_data['transcript']:
                return None
            
            # AI 분석 실행 (올바른 파라미터 사용)
            analysis = self.reporter.analyze_content_with_ai(
                title=video_data['title'],
                transcript=video_data['transcript'],
                channel_name=video_data['channel_name'],
                video_id=video_data['video_id']
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI 분석 실패: {e}")
            return None
    
    async def send_analysis_result(self, update: Update, video_data: dict, analysis: dict, progress_msg):
        """분석 결과 전송"""
        try:
            # 기본 영상 정보
            basic_info = (
                f"🎬 **YouTube 영상 요약 완료**\n\n"
                f"📹 **제목:** {video_data['title']}\n"
                f"👤 **채널:** {video_data['channel_name']}\n"
                f"👀 **조회수:** {video_data['view_count']:,}회\n"
                f"👍 **좋아요:** {video_data['like_count']:,}개\n"
                f"🔗 **링크:** {video_data['url']}\n"
            )
            
            # 종합 요약
            executive_summary = analysis.get('summary', '요약 정보가 없습니다.')
            summary_text = (
                f"{basic_info}\n"
                f"📋 **종합 요약:**\n{executive_summary}\n"
            )
            
            # 메인 요약 전송 (진행 메시지 업데이트)
            await progress_msg.edit_text(
                summary_text,
                parse_mode='Markdown'
            )
            
            # 상세 분석이 있으면 추가 메시지 전송
            if analysis.get('detailed_analysis'):
                detailed_analysis = analysis['detailed_analysis']
                
                # 상세 인사이트
                if detailed_analysis.get('detailed_insights'):
                    detailed_text = f"🔍 **상세 분석:**\n{detailed_analysis['detailed_insights']}"
                    
                    if len(detailed_text) > 4000:
                        # 긴 텍스트는 나누어 전송
                        chunks = [detailed_text[i:i+4000] for i in range(0, len(detailed_text), 4000)]
                        for i, chunk in enumerate(chunks):
                            chunk_title = f"📄 **상세 분석 ({i+1}/{len(chunks)})**\n\n" if i == 0 else ""
                            await update.message.reply_text(
                                chunk_title + chunk,
                                parse_mode='Markdown'
                            )
                    else:
                        await update.message.reply_text(
                            detailed_text,
                            parse_mode='Markdown'
                        )
                
                # 투자 시사점이 있으면 전송
                if detailed_analysis.get('investment_implications'):
                    investment_implications = detailed_analysis['investment_implications']
                    if isinstance(investment_implications, dict):
                        investment_text = "💰 **투자 시사점:**\n"
                        if investment_implications.get('short_term'):
                            investment_text += f"**단기:** {investment_implications['short_term']}\n"
                        if investment_implications.get('long_term'):
                            investment_text += f"**장기:** {investment_implications['long_term']}\n"
                    else:
                        investment_text = f"💰 **투자 시사점:**\n{investment_implications}"
                    
                    await update.message.reply_text(
                        investment_text,
                        parse_mode='Markdown'
                    )
                
                # 핵심 키워드 표시
                if analysis.get('topics'):
                    topics_text = f"🏷️ **핵심 키워드:** {analysis['topics']}"
                    await update.message.reply_text(
                        topics_text,
                        parse_mode='Markdown'
                    )
                    
        except Exception as e:
            logger.error(f"결과 전송 실패: {e}")
            await update.message.reply_text(f"❌ 결과 전송 중 오류: {str(e)}")
    
    async def process_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """채널 추가 처리"""
        text = update.message.text.strip()
        
        try:
            # URL에서 채널 ID 추출 시도
            channel_id = None
            
            # 다양한 YouTube 채널 URL 패턴 처리
            channel_patterns = [
                r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
                r'youtube\.com/@([a-zA-Z0-9_-]+)',
                r'youtube\.com/c/([a-zA-Z0-9_-]+)',
                r'youtube\.com/user/([a-zA-Z0-9_-]+)',
                r'^UC[a-zA-Z0-9_-]+$',  # 직접 채널 ID
                r'^@([a-zA-Z0-9_-]+)$'  # @username 형식
            ]
            
            for pattern in channel_patterns:
                match = re.search(pattern, text)
                if match:
                    if pattern.startswith('^UC'):  # 직접 채널 ID
                        channel_id = text
                    elif pattern.startswith('^@'):  # @username
                        username = match.group(1)
                        # username으로 검색
                        text = username
                    else:
                        # URL에서 추출된 경우 검색으로 처리
                        text = match.group(1)
                    break
            
            # 채널 ID가 직접 제공되지 않은 경우 검색
            if not channel_id:
                # YouTube 검색으로 채널 찾기
                result = self.reporter._execute_youtube_api_with_retry(
                    lambda: self.reporter.youtube.search().list(
                        part='snippet',
                        q=text,
                        type='channel',
                        maxResults=5
                    ).execute()
                )
                
                if not result['items']:
                    await update.message.reply_text(
                        f"❌ '{text}' 채널을 찾을 수 없습니다.\n"
                        "다른 검색어를 시도해보세요."
                    )
                    return
                
                # 첫 번째 결과 사용
                item = result['items'][0]
                channel_id = item['id']['channelId']
            
            # 채널 상세 정보 가져오기
            channel_response = self.reporter._execute_youtube_api_with_retry(
                lambda: self.reporter.youtube.channels().list(
                    part='snippet,statistics',
                    id=channel_id
                ).execute()
            )
            
            if not channel_response['items']:
                await update.message.reply_text("❌ 채널 정보를 가져올 수 없습니다.")
                return
            
            channel_info = channel_response['items'][0]
            snippet = channel_info['snippet']
            statistics = channel_info['statistics']
            
            channel_name = snippet['title']
            description = snippet.get('description', '')[:200] + "..." if len(snippet.get('description', '')) > 200 else snippet.get('description', '')
            subscriber_count = int(statistics.get('subscriberCount', 0))
            video_count = int(statistics.get('videoCount', 0))
            
            # 데이터베이스에 추가
            db = SessionLocal()
            
            # 중복 확인
            existing = db.query(Channel).filter(Channel.channel_id == channel_id).first()
            if existing:
                await update.message.reply_text(f"⚠️ **{channel_name}**은 이미 구독 중인 채널입니다.")
                db.close()
                return
            
            channel = Channel(
                channel_id=channel_id,
                channel_name=channel_name,
                channel_url=f"https://www.youtube.com/channel/{channel_id}",
                description=description
            )
            
            db.add(channel)
            db.commit()
            db.close()
            
            await update.message.reply_text(
                f"✅ **{channel_name}** 채널이 추가되었습니다!\n\n"
                f"📊 **채널 정보:**\n"
                f"• 구독자: {subscriber_count:,}명\n"
                f"• 영상 수: {video_count:,}개\n"
                f"• 설명: {description}\n\n"
                f"🔗 https://www.youtube.com/channel/{channel_id}",
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"채널 추가 중 오류: {e}")
            await update.message.reply_text(f"❌ 채널 추가 중 오류 발생: {str(e)}")
        
        # 상태 초기화
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
        
        # 상태 초기화
        context.user_data.pop('action', None)
    
    async def run_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """분석 실행"""
        await update.callback_query.edit_message_text("🔍 **분석을 시작합니다...**")
        
        try:
            # 분석 실행
            success = self.reporter.run_detailed_analysis(
                hours_back=24,
                send_telegram=True
            )
            
            if success:
                await update.callback_query.edit_message_text(
                    "✅ **분석이 완료되었습니다!**\n"
                    "결과가 별도 메시지로 전송됩니다."
                )
            else:
                await update.callback_query.edit_message_text("❌ 분석 중 오류가 발생했습니다.")
                
        except Exception as e:
            logger.error(f"분석 실행 중 오류: {e}")
            await update.callback_query.edit_message_text(f"❌ 분석 실행 중 오류: {str(e)}")
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """통계 표시"""
        try:
            # 캐시 통계
            stats = self.reporter.cache_service.get_cache_statistics()
            
            # 채널 통계
            db = SessionLocal()
            total_channels = db.query(Channel).count()
            total_keywords = db.query(Keyword).count()
            db.close()
            
            text = (
                f"📊 **시스템 통계**\n\n"
                f"📺 **구독 채널**: {total_channels}개\n"
                f"🔍 **키워드**: {total_keywords}개\n"
                f"📹 **전체 영상**: {stats.get('total_videos', 0)}개\n"
                f"🎯 **캐시된 분석**: {stats.get('cached_analyses', 0)}개\n"
                f"📝 **자막 보유**: {stats.get('total_transcripts', 0)}개\n"
                f"📊 **캐시 히트율**: {stats.get('cache_hit_rate', 0)}%\n"
                f"🆕 **최근 7일 분석**: {stats.get('recent_analyses', 0)}개\n\n"
                f"🎬 **새로운 기능**: YouTube URL 즉시 요약\n"
                f"🔎 **키워드 검색**: 등록 안 된 키워드도 검색 가능"
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
        
        print("🤖 텔레그램 봇이 시작되었습니다...")
        print("🎬 YouTube URL 요약 기능이 활성화되었습니다!")
        print("🔎 키워드 검색 기능이 활성화되었습니다!")
        print("📺 채널 관리 기능이 완전히 구현되었습니다!")
        application.run_polling()

if __name__ == "__main__":
    bot = TelegramBotManager()
    bot.run() 