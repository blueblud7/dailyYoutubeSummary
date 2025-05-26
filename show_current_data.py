#!/usr/bin/env python3

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path.cwd()))

from app.models.database import SessionLocal, Channel, Keyword

def show_current_data():
    """현재 등록된 채널과 키워드를 표시합니다."""
    
    db = SessionLocal()
    
    print('📺 등록된 채널 목록:')
    print('='*60)
    channels = db.query(Channel).all()
    
    if channels:
        for i, ch in enumerate(channels, 1):
            print(f'{i:2d}. {ch.channel_name}')
            if ch.subscriber_count:
                print(f'    👥 구독자: {ch.subscriber_count:,}명')
            if ch.video_count:
                print(f'    📹 영상 수: {ch.video_count:,}개')
            if ch.description:
                desc = ch.description[:100] + "..." if len(ch.description) > 100 else ch.description
                print(f'    📝 설명: {desc}')
            print(f'    🆔 채널 ID: {ch.channel_id}')
            if ch.channel_url:
                print(f'    🔗 URL: {ch.channel_url}')
            print()
    else:
        print('❌ 등록된 채널이 없습니다.')
    
    print()
    print('🔍 등록된 키워드 목록:')
    print('='*60)
    keywords = db.query(Keyword).all()
    
    if keywords:
        # 카테고리별로 그룹화
        categories = {}
        for kw in keywords:
            if kw.category not in categories:
                categories[kw.category] = []
            categories[kw.category].append(kw.keyword)
        
        for category, kw_list in categories.items():
            print(f'📂 **{category}** ({len(kw_list)}개):')
            for kw in kw_list:
                print(f'   • {kw}')
            print()
    else:
        print('❌ 등록된 키워드가 없습니다.')
    
    print()
    print('📊 시스템 요약:')
    print('='*60)
    print(f'📺 총 채널: {len(channels)}개')
    print(f'🔍 총 키워드: {len(keywords)}개')
    
    if keywords:
        print(f'📂 카테고리: {len(set(kw.category for kw in keywords))}개')
    
    db.close()

if __name__ == "__main__":
    show_current_data() 