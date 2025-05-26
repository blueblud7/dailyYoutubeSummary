#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_telegram_bot import UnifiedTelegramBot
from dotenv import load_dotenv

def main():
    """통합 텔레그램 봇을 실행합니다."""
    
    # 환경 변수 로드
    load_dotenv('config.env')
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('unified_telegram_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # 필수 환경 변수 확인
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN이 config.env에 설정되지 않았습니다.")
        return
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY가 config.env에 설정되지 않았습니다.")
        return
    
    youtube_keys = os.getenv("YOUTUBE_API_KEYS")
    if not youtube_keys:
        logger.error("❌ YOUTUBE_API_KEYS가 config.env에 설정되지 않았습니다.")
        return
    
    logger.info("🤖 통합 투자 분석 텔레그램 봇 시작!")
    logger.info("="*60)
    logger.info("📱 모든 기능이 하나로 통합되었습니다!")
    logger.info("")
    logger.info("🎬 YouTube URL 요약 - URL만 보내면 AI가 자동 분석")
    logger.info("📺 채널 관리 - 채널 추가/삭제 완전 지원")
    logger.info("🔍 키워드 관리 - 키워드 추가/삭제 완전 지원")
    logger.info("🔎 실시간 키워드 검색 - 등록 안 된 키워드도 검색")
    logger.info("📊 정기 분석 - 구독된 채널 자동 분석")
    logger.info("📈 통계 및 트렌드 - 상세한 시스템 현황")
    logger.info("")
    logger.info("✨ 사용법: /start 명령으로 시작하거나 YouTube URL 바로 전송")
    logger.info("="*60)
    logger.info("봇을 중지하려면 Ctrl+C를 누르세요.")
    
    try:
        # 통합 봇 실행
        bot = UnifiedTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 봇이 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 봇 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 