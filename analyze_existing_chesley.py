#!/usr/bin/env python3

from app.models.database import SessionLocal, Video, Analysis, Transcript
from datetime import datetime, timedelta
import json

def analyze_existing_chesley():
    """데이터베이스에 있는 체슬리TV 데이터를 분석합니다."""
    
    print("🌅 체슬리TV 기존 데이터 분석")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        # 체슬리TV 채널 ID
        chesley_channel_id = "UCXST0Hq6CAmG0dmo3jgrlEw"
        
        # 최근 7일 데이터 조회
        recent_date = datetime.now() - timedelta(days=7)
        videos = db.query(Video).filter(
            Video.channel_id == chesley_channel_id,
            Video.published_at >= recent_date
        ).order_by(Video.published_at.desc()).all()
        
        print(f"📺 최근 7일 체슬리TV 비디오: {len(videos)}개")
        
        # 모닝브리프만 필터링
        morning_brief_videos = []
        for video in videos:
            title_lower = video.title.lower()
            if any(keyword in title_lower for keyword in ['모닝브리프', 'morning brief', '모닝', 'morning']):
                morning_brief_videos.append(video)
        
        print(f"🌅 모닝브리프 비디오: {len(morning_brief_videos)}개")
        
        # 모닝브리프가 없으면 전체 비디오 중 최신 5개 분석
        if not morning_brief_videos:
            print("📺 모닝브리프가 없어 최신 비디오들을 분석합니다:")
            analysis_videos = videos[:5]
        else:
            analysis_videos = morning_brief_videos
        
        # 비디오별 상세 정보 수집
        analysis_results = []
        for video in analysis_videos:
            # 분석 데이터 가져오기
            analysis = db.query(Analysis).filter(
                Analysis.video_id == video.video_id
            ).first()
            
            # 자막 데이터 가져오기  
            transcript = db.query(Transcript).filter(
                Transcript.video_id == video.video_id
            ).first()
            
            video_info = {
                'video_title': video.title,
                'published_at': video.published_at,
                'view_count': video.view_count,
                'video_url': video.video_url,
                'has_transcript': transcript is not None,
                'transcript_language': transcript.language if transcript else None,
                'transcript_auto': transcript.is_auto_generated if transcript else None,
                'has_analysis': analysis is not None
            }
            
            if analysis:
                video_info.update({
                    'summary': analysis.summary,
                    'sentiment_score': analysis.sentiment_score,
                    'importance_score': analysis.importance_score,
                    'key_insights': json.loads(analysis.key_insights) if analysis.key_insights else [],
                    'mentioned_entities': json.loads(analysis.mentioned_entities) if analysis.mentioned_entities else []
                })
            
            analysis_results.append(video_info)
        
        # 결과 출력
        print(f"\n🎯 분석 결과 요약:")
        print(f"- 분석 기간: {recent_date.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}")
        print(f"- 전체 비디오: {len(videos)}개")
        print(f"- 분석 대상: {len(analysis_videos)}개")
        
        # 자막/분석 통계
        transcript_count = sum(1 for v in analysis_results if v['has_transcript'])
        analysis_count = sum(1 for v in analysis_results if v['has_analysis'])
        
        print(f"- 자막 보유: {transcript_count}/{len(analysis_results)}개")
        print(f"- 분석 완료: {analysis_count}/{len(analysis_results)}개")
        
        if analysis_count > 0:
            avg_sentiment = sum(v.get('sentiment_score', 0) for v in analysis_results if v['has_analysis']) / analysis_count
            print(f"- 평균 감정 점수: {avg_sentiment:.2f}")
        
        print(f"\n📋 상세 분석 결과:")
        print("="*60)
        
        for i, video in enumerate(analysis_results, 1):
            print(f"\n{i}. 📺 {video['video_title']}")
            print(f"   📅 {video['published_at'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   👀 조회수: {video['view_count']:,}")
            
            # 자막 정보
            if video['has_transcript']:
                auto_text = "자동" if video['transcript_auto'] else "수동"
                print(f"   📝 자막: ✅ ({video['transcript_language']}, {auto_text})")
            else:
                print(f"   📝 자막: ❌")
            
            # 분석 정보
            if video['has_analysis']:
                print(f"   🤖 분석: ✅")
                print(f"   📈 중요도: {video['importance_score']:.2f} | 😊 감정: {video['sentiment_score']:.2f}")
                print(f"   💬 요약: {video['summary'][:100]}...")
                
                if video['key_insights']:
                    print(f"   💡 인사이트:")
                    for insight in video['key_insights'][:2]:
                        print(f"      • {insight}")
                
                if video['mentioned_entities']:
                    entities = ', '.join(video['mentioned_entities'][:5])
                    print(f"   🏢 주요 언급: {entities}")
            else:
                print(f"   🤖 분석: ❌")
            
            print(f"   🔗 {video['video_url']}")
            print("-" * 50)
        
        # 모닝브리프가 있는 경우 추가 분석
        if morning_brief_videos and analysis_count > 1:
            print(f"\n📊 모닝브리프 종합 분석")
            print("="*40)
            
            analyzed_morning = [v for v in analysis_results if v['has_analysis'] and 
                               any(keyword in v['video_title'].lower() for keyword in ['모닝브리프', 'morning'])]
            
            if analyzed_morning:
                # 감정 변화 추이
                sentiments = [v['sentiment_score'] for v in reversed(analyzed_morning)]
                print(f"📈 감정 점수 변화: {' → '.join([f'{s:.2f}' for s in sentiments])}")
                
                # 가장 중요한 이슈
                most_important = max(analyzed_morning, key=lambda x: x['importance_score'])
                print(f"\n🔥 가장 중요한 이슈:")
                print(f"   {most_important['video_title']}")
                print(f"   중요도: {most_important['importance_score']:.2f}")
                
                # 주요 언급 엔티티 통계
                all_entities = []
                for v in analyzed_morning:
                    all_entities.extend(v['mentioned_entities'])
                
                entity_counts = {}
                for entity in all_entities:
                    entity_counts[entity] = entity_counts.get(entity, 0) + 1
                
                if entity_counts:
                    top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(f"\n🏆 주간 핫 키워드:")
                    for entity, count in top_entities:
                        print(f"   • {entity} ({count}회 언급)")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    analyze_existing_chesley() 