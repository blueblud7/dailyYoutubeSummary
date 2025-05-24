#!/usr/bin/env python3
"""
구독 채널의 최신 업데이트를 수집하고 리포트를 생성하는 테스트 스크립트
"""

import logging
from datetime import datetime, timedelta
from app.models.database import SessionLocal, Channel, Video, Analysis
from app.services.data_collector import DataCollector
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def collect_subscription_updates():
    """구독 채널들의 최신 업데이트를 수집합니다."""
    logger.info("=== 구독 채널 업데이트 수집 시작 ===")
    
    db = SessionLocal()
    data_collector = DataCollector()
    
    try:
        # DB에서 구독 채널 목록 가져오기
        channels = db.query(Channel).all()
        logger.info(f"총 {len(channels)}개 구독 채널 발견")
        
        # 각 채널별로 최근 3일간의 새 영상 수집
        total_new_videos = 0
        
        for channel in channels:
            logger.info(f"📺 {channel.channel_name} 채널 업데이트 확인 중...")
            
            try:
                # 최근 3일간의 비디오 수집
                videos = data_collector.collect_channel_videos(
                    channel.channel_id, 
                    days_back=3, 
                    db=db
                )
                
                if videos:
                    logger.info(f"   ✅ {len(videos)}개 새 영상 발견")
                    total_new_videos += len(videos)
                    
                    # 수집된 비디오들 자막 및 분석 진행
                    for video in videos:
                        try:
                            # 자막 수집
                            data_collector.collect_video_transcript(video.video_id, db)
                            logger.info(f"   📝 자막 수집: {video.title[:50]}...")
                        except Exception as e:
                            logger.warning(f"   ⚠️ 자막 수집 실패: {e}")
                            
                    # 키워드별 분석 수행
                    default_keywords = [
                        "투자", "주식", "부동산", "경제", "금리", "인플레이션",
                        "달러", "환율", "코스피", "나스닥", "반도체", "AI"
                    ]
                    
                    analyses = data_collector.analyze_videos(videos, default_keywords, db)
                    logger.info(f"   🔍 {len(analyses)}개 분석 완료")
                    
                else:
                    logger.info(f"   ℹ️ 새 영상 없음")
                    
            except Exception as e:
                logger.error(f"   ❌ {channel.channel_name} 채널 처리 중 오류: {e}")
                continue
        
        logger.info(f"=== 수집 완료: 총 {total_new_videos}개 새 영상 ===")
        return total_new_videos
        
    except Exception as e:
        logger.error(f"구독 채널 업데이트 수집 중 오류: {e}")
        return 0
    finally:
        db.close()

def generate_subscription_report():
    """구독 채널 업데이트 리포트를 생성합니다."""
    logger.info("=== 구독 채널 업데이트 리포트 생성 시작 ===")
    
    db = SessionLocal()
    report_service = ReportService()
    
    try:
        # 최근 1일간의 데이터로 일일 리포트 생성
        report = report_service.generate_daily_report(
            db=db,
            keywords=[
                "투자", "주식", "부동산", "경제", "금리", "인플레이션",
                "달러", "환율", "코스피", "나스닥", "반도체", "AI"
            ]
        )
        
        if report and not report.get('error'):
            logger.info("✅ 일일 리포트 생성 완료")
            
            # 리포트 내용 출력
            print("\n" + "="*60)
            print("📊 구독 채널 업데이트 리포트")
            print("="*60)
            print(f"📅 기간: {report.get('period', '오늘')}")
            print(f"📈 전체 트렌드: {report.get('market_trend', {}).get('overall_trend', 'N/A')}")
            print(f"💭 시장 심리: {report.get('market_sentiment', 'N/A')}")
            print(f"📊 분석된 영상 수: {report.get('total_analyses', 0)}개")
            
            # 주요 인사이트
            if 'key_insights' in report:
                print(f"\n🔍 주요 인사이트:")
                for i, insight in enumerate(report['key_insights'][:5], 1):
                    print(f"   {i}. {insight}")
            
            # 채널별 업데이트
            if 'channel_summary' in report:
                print(f"\n📺 채널별 업데이트:")
                for channel, summary in report['channel_summary'].items():
                    print(f"   • {channel}: {summary.get('total_videos', 0)}개 영상")
            
            print("="*60)
            
            return report
        else:
            logger.error("❌ 리포트 생성 실패")
            return None
            
    except Exception as e:
        logger.error(f"리포트 생성 중 오류: {e}")
        return None
    finally:
        db.close()

def send_subscription_notification(report):
    """구독 채널 업데이트 알림을 발송합니다."""
    logger.info("=== 구독 채널 업데이트 알림 발송 시작 ===")
    
    notification_service = NotificationService()
    
    try:
        # 일일 리포트 알림 발송
        results = notification_service.send_daily_report_notifications(report)
        logger.info(f"✅ 알림 발송 완료: {results}")
        return results
        
    except Exception as e:
        logger.error(f"알림 발송 중 오류: {e}")
        return None

def run_subscription_update_cycle():
    """구독 채널 업데이트 전체 사이클을 실행합니다."""
    logger.info("🚀 구독 채널 업데이트 사이클 시작")
    
    start_time = datetime.now()
    
    # 1. 구독 채널 업데이트 수집
    new_videos = collect_subscription_updates()
    
    # 2. 리포트 생성
    report = generate_subscription_report()
    
    # 3. 알림 발송
    if report:
        notification_results = send_subscription_notification(report)
    else:
        notification_results = None
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 결과 요약
    print(f"\n🎉 구독 채널 업데이트 사이클 완료")
    print(f"⏱️ 소요 시간: {duration:.1f}초")
    print(f"📹 새 영상: {new_videos}개")
    print(f"📊 리포트 생성: {'성공' if report else '실패'}")
    print(f"📧 알림 발송: {'성공' if notification_results else '실패'}")
    
    return {
        "duration": duration,
        "new_videos": new_videos,
        "report_generated": bool(report),
        "notifications_sent": bool(notification_results)
    }

if __name__ == "__main__":
    # 구독 채널 업데이트 사이클 실행
    result = run_subscription_update_cycle()
    
    if result['report_generated']:
        print("\n✅ 구독 채널 업데이트 리포트가 성공적으로 생성되었습니다!")
        if result['notifications_sent']:
            print("📧 알림도 성공적으로 발송되었습니다!")
    else:
        print("\n❌ 리포트 생성에 실패했습니다.") 