#!/usr/bin/env python3

from app.services.youtube_service import YouTubeService
from app.models.database import SessionLocal, Channel

# 기본 채널 정보 확인
default_channels = [
    'UCXST0Hq6CAmG0dmo3jgrlEw',  # 체슬리TV
    'UCIUni4ScRp4mqPXsxy62L5w',  # 언더스탠딩 : 세상의 모든 지식
    'UCSVtOfGvhtz2QosSIM_3WoQ',  # 오종태의 투자병법
    'UC18feVzOBjtLU9trm8A788g',  # 김준송TV
    'UCC3yfxS5qC6PCwDzetUuEWg',  # 소수몽키
    'UCr29QUcfio3Y_EX0T4DHCJQ',  # Mkinvest
    'UCWskYkV4c4S9D__rsfOl2JA',  # 한경 글로벌마켓
]

print('=== 기본 설정된 채널들 ===')
youtube = YouTubeService()
for i, channel_id in enumerate(default_channels):
    try:
        info = youtube.get_channel_details(channel_id)
        if info:
            print(f'{i+1}. {info["channel_name"]} (구독자: {info["subscriber_count"]:,}명)')
            print(f'   채널 ID: {channel_id}')
        else:
            print(f'{i+1}. 채널 정보를 가져올 수 없음: {channel_id}')
    except Exception as e:
        print(f'{i+1}. 오류 ({channel_id}): {e}')

print()
print('=== 데이터베이스 등록된 채널들 ===')
db = SessionLocal()
try:
    channels = db.query(Channel).all()
    if channels:
        for channel in channels:
            print(f'- {channel.channel_name} (ID: {channel.channel_id})')
            print(f'  구독자: {channel.subscriber_count:,}명, 등록일: {channel.created_at.strftime("%Y-%m-%d")}')
    else:
        print('데이터베이스에 등록된 채널이 없습니다.')
finally:
    db.close() 