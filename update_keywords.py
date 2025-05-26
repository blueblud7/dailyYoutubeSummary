#!/usr/bin/env python3

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path.cwd()))

from app.models.database import SessionLocal, Keyword

def update_keywords():
    """기존 키워드를 모두 삭제하고 새로운 키워드들로 교체합니다."""
    
    db = SessionLocal()
    
    try:
        # 1. 기존 키워드 모두 삭제
        print("🗑️ 기존 키워드 삭제 중...")
        existing_keywords = db.query(Keyword).all()
        for keyword in existing_keywords:
            print(f"   삭제: {keyword.keyword} ({keyword.category})")
            db.delete(keyword)
        
        db.commit()
        print(f"✅ 총 {len(existing_keywords)}개 키워드 삭제 완료")
        
        # 2. 새로운 키워드 추가
        print("\n➕ 새로운 키워드 추가 중...")
        
        new_keywords = [
            ("오건영", "인물"),
            ("성상현", "인물"), 
            ("나스닥", "투자"),
            ("AI", "기술")
        ]
        
        for keyword_text, category in new_keywords:
            keyword = Keyword(
                keyword=keyword_text,
                category=category
            )
            db.add(keyword)
            print(f"   추가: {keyword_text} ({category})")
        
        db.commit()
        print(f"✅ 총 {len(new_keywords)}개 키워드 추가 완료")
        
        # 3. 최종 결과 확인
        print("\n📋 최종 키워드 목록:")
        print("="*40)
        final_keywords = db.query(Keyword).all()
        
        categories = {}
        for kw in final_keywords:
            if kw.category not in categories:
                categories[kw.category] = []
            categories[kw.category].append(kw.keyword)
        
        for category, kw_list in categories.items():
            print(f"📂 **{category}** ({len(kw_list)}개):")
            for kw in kw_list:
                print(f"   • {kw}")
            print()
        
        print(f"📊 총 {len(final_keywords)}개 키워드, {len(categories)}개 카테고리")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_keywords() 