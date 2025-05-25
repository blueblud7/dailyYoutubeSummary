#!/usr/bin/env python3
"""
투자 인사이트 분석 시스템 테스트 스크립트

이 스크립트는 시스템의 주요 기능들을 테스트합니다.
API 키가 설정되어 있어야 정상적으로 동작합니다.
"""

import os
import sys
import logging
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, create_tables
from app.services.data_collector import DataCollector
from app.services.report_service import ReportService
from app.services.scheduler import scheduler

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_setup():
    """데이터베이스 설정 테스트"""
    logger.info("=== 데이터베이스 설정 테스트 ===")
    try:
        create_tables()
        logger.info("✅ 데이터베이스 테이블 생성 성공")
        
        # 데이터베이스 연결 테스트
        db = SessionLocal()
        db.close()
        logger.info("✅ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 설정 실패: {e}")
        return False

def test_youtube_api():
    """YouTube API 연결 테스트"""
    logger.info("=== YouTube API 테스트 ===")
    try:
        from app.services.youtube_service import YouTubeService
        
        youtube_service = YouTubeService()
        
        # 테스트용 채널 정보 조회
        test_channel_id = "UC7RQon_YwCnp_LbPtEwW65w"  # 슈카월드
        channel_info = youtube_service.get_channel_details(test_channel_id)
        
        if channel_info:
            logger.info(f"✅ YouTube API 연결 성공")
            logger.info(f"   채널명: {channel_info['channel_name']}")
            logger.info(f"   구독자 수: {channel_info['subscriber_count']:,}")
            return True
        else:
            logger.error("❌ 채널 정보를 가져올 수 없습니다")
            return False
            
    except Exception as e:
        logger.error(f"❌ YouTube API 테스트 실패: {e}")
        return False

def test_openai_api():
    """OpenAI API 연결 테스트"""
    logger.info("=== OpenAI API 테스트 ===")
    try:
        from app.services.analysis_service import AnalysisService
        
        analysis_service = AnalysisService()
        
        # 간단한 테스트 분석
        test_transcript = "오늘 주식시장이 상승했습니다. 삼성전자가 3% 올랐고, 투자자들의 심리가 긍정적입니다."
        result = analysis_service.analyze_transcript(
            test_transcript, 
            "테스트 비디오", 
            "테스트 채널",
            ["주식", "투자"]
        )
        
        if result and result.get('summary'):
            logger.info("✅ OpenAI API 연결 성공")
            logger.info(f"   분석 결과: {result['summary'][:50]}...")
            return True
        else:
            logger.error("❌ 분석 결과를 받을 수 없습니다")
            return False
            
    except Exception as e:
        logger.error(f"❌ OpenAI API 테스트 실패: {e}")
        return False

def test_data_collection():
    """데이터 수집 기능 테스트"""
    logger.info("=== 데이터 수집 테스트 ===")
    try:
        db = SessionLocal()
        data_collector = DataCollector()
        
        # 테스트용 채널 추가
        test_channel_id = "UC7RQon_YwCnp_LbPtEwW65w"
        channel = data_collector.add_channel(test_channel_id, db)
        
        if channel:
            logger.info(f"✅ 채널 추가 성공: {channel.channel_name}")
            
            # 키워드 추가
            keywords = data_collector.add_keywords(["테스트", "투자"], "테스트", db)
            logger.info(f"✅ 키워드 추가 성공: {len(keywords)}개")
            
            db.close()
            return True
        else:
            logger.error("❌ 채널 추가 실패")
            db.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ 데이터 수집 테스트 실패: {e}")
        return False

def test_report_generation():
    """리포트 생성 테스트"""
    logger.info("=== 리포트 생성 테스트 ===")
    try:
        db = SessionLocal()
        report_service = ReportService()
        
        # 간단한 테스트 데이터로 트렌드 분석
        test_analyses = [
            {
                'summary': '테스트 요약 1',
                'sentiment_score': 0.5,
                'key_insights': ['인사이트 1', '인사이트 2'],
                'mentioned_entities': ['삼성전자', '투자']
            },
            {
                'summary': '테스트 요약 2', 
                'sentiment_score': -0.2,
                'key_insights': ['인사이트 3', '인사이트 4'],
                'mentioned_entities': ['SK하이닉스', '경제']
            }
        ]
        
        from app.services.analysis_service import AnalysisService
        analysis_service = AnalysisService()
        
        trend_result = analysis_service.generate_trend_analysis(
            test_analyses, ['투자', '주식'], '테스트'
        )
        
        if trend_result and trend_result.get('overall_trend'):
            logger.info("✅ 트렌드 분석 성공")
            logger.info(f"   전체 트렌드: {trend_result['overall_trend'][:50]}...")
            db.close()
            return True
        else:
            logger.error("❌ 트렌드 분석 실패")
            db.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ 리포트 생성 테스트 실패: {e}")
        return False

def test_full_workflow():
    """전체 워크플로우 테스트 (실제 데이터 수집 포함)"""
    logger.info("=== 전체 워크플로우 테스트 ===")
    logger.warning("⚠️  이 테스트는 실제 API를 호출하여 데이터를 수집합니다.")
    
    response = input("계속 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        logger.info("테스트를 건너뜁니다.")
        return True
    
    try:
        # 수동 데이터 수집 실행
        result = scheduler.run_manual_collection(
            channels=["UC7RQon_YwCnp_LbPtEwW65w"],
            keywords=["투자", "주식"]
        )
        
        if result and not result.get('error'):
            logger.info("✅ 데이터 수집 성공")
            logger.info(f"   수집된 비디오: {result.get('total_videos_collected', 0)}개")
            
            # 리포트 생성 테스트
            report_result = scheduler.run_manual_report("daily", ["투자", "주식"])
            
            if report_result and not report_result.get('error'):
                logger.info("✅ 리포트 생성 성공")
                return True
            else:
                logger.error("❌ 리포트 생성 실패")
                return False
        else:
            logger.error(f"❌ 데이터 수집 실패: {result.get('error', '알 수 없는 오류')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 전체 워크플로우 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("🚀 투자 인사이트 분석 시스템 테스트 시작")
    logger.info(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("데이터베이스 설정", test_database_setup),
        ("YouTube API", test_youtube_api),
        ("OpenAI API", test_openai_api),
        ("데이터 수집", test_data_collection),
        ("리포트 생성", test_report_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} 테스트 ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 테스트 통과")
            else:
                logger.error(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            logger.error(f"❌ {test_name} 테스트 중 예외 발생: {e}")
    
    # 전체 워크플로우 테스트 (옵션)
    logger.info("\n--- 전체 워크플로우 테스트 (옵션) ---")
    if test_full_workflow():
        passed += 1
        total += 1
    else:
        total += 1
    
    # 결과 출력
    logger.info("\n" + "="*50)
    logger.info(f"🎯 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        logger.info("💡 이제 다음 명령으로 시스템을 실행할 수 있습니다:")
        logger.info("   python main.py")
    else:
        logger.warning("⚠️  일부 테스트가 실패했습니다. 설정을 확인해주세요.")
        logger.info("📋 확인사항:")
        logger.info("   1. config.env 파일의 API 키 설정")
        logger.info("   2. 네트워크 연결 상태")
        logger.info("   3. 필요한 패키지 설치 여부")
    
    logger.info(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 