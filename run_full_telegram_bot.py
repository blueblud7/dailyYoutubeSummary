#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.telegram_bot_service import TelegramBotService
from dotenv import load_dotenv

def main():
    """전체 기능이 포함된 텔레그램 봇을 실행합니다."""
    
    # 환경 변수 로드
    load_dotenv('config.env')
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('full_telegram_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # 텔레그램 봇 토큰 확인
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN이 config.env에 설정되지 않았습니다.")
        return
    
    logger.info("🤖 전체 기능 투자 분석 텔레그램 봇 시작!")
    logger.info("="*60)
    logger.info("📋 분석 명령어:")
    logger.info("• /start - 봇 시작 및 환영 메시지")
    logger.info("• /help - 상세 사용법 안내")
    logger.info("• /search [키워드] - 🔥 실시간 YouTube 검색")
    logger.info("• /keyword [키워드] - 키워드 분석")
    logger.info("• /channel [채널명] - 채널 분석")
    logger.info("• /influencer [인물명] - 인물 언급 분석")
    logger.info("• /daily - 오늘의 일일 리포트")
    logger.info("• /weekly - 주간 종합 리포트")
    logger.info("• /hot - 핫한 키워드 TOP 10")
    logger.info("• /trend - 최근 3일 트렌드 분석")
    logger.info("• /multi - 다차원 분석")
    logger.info("")
    logger.info("🎛️ 관리 명령어:")
    logger.info("• /list_keywords - 등록된 키워드 목록")
    logger.info("• /list_channels - 등록된 채널 목록")
    logger.info("• /add_keyword [키워드] [카테고리] - 키워드 추가")
    logger.info("• /add_channel [채널명/URL] - 채널 추가")
    logger.info("• /remove_keyword [ID] - 키워드 제거")
    logger.info("• /remove_channel [ID] - 채널 제거")
    logger.info("")
    logger.info("🎬 기타:")
    logger.info("• YouTube URL 전송 - 자동 영상 요약")
    logger.info("="*60)
    logger.info("🔥 주요 기능:")
    logger.info("  1️⃣ 실시간 YouTube 키워드 검색")
    logger.info("  2️⃣ YouTube URL 자동 감지 및 AI 요약")
    logger.info("  3️⃣ 키워드/채널 관리 시스템")
    logger.info("  4️⃣ 봇 시작/업데이트 자동 알림")
    logger.info("="*60)
    logger.info("봇을 중지하려면 Ctrl+C를 누르세요.")
    
    try:
        # 전체 기능 봇 실행
        bot_service = TelegramBotService()
        bot_service.run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 봇이 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 봇 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 