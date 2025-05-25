#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.telegram_bot_service import telegram_bot
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
    
    logger.info("🤖 투자 인사이트 텔레그램 봇 시작!")
    logger.info("="*50)
    logger.info("📱 사용 가능한 명령어:")
    logger.info("• /start - 봇 시작")
    logger.info("• /help - 사용법 안내")
    logger.info("• /keyword [키워드] - 키워드 분석")
    logger.info("• /channel [채널명] - 채널 분석")
    logger.info("• /influencer [인물명] - 인플루언서 언급 분석")
    logger.info("• /daily - 일일 리포트")
    logger.info("• /weekly - 주간 리포트")
    logger.info("• /hot - 핫한 키워드")
    logger.info("• /trend - 트렌드 분석")
    logger.info("• /multi [키워드] [채널] [인물] - 다차원 분석")
    logger.info("="*50)
    logger.info("봇을 중지하려면 Ctrl+C를 누르세요.")
    
    try:
        # 봇 실행
        telegram_bot.run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 봇이 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 봇 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 