#!/usr/bin/env python3

from app.services.data_collector import DataCollector
from app.services.report_service import ReportService
from app.services.analysis_service import AnalysisService
from app.models.database import SessionLocal
from datetime import datetime, timedelta
import json

def analyze_kimjungsong_weekly():
    """김준송TV의 지난 1주일 콘텐츠를 분석합니다."""
    
    # 김준송TV 채널 ID
    kimjungsong_channel_id = "UC18feVzOBjtLU9trm8A788g"
    
    print("🎬 김준송TV 지난 1주일 분석 시작")
    print("="*50)
    
    db = SessionLocal()
    data_collector = DataCollector()
    analysis_service = AnalysisService()
    
    try:
        # 1. 최근 1주일 비디오 수집
        print("📺 최근 1주일 비디오 수집 중...")
        videos = data_collector.collect_channel_videos(
            channel_id=kimjungsong_channel_id,
            days_back=7,
            db=db
        )
        
        print(f"✅ 수집된 비디오: {len(videos)}개")
        
        if not videos:
            print("❌ 최근 1주일간 새로운 비디오가 없습니다.")
            return
        
        # 비디오 목록 출력
        print("\n📋 수집된 비디오 목록:")
        for i, video in enumerate(videos, 1):
            print(f"{i}. {video.title}")
            print(f"   📅 {video.published_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   👀 조회수: {video.view_count:,}")
            print(f"   🔗 {video.video_url}")
            print()
        
        # 2. 자막 수집
        print("📝 자막 수집 중...")
        transcripts = data_collector.collect_video_transcripts(videos, db)
        
        print(f"✅ 자막 수집 완료: {len(transcripts)}개")
        
        # 3. AI 분석 수행
        print("\n🤖 AI 분석 수행 중...")
        keywords = ["투자", "주식", "경제", "시장", "전망"]
        analyses = data_collector.analyze_videos(videos, keywords, db)
        
        print(f"✅ 분석 완료: {len(analyses)}개")
        
        # 4. 분석 결과 수집
        analysis_results = []
        for video in videos:
            from app.models.database import Analysis, Transcript
            
            # 해당 비디오의 분석 결과 가져오기
            analysis = db.query(Analysis).filter(Analysis.video_id == video.video_id).first()
            transcript = db.query(Transcript).filter(Transcript.video_id == video.video_id).first()
            
            if analysis:
                analysis_dict = {
                    'video_title': video.title,
                    'published_at': video.published_at,
                    'view_count': video.view_count,
                    'video_url': video.video_url,
                    'summary': analysis.summary,
                    'sentiment_score': analysis.sentiment_score,
                    'importance_score': analysis.importance_score,
                    'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                    'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else [],
                    'has_transcript': transcript is not None
                }
                analysis_results.append(analysis_dict)
        
        # 5. 전반적인 트렌드 분석
        print("\n📊 전반적인 트렌드 분석 중...")
        trend_analysis = analysis_service.generate_trend_analysis(
            analysis_results, 
            keywords, 
            "김준송TV 최근 1주일"
        )
        
        # 6. 결과 출력
        print("\n" + "="*60)
        print("📈 김준송TV 지난 1주일 투자 인사이트 분석")
        print("="*60)
        
        print(f"\n🎯 분석 개요")
        print(f"- 분석 기간: {datetime.now() - timedelta(days=7):%Y-%m-%d} ~ {datetime.now():%Y-%m-%d}")
        print(f"- 총 비디오 수: {len(videos)}개")
        print(f"- 분석 완료: {len(analysis_results)}개")
        print(f"- 평균 감정 점수: {sum([r['sentiment_score'] for r in analysis_results])/len(analysis_results):.2f}")
        
        print(f"\n📺 주요 비디오들:")
        # 중요도와 조회수 기준으로 정렬
        sorted_videos = sorted(analysis_results, 
                             key=lambda x: (x['importance_score'], x['view_count']), 
                             reverse=True)
        
        for i, video in enumerate(sorted_videos[:3], 1):
            print(f"\n{i}. {video['video_title']}")
            print(f"   📅 {video['published_at'].strftime('%m-%d %H:%M')}")
            print(f"   📈 중요도: {video['importance_score']:.2f}")
            print(f"   😊 감정: {video['sentiment_score']:.2f}")
            print(f"   📝 요약: {video['summary']}")
            print(f"   💡 주요 인사이트: {', '.join(video['key_insights'][:2])}")
            print(f"   🔗 {video['video_url']}")
        
        print(f"\n🔍 전반적인 트렌드:")
        print(f"- 시장 전망: {trend_analysis['overall_trend']}")
        print(f"- 시장 감정: {trend_analysis['market_sentiment']}")
        print(f"- 주요 테마: {', '.join(trend_analysis['key_themes'])}")
        print(f"- 핫 토픽: {', '.join(trend_analysis['hot_topics'])}")
        
        print(f"\n💼 투자 관점:")
        print(f"- 전문가 합의: {trend_analysis['consensus_view']}")
        print(f"- 위험 요소: {', '.join(trend_analysis['risk_factors'])}")
        print(f"- 투자 기회: {', '.join(trend_analysis['opportunities'])}")
        
        print(f"\n📋 요약:")
        print(trend_analysis['summary'])
        
        return {
            'videos': analysis_results,
            'trend_analysis': trend_analysis,
            'stats': {
                'total_videos': len(videos),
                'analyzed_videos': len(analysis_results),
                'avg_sentiment': sum([r['sentiment_score'] for r in analysis_results])/len(analysis_results) if analysis_results else 0
            }
        }
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    analyze_kimjungsong_weekly() 