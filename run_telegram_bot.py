#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from simple_telegram_bot_manager import SimpleTelegramBotManager
from dotenv import load_dotenv

def main():
    """텔레그램 봇을 실행합니다."""
    
    # 환경 변수 로드
    load_dotenv('config.env')
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('telegram_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # 텔레그램 봇 토큰 확인
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN이 config.env에 설정되지 않았습니다.")
        logger.info("📋 텔레그램 봇 설정 방법:")
        logger.info("1. @BotFather에게 /newbot 명령으로 새 봇 생성")
        logger.info("2. 받은 토큰을 config.env에 TELEGRAM_BOT_TOKEN으로 설정")
        logger.info("3. 봇과 대화를 시작하고 /start 명령 실행")
        return
    
    logger.info("🤖 투자 분석 텔레그램 봇 (버튼 포함) 시작!")
    logger.info("="*50)
    logger.info("📱 사용 가능한 기능:")
    logger.info("• /start - 봇 시작 (인라인 버튼 메뉴)")
    logger.info("• 📺 채널 구독 관리")
    logger.info("• 🔍 키워드 관리")
    logger.info("• 🔎 키워드 검색 (등록 안 된 것도 검색 가능)")
    logger.info("• 📊 정기 분석 실행")
    logger.info("• 🎬 YouTube URL 즉시 요약")
    logger.info("="*50)
    logger.info("봇을 중지하려면 Ctrl+C를 누르세요.")
    
    try:
        # 간단한 봇 관리자 실행
        bot_manager = SimpleTelegramBotManager()
        bot_manager.run()
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 봇이 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 봇 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 