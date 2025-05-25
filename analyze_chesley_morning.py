#!/usr/bin/env python3

from app.services.data_collector import DataCollector
from app.services.report_service import ReportService
from app.services.analysis_service import AnalysisService
from app.models.database import SessionLocal
from datetime import datetime, timedelta
import json

def analyze_chesley_morning_brief():
    """체슬리TV의 지난 1주일 모닝브리프를 분석합니다."""
    
    # 체슬리TV 채널 ID
    chesley_channel_id = "UCXST0Hq6CAmG0dmo3jgrlEw"
    
    print("🌅 체슬리TV 모닝브리프 1주일 분석 시작")
    print("="*50)
    
    db = SessionLocal()
    data_collector = DataCollector()
    analysis_service = AnalysisService()
    
    try:
        # 1. 최근 1주일 비디오 수집
        print("📺 최근 1주일 비디오 수집 중...")
        videos = data_collector.collect_channel_videos(
            channel_id=chesley_channel_id,
            days_back=7,
            db=db
        )
        
        print(f"✅ 수집된 전체 비디오: {len(videos)}개")
        
        # 모닝브리프 비디오만 필터링
        morning_brief_videos = []
        for video in videos:
            title_lower = video.title.lower()
            if any(keyword in title_lower for keyword in ['모닝브리프', 'morning brief', '모닝', 'morning']):
                morning_brief_videos.append(video)
        
        print(f"🌅 모닝브리프 비디오: {len(morning_brief_videos)}개")
        
        if not morning_brief_videos:
            print("❌ 최근 1주일간 모닝브리프 비디오가 없습니다.")
            # 전체 비디오 중 최신 몇 개라도 보여주기
            if videos:
                print("📺 대신 최신 비디오들을 분석하겠습니다:")
                morning_brief_videos = videos[:5]  # 최신 5개
            else:
                return
        
        # 비디오 목록 출력
        print("\n📋 분석 대상 비디오 목록:")
        for i, video in enumerate(morning_brief_videos, 1):
            print(f"{i}. {video.title}")
            print(f"   📅 {video.published_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   👀 조회수: {video.view_count:,}")
            print(f"   🔗 {video.video_url}")
            print()
        
        # 2. 자막 수집
        print("📝 자막 수집 중...")
        transcripts = data_collector.collect_video_transcripts(morning_brief_videos, db)
        
        print(f"✅ 자막 수집 완료: {len(transcripts)}개")
        
        # 3. AI 분석 수행
        print("\n🤖 AI 분석 수행 중...")
        keywords = ["투자", "주식", "경제", "시장", "전망", "모닝브리프", "브리핑"]
        analyses = data_collector.analyze_videos(morning_brief_videos, keywords, db)
        
        print(f"✅ 분석 완료: {len(analyses)}개")
        
        # 4. 분석 결과 수집
        analysis_results = []
        for video in morning_brief_videos:
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
        
        # 5. 결과 출력
        print("\n" + "="*60)
        print("🌅 체슬리TV 모닝브리프 1주일 핵심 요약")
        print("="*60)
        
        print(f"\n🎯 분석 개요")
        print(f"- 분석 기간: {datetime.now() - timedelta(days=7):%Y-%m-%d} ~ {datetime.now():%Y-%m-%d}")
        print(f"- 모닝브리프 개수: {len(morning_brief_videos)}개")
        print(f"- 분석 완료: {len(analysis_results)}개")
        if analysis_results:
            print(f"- 평균 감정 점수: {sum([r['sentiment_score'] for r in analysis_results])/len(analysis_results):.2f}")
        
        # 날짜순으로 정렬 (최신순)
        sorted_videos = sorted(analysis_results, 
                             key=lambda x: x['published_at'], 
                             reverse=True)
        
        print(f"\n📈 일별 모닝브리프 주요 내용:")
        print("-" * 50)
        
        for i, video in enumerate(sorted_videos, 1):
            print(f"\n🗓️ {video['published_at'].strftime('%m월 %d일 (%a)')} 모닝브리프")
            print(f"📺 제목: {video['video_title']}")
            print(f"📈 중요도: {video['importance_score']:.2f} | 😊 감정: {video['sentiment_score']:.2f}")
            print(f"📝 핵심 요약:")
            print(f"   {video['summary']}")
            
            if video['key_insights']:
                print(f"💡 주요 인사이트:")
                for insight in video['key_insights'][:3]:  # 상위 3개만
                    print(f"   • {insight}")
            
            if video['mentioned_entities']:
                entities = ', '.join(video['mentioned_entities'][:5])  # 상위 5개만
                print(f"🏢 언급된 주요 종목/이슈: {entities}")
            
            print(f"👀 조회수: {video['view_count']:,}")
            print(f"🔗 {video['video_url']}")
            print("-" * 50)
        
        # 6. 주간 종합 분석
        if len(analysis_results) > 1:
            print(f"\n📊 주간 종합 분석")
            print("="*40)
            
            # 감정 변화 추이
            sentiments = [r['sentiment_score'] for r in sorted_videos[::-1]]  # 시간순으로 정렬
            print(f"📈 감정 점수 변화: {' → '.join([f'{s:.2f}' for s in sentiments])}")
            
            # 가장 중요한 이슈
            most_important = max(analysis_results, key=lambda x: x['importance_score'])
            print(f"\n🔥 가장 중요한 이슈:")
            print(f"   {most_important['video_title']}")
            print(f"   중요도: {most_important['importance_score']:.2f}")
            
            # 주요 언급 엔티티 통계
            all_entities = []
            for r in analysis_results:
                all_entities.extend(r['mentioned_entities'])
            
            entity_counts = {}
            for entity in all_entities:
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
            
            if entity_counts:
                top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"\n🏆 주간 핫 키워드:")
                for entity, count in top_entities:
                    print(f"   • {entity} ({count}회 언급)")
            
            # 전반적인 시장 전망
            avg_sentiment = sum([r['sentiment_score'] for r in analysis_results]) / len(analysis_results)
            if avg_sentiment > 0.2:
                market_mood = "긍정적 📈"
            elif avg_sentiment < -0.2:
                market_mood = "부정적 📉"
            else:
                market_mood = "중립적 ➡️"
            
            print(f"\n🎯 체슬리의 주간 시장 전망: {market_mood}")
            print(f"   평균 감정 점수: {avg_sentiment:.2f}")
        
        return {
            'videos': analysis_results,
            'stats': {
                'total_videos': len(morning_brief_videos),
                'analyzed_videos': len(analysis_results),
                'avg_sentiment': sum([r['sentiment_score'] for r in analysis_results])/len(analysis_results) if analysis_results else 0
            }
        }
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    analyze_chesley_morning_brief() 