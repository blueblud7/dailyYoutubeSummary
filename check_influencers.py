#!/usr/bin/env python3

from app.models.database import SessionLocal, PersonInfluencer

print('=== 등록된 인물들 ===')
db = SessionLocal()
try:
    influencers = db.query(PersonInfluencer).all()
    if influencers:
        for person in influencers:
            print(f'👤 {person.name}')
            print(f'   직책: {person.title}')
            print(f'   전문분야: {person.expertise_area}')
            print(f'   영향력 점수: {person.influence_score}')
            print(f'   등록일: {person.created_at.strftime("%Y-%m-%d")}')
            print()
    else:
        print('등록된 인물이 없습니다.')
finally:
    db.close() 