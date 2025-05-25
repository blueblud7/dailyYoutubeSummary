#!/usr/bin/env python3
"""
기본 키워드 추가 스크립트
"""

from app.models.database import SessionLocal, Keyword, create_tables
from datetime import datetime

def add_default_keywords():
    """기본 투자/경제 키워드들을 데이터베이스에 추가"""
    
    default_keywords = [
        # 투자 관련
        ("주식", "투자"),
        ("코스피", "투자"),
        ("코스닥", "투자"),
        ("삼성전자", "투자"),
        ("SK하이닉스", "투자"),
        ("NAVER", "투자"),
        ("카카오", "투자"),
        ("현대차", "투자"),
        ("포스코", "투자"),
        ("LG에너지솔루션", "투자"),
        
        # 암호화폐
        ("비트코인", "암호화폐"),
        ("이더리움", "암호화폐"),
        ("리플", "암호화폐"),
        ("도지코인", "암호화폐"),
        ("블록체인", "암호화폐"),
        
        # 부동산
        ("부동산", "부동산"),
        ("아파트", "부동산"),
        ("전세", "부동산"),
        ("월세", "부동산"),
        ("분양", "부동산"),
        ("재개발", "부동산"),
        ("재건축", "부동산"),
        
        # 경제 지표
        ("금리", "경제"),
        ("인플레이션", "경제"),
        ("환율", "경제"),
        ("달러", "경제"),
        ("원화", "경제"),
        ("GDP", "경제"),
        ("실업률", "경제"),
        ("기준금리", "경제"),
        
        # 국제 경제
        ("미국", "국제경제"),
        ("중국", "국제경제"),
        ("일본", "국제경제"),
        ("유럽", "국제경제"),
        ("연준", "국제경제"),
        ("미연준", "국제경제"),
        ("파월", "국제경제"),
        
        # 정책/제도
        ("정부정책", "정책"),
        ("규제", "정책"),
        ("세금", "정책"),
        ("양도세", "정책"),
        ("종부세", "정책"),
        ("부가세", "정책"),
        
        # 시장 동향
        ("시장전망", "시장동향"),
        ("경기침체", "시장동향"),
        ("경기회복", "시장동향"),
        ("버블", "시장동향"),
        ("폭락", "시장동향"),
        ("급등", "시장동향"),
        
        # 기업/산업
        ("반도체", "산업"),
        ("자동차", "산업"),
        ("배터리", "산업"),
        ("바이오", "산업"),
        ("게임", "산업"),
        ("플랫폼", "산업"),
        ("AI", "산업"),
        ("인공지능", "산업"),
    ]
    
    print('🔍 기본 키워드 추가 중...\n')
    
    # 테이블 생성 확인
    create_tables()
    
    db = SessionLocal()
    try:
        added_count = 0
        
        for keyword_text, category in default_keywords:
            # 중복 확인
            existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
            
            if not existing:
                keyword = Keyword(
                    keyword=keyword_text,
                    category=category
                )
                
                db.add(keyword)
                print(f'➕ {keyword_text} ({category})')
                added_count += 1
            else:
                print(f'⚠️ {keyword_text} (이미 존재)')
        
        db.commit()
        print(f'\n🎉 {added_count}개의 새로운 키워드가 추가되었습니다!')
        
        # 최종 키워드 통계
        total_keywords = db.query(Keyword).count()
        categories = db.query(Keyword.category).distinct().all()
        
        print(f'\n📊 전체 키워드 현황:')
        print(f'   총 키워드: {total_keywords}개')
        print(f'   카테고리: {len(categories)}개')
        
        # 카테고리별 개수
        print(f'\n📝 카테고리별 키워드 개수:')
        for category_row in categories:
            category = category_row[0]
            count = db.query(Keyword).filter(Keyword.category == category).count()
            print(f'   {category}: {count}개')
        
    except Exception as e:
        print(f'❌ 키워드 추가 중 오류 발생: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_default_keywords() 