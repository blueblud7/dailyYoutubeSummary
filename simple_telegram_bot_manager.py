#!/usr/bin/env python3
"""
간단한 텔레그램 봇 관리자 (버튼 포함)
"""

import os
import logging
import re
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

from app.models.database import SessionLocal, Channel, Keyword, create_tables

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv('config.env')

class SimpleTelegramBotManager:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.authorized_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        
        # 테이블 생성 확인
        create_tables()
        
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
            await self.show_analyze_menu(update, context)
        elif query.data == "stats":
            await self.show_stats(update, context)
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
            [InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"📺 **현재 구독 채널 ({len(channels)}개)**\n\n{channel_list}"
        
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
            [InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"🔍 **현재 키워드 ({len(keywords)}개)**\n\n{keyword_list}"
        
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
    
    async def show_analyze_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """분석 메뉴 표시"""
        text = (
            "📊 **분석 실행**\n\n"
            "정기 분석을 실행합니다.\n"
            "구독된 채널의 최신 영상들을 분석하여 인사이트를 제공합니다.\n\n"
            "이 기능은 현재 개발 중입니다. 🚧"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """통계 보기"""
        db = SessionLocal()
        channel_count = db.query(Channel).count()
        keyword_count = db.query(Keyword).count()
        db.close()
        
        text = (
            "📈 **시스템 통계**\n\n"
            f"• 구독 채널: {channel_count}개\n"
            f"• 등록 키워드: {keyword_count}개\n\n"
            "더 상세한 통계는 추후 추가될 예정입니다."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 메인 메뉴", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """메시지 처리"""
        if not self.is_authorized(update):
            await update.message.reply_text("❌ 인증되지 않은 사용자입니다.")
            return
        
        text = update.message.text
        
        # YouTube URL 패턴 확인
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)'
        ]
        
        is_youtube_url = False
        for pattern in youtube_patterns:
            if re.search(pattern, text):
                is_youtube_url = True
                break
        
        if is_youtube_url:
            await update.message.reply_text(
                "🎬 YouTube URL을 감지했습니다!\n\n"
                "현재 URL 분석 기능은 개발 중입니다. 🚧\n"
                "곧 자동으로 영상을 요약해드릴 예정입니다!"
            )
        else:
            # 기본 응답
            await update.message.reply_text(
                "💡 **사용법:**\n\n"
                "• `/start` - 메인 메뉴로 이동\n"
                "• YouTube URL 전송 - 영상 요약 (개발 중)\n"
                "• 텍스트 메시지 - 키워드 검색 (개발 중)"
            )
    
    def run(self):
        """봇 실행"""
        application = Application.builder().token(self.token).build()
        
        # 핸들러 등록
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        logger.info("🤖 간단한 텔레그램 봇 관리자 시작!")
        application.run_polling()

if __name__ == "__main__":
    bot = SimpleTelegramBotManager()
    bot.run() 