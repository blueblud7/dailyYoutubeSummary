#!/usr/bin/env python3
"""
리포트 생성 과정 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal
from app.services.report_service import ReportService
from datetime import datetime, timedelta

def debug_data_availability():
    """데이터 가용성 확인"""
    print("🔍 데이터 가용성 확인...")
    
    db = SessionLocal()
    try:
        from app.models.database import Video, Analysis, Channel, Keyword
        
        # 비디오 수 확인
        total_videos = db.query(Video).count()
        print(f"📹 총 비디오 수: {total_videos}")
        
        # 최근 24시간 비디오
        yesterday = datetime.now() - timedelta(days=1)
        recent_videos = db.query(Video).filter(Video.published_at >= yesterday).count()
        print(f"📹 최근 24시간 비디오 수: {recent_videos}")
        
        # 분석 수 확인
        total_analyses = db.query(Analysis).count()
        print(f"📊 총 분석 수: {total_analyses}")
        
        # 최근 24시간 분석
        recent_analyses = db.query(Analysis).join(Video).filter(Video.published_at >= yesterday).count()
        print(f"📊 최근 24시간 분석 수: {recent_analyses}")
        
        # 채널 수 확인
        total_channels = db.query(Channel).count()
        print(f"📺 총 채널 수: {total_channels}")
        
        # 키워드 수 확인
        total_keywords = db.query(Keyword).count()
        print(f"🔑 총 키워드 수: {total_keywords}")
        
        # 최근 7일 데이터
        week_ago = datetime.now() - timedelta(days=7)
        weekly_videos = db.query(Video).filter(Video.published_at >= week_ago).count()
        weekly_analyses = db.query(Analysis).join(Video).filter(Video.published_at >= week_ago).count()
        print(f"📹 최근 7일 비디오 수: {weekly_videos}")
        print(f"📊 최근 7일 분석 수: {weekly_analyses}")
        
        return {
            'total_videos': total_videos,
            'recent_videos': recent_videos,
            'total_analyses': total_analyses,
            'recent_analyses': recent_analyses,
            'weekly_videos': weekly_videos,
            'weekly_analyses': weekly_analyses
        }
        
    except Exception as e:
        print(f"❌ 데이터 확인 실패: {e}")
        return None
    finally:
        db.close()

def debug_report_generation():
    """리포트 생성 과정 디버깅"""
    print("\n🔍 리포트 생성 과정 디버깅...")
    
    db = SessionLocal()
    try:
        report_service = ReportService()
        
        # 기간 설정
        today = datetime.now().date()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        print(f"📅 분석 기간: {start_date} ~ {end_date}")
        
        # 1. 기간별 분석 가져오기
        analyses = report_service.get_period_analyses(db, start_date, end_date)
        print(f"📊 해당 기간 분석 수: {len(analyses)}")
        
        if analyses:
            print(f"📝 첫 번째 분석 샘플:")
            first_analysis = analyses[0]
            print(f"  • 제목: {first_analysis.get('video_title', 'N/A')}")
            print(f"  • 채널: {first_analysis.get('channel_name', 'N/A')}")
            print(f"  • 감정: {first_analysis.get('sentiment_score', 0)}")
            print(f"  • 요약: {first_analysis.get('summary', 'N/A')[:100]}...")
        
        # 2. 상위 비디오 가져오기
        top_videos = report_service.get_top_videos(db, start_date, end_date, limit=10)
        print(f"🎯 상위 비디오 수: {len(top_videos)}")
        
        # 3. 주간 데이터도 확인
        week_start = datetime.now() - timedelta(days=7)
        week_end = datetime.now()
        weekly_analyses = report_service.get_period_analyses(db, week_start, week_end)
        print(f"📊 주간 분석 수: {len(weekly_analyses)}")
        
        return {
            'daily_analyses': len(analyses),
            'top_videos': len(top_videos),
            'weekly_analyses': len(weekly_analyses),
            'sample_analysis': analyses[0] if analyses else None
        }
        
    except Exception as e:
        print(f"❌ 리포트 생성 과정 디버깅 실패: {e}")
        return None
    finally:
        db.close()

def test_simple_trend_analysis():
    """간단한 트렌드 분석 테스트"""
    print("\n🔍 간단한 트렌드 분석 테스트...")
    
    try:
        from app.services.analysis_service import AnalysisService
        analysis_service = AnalysisService()
        
        # 가짜 분석 데이터로 테스트
        fake_analyses = [
            {
                'summary': '주식 시장이 상승세를 보이고 있습니다.',
                'sentiment_score': 0.3,
                'importance_score': 0.8,
                'key_insights': ['주식 상승', '긍정적 전망'],
                'mentioned_entities': ['삼성전자', 'SK하이닉스'],
                'video_title': '테스트 비디오 1',
                'channel_name': '테스트 채널'
            },
            {
                'summary': '부동산 시장 동향을 분석해봅니다.',
                'sentiment_score': 0.1,
                'importance_score': 0.6,
                'key_insights': ['부동산 안정', '정책 변화'],
                'mentioned_entities': ['아파트', '정부 정책'],
                'video_title': '테스트 비디오 2',
                'channel_name': '테스트 채널'
            }
        ]
        
        print(f"📊 가짜 분석 데이터 수: {len(fake_analyses)}")
        
        # 트렌드 분석 시도
        trend_result = analysis_service.generate_trend_analysis(
            fake_analyses, ["주식", "부동산"], "테스트 기간"
        )
        
        print(f"✅ 트렌드 분석 성공!")
        print(f"📈 전체 트렌드: {trend_result.get('overall_trend', 'N/A')[:100]}...")
        print(f"💭 시장 감정: {trend_result.get('market_sentiment', 'N/A')}")
        print(f"🎯 주요 테마: {trend_result.get('key_themes', [])}")
        print(f"📝 요약: {trend_result.get('summary', 'N/A')[:100]}...")
        
        return trend_result
        
    except Exception as e:
        print(f"❌ 트렌드 분석 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_daily_report_generation():
    """일일 리포트 생성 테스트"""
    print("\n🔍 일일 리포트 생성 테스트...")
    
    try:
        from app.services.analysis_service import AnalysisService
        analysis_service = AnalysisService()
        
        # 가짜 트렌드 분석 데이터
        fake_trend = {
            'overall_trend': '테스트 트렌드',
            'key_themes': ['AI', '반도체', '투자'],
            'market_sentiment': 'bullish',
            'summary': '테스트 요약입니다.',
            'hot_topics': ['ChatGPT', '삼성전자'],
            'risk_factors': ['금리 변동'],
            'opportunities': ['성장주 투자']
        }
        
        # 가짜 상위 비디오 데이터
        fake_videos = [
            {'title': '테스트 비디오 1', 'view_count': 10000},
            {'title': '테스트 비디오 2', 'view_count': 8000}
        ]
        
        # 일일 리포트 생성 시도
        daily_result = analysis_service.generate_daily_report(
            fake_trend, fake_videos, datetime.now()
        )
        
        print(f"✅ 일일 리포트 생성 성공!")
        print(f"📋 제목: {daily_result.get('title', 'N/A')}")
        print(f"💡 요약: {daily_result.get('executive_summary', 'N/A')[:100]}...")
        print(f"🔮 내일 전망: {daily_result.get('tomorrow_outlook', 'N/A')[:100]}...")
        
        return daily_result
        
    except Exception as e:
        print(f"❌ 일일 리포트 생성 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 리포트 생성 디버깅 시작\n")
    
    # 1. 데이터 가용성 확인
    data_info = debug_data_availability()
    
    # 2. 리포트 생성 과정 디버깅
    report_info = debug_report_generation()
    
    # 3. 간단한 트렌드 분석 테스트
    trend_result = test_simple_trend_analysis()
    
    # 4. 일일 리포트 생성 테스트
    daily_result = test_daily_report_generation()
    
    print("\n🎉 디버깅 완료!")
    
    # 결과 요약
    print("\n📋 디버깅 결과 요약:")
    if data_info:
        print(f"• 데이터: 비디오 {data_info['total_videos']}개, 분석 {data_info['total_analyses']}개")
        print(f"• 최근: 일일 분석 {data_info['recent_analyses']}개, 주간 분석 {data_info['weekly_analyses']}개")
    print(f"• 트렌드 분석: {'✅ 성공' if trend_result else '❌ 실패'}")
    print(f"• 일일 리포트: {'✅ 성공' if daily_result else '❌ 실패'}") 