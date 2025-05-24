#!/usr/bin/env python3

from app.services.youtube_service import YouTubeService
from app.models.database import SessionLocal, Channel, Video, Transcript, Analysis, PersonInfluencer
from app.services.data_collector import DataCollector

def get_channel_id_from_handle(youtube_service, handle):
    """YouTube 핸들(@username)에서 채널 ID를 가져옵니다."""
    try:
        # @ 제거
        if handle.startswith('@'):
            handle = handle[1:]
        
        # 검색을 통해 채널 찾기
        channels = youtube_service.search_channels(handle, max_results=5)
        
        if channels:
            # 가장 관련성 높은 채널 반환
            for channel in channels:
                if handle.lower() in channel['channel_name'].lower() or channel['channel_name'].lower() in handle.lower():
                    return channel['channel_id']
            # 첫 번째 결과 반환
            return channels[0]['channel_id']
        return None
    except Exception as e:
        print(f"핸들 {handle} 검색 중 오류: {e}")
        return None

def clear_existing_data(db):
    """기존 데이터를 모두 삭제합니다."""
    print("기존 데이터 삭제 중...")
    
    # 관련 데이터 순서대로 삭제
    db.query(Analysis).delete()
    db.query(Transcript).delete() 
    db.query(Video).delete()
    db.query(Channel).delete()
    db.query(PersonInfluencer).delete()
    
    db.commit()
    print("✅ 기존 데이터 삭제 완료")

def main():
    # 새로운 채널 URL들
    new_channels = [
        "chesleytv",           # 체슬리TV
        "understanding.",      # 언더스탠딩
        "오종태",              # 오종태
        "kimjoonsongtv",       # 김준송TV  
        "sosumonkey",          # 소수몽키
        "MK_Invest",           # MK Invest
        "hkglobalmarket"       # HK Global Market
    ]
    
    # 인물들
    influencers = [
        {"name": "오건영", "title": "투자전문가", "expertise_area": "거시경제분석"},
        {"name": "박세익", "title": "투자전문가", "expertise_area": "주식투자"},
        {"name": "김준송", "title": "유튜버", "expertise_area": "주식투자"},
        {"name": "성상현", "title": "투자전문가", "expertise_area": "투자분석"},
        {"name": "문홍철", "title": "투자전문가", "expertise_area": "시장분석"}
    ]
    
    db = SessionLocal()
    youtube_service = YouTubeService()
    data_collector = DataCollector()
    
    try:
        # 1. 기존 데이터 삭제
        clear_existing_data(db)
        
        # 2. 새로운 채널들 추가
        print("\n새로운 채널들 추가 중...")
        added_channels = []
        
        for handle in new_channels:
            print(f"\n채널 처리 중: @{handle}")
            
            # 핸들에서 채널 ID 찾기
            channel_id = get_channel_id_from_handle(youtube_service, handle)
            
            if channel_id:
                # 채널 정보 가져오기 및 추가
                channel = data_collector.add_channel(channel_id, db)
                if channel:
                    added_channels.append(channel)
                    print(f"✅ 추가됨: {channel.channel_name} (구독자: {channel.subscriber_count:,}명)")
                else:
                    print(f"❌ 채널 추가 실패: {handle}")
            else:
                print(f"❌ 채널 ID를 찾을 수 없음: {handle}")
        
        # 3. 인물들 추가
        print("\n인물들 추가 중...")
        for person in influencers:
            influencer = PersonInfluencer(
                name=person["name"],
                title=person["title"],
                expertise_area=person["expertise_area"],
                influence_score=0.8  # 기본 영향력 점수
            )
            db.add(influencer)
            print(f"✅ 인물 추가: {person['name']} ({person['expertise_area']})")
        
        db.commit()
        
        # 4. 결과 출력
        print(f"\n🎉 설정 완료!")
        print(f"📺 추가된 채널: {len(added_channels)}개")
        print(f"👥 추가된 인물: {len(influencers)}명")
        
        print(f"\n📋 추가된 채널 목록:")
        for channel in added_channels:
            print(f"- {channel.channel_name} (ID: {channel.channel_id})")
        
        return [channel.channel_id for channel in added_channels]
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
        return []
    finally:
        db.close()

if __name__ == "__main__":
    channel_ids = main()
    print(f"\n새로운 채널 ID들: {channel_ids}") 