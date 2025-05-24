#!/usr/bin/env python3

from app.services.data_collector import DataCollector
from app.services.youtube_service import YouTubeService
from app.models.database import SessionLocal, Video, Transcript, Analysis
from datetime import datetime, timedelta

def retry_failed_transcripts():
    """자막 수집에 실패한 비디오들을 다시 처리합니다."""
    
    print("🔄 자막 수집 실패 비디오 재시도")
    print("="*40)
    
    db = SessionLocal()
    data_collector = DataCollector()
    youtube_service = YouTubeService()
    
    try:
        # 체슬리TV 최근 비디오 중 자막이 없는 것들 찾기
        chesley_channel_id = "UCXST0Hq6CAmG0dmo3jgrlEw"
        
        # 최근 7일 체슬리TV 비디오 중 자막이 없는 것들
        recent_date = datetime.now() - timedelta(days=7)
        videos_without_transcripts = db.query(Video).filter(
            Video.channel_id == chesley_channel_id,
            Video.published_at >= recent_date
        ).all()
        
        print(f"📺 체슬리TV 최근 비디오: {len(videos_without_transcripts)}개")
        
        # 자막이 없는 비디오 찾기
        videos_to_retry = []
        for video in videos_without_transcripts:
            transcript = db.query(Transcript).filter(
                Transcript.video_id == video.video_id
            ).first()
            
            if not transcript:
                videos_to_retry.append(video)
        
        print(f"🔍 자막이 없는 비디오: {len(videos_to_retry)}개")
        
        if not videos_to_retry:
            print("✅ 모든 비디오에 자막이 있습니다.")
            return
        
        # 자막이 없는 비디오들 목록 출력
        print("\n📋 자막 재시도 대상:")
        for i, video in enumerate(videos_to_retry, 1):
            print(f"{i}. {video.title}")
            print(f"   📅 {video.published_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   🔗 {video.video_url}")
            print()
        
        # 1. 개선된 자막 수집 재시도
        print("🎬 개선된 자막 수집 재시도...")
        success_count = 0
        for video in videos_to_retry:
            print(f"\n처리 중: {video.title[:50]}...")
            
            # 개선된 자막 추출 시도
            transcript_data = youtube_service.get_video_transcript(video.video_id)
            
            if transcript_data:
                # 자막 저장
                transcript = Transcript(
                    video_id=transcript_data['video_id'],
                    transcript_text=transcript_data['transcript_text'],
                    is_auto_generated=transcript_data['is_auto_generated'],
                    language=transcript_data['language']
                )
                db.add(transcript)
                success_count += 1
                print(f"   ✅ 자막 수집 성공 ({transcript_data['language']})")
            else:
                print(f"   ❌ 자막 수집 실패")
        
        db.commit()
        print(f"\n🎯 자막 수집 결과: {success_count}/{len(videos_to_retry)}개 성공")
        
        # 2. 분석 재시도 (자막이 있는 것 + 제목/설명 분석)
        print(f"\n🤖 분석 재시도...")
        keywords = ["투자", "주식", "경제", "시장", "전망", "모닝브리프"]
        
        # 분석이 없는 비디오들 찾기
        videos_to_analyze = []
        for video in videos_to_retry:
            existing_analysis = db.query(Analysis).filter(
                Analysis.video_id == video.video_id
            ).first()
            
            if not existing_analysis:
                videos_to_analyze.append(video)
        
        if videos_to_analyze:
            analyses = data_collector.analyze_videos(videos_to_analyze, keywords, db)
            print(f"✅ 분석 완료: {len(analyses)}개")
        else:
            print("✅ 모든 비디오가 이미 분석되었습니다.")
        
        # 3. 결과 확인
        print(f"\n📊 최종 결과:")
        for video in videos_to_retry:
            transcript = db.query(Transcript).filter(
                Transcript.video_id == video.video_id
            ).first()
            
            analysis_count = db.query(Analysis).filter(
                Analysis.video_id == video.video_id
            ).count()
            
            transcript_status = "✅ 있음" if transcript else "❌ 없음"
            analysis_status = f"✅ {analysis_count}개" if analysis_count > 0 else "❌ 없음"
            
            print(f"📺 {video.title[:40]}...")
            print(f"   자막: {transcript_status}")
            if transcript:
                print(f"   언어: {transcript.language} ({'자동' if transcript.is_auto_generated else '수동'})")
            print(f"   분석: {analysis_status}")
            print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    retry_failed_transcripts() 