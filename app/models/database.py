from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('config.env')

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///investment_insights.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String, unique=True, index=True)
    channel_name = Column(String, index=True)
    channel_url = Column(String)
    description = Column(Text)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    videos = relationship("Video", back_populates="channel")

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, index=True)
    channel_id = Column(String, ForeignKey("channels.channel_id"))
    title = Column(String, index=True)
    description = Column(Text)
    published_at = Column(DateTime)
    duration = Column(String)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    video_url = Column(String)
    thumbnail_url = Column(String)
    tags = Column(Text)  # JSON string으로 저장
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    channel = relationship("Channel", back_populates="videos")
    transcript = relationship("Transcript", back_populates="video", uselist=False)
    video_analysis = relationship("VideoAnalysis", back_populates="video", uselist=False)
    analysis = relationship("Analysis", back_populates="video")

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.video_id"), unique=True)
    transcript_text = Column(Text)
    transcript_length = Column(Integer)  # 자막 길이
    is_auto_generated = Column(Boolean, default=False)
    language = Column(String, default="ko")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    video = relationship("Video", back_populates="transcript")

class VideoAnalysis(Base):
    """포괄적인 AI 영상 분석 결과를 저장하는 테이블"""
    __tablename__ = "video_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.video_id"), unique=True, index=True)
    
    # 기본 분석 정보
    executive_summary = Column(Text)  # 종합 요약
    sentiment = Column(String)  # positive/negative/neutral/mixed
    importance_score = Column(Float)  # 0.0-1.0
    confidence_level = Column(Float)  # 0.0-1.0
    
    # 상세 분석 (JSON 형태로 저장)
    detailed_insights = Column(Text)  # JSON: 구체적인 인사이트 리스트
    market_analysis = Column(Text)  # JSON: 시장 분석 (현재상황, 미래전망, 리스크, 기회)
    investment_implications = Column(Text)  # JSON: 투자 시사점
    key_data_points = Column(Text)  # JSON: 핵심 데이터 포인트
    expert_opinions = Column(Text)  # JSON: 전문가 의견
    historical_context = Column(Text)  # 역사적 맥락
    actionable_steps = Column(Text)  # JSON: 실행 가능한 단계
    
    # 메타데이터
    topics = Column(Text)  # JSON: 주요 키워드
    related_companies = Column(Text)  # JSON: 관련 기업들
    economic_indicators = Column(Text)  # JSON: 경제지표들
    time_sensitive_info = Column(Text)  # 시간 민감 정보
    
    # AI 모델 정보
    ai_model_used = Column(String)  # 사용된 AI 모델
    analysis_version = Column(String, default="1.0")  # 분석 버전
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    video = relationship("Video", back_populates="video_analysis")

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True)
    category = Column(String)  # 투자, 경제, 부동산 등
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    analyses = relationship("Analysis", back_populates="keyword")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.video_id"))
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    summary = Column(Text)
    sentiment_score = Column(Float)  # -1 ~ 1 (부정적 ~ 긍정적)
    key_insights = Column(Text)  # JSON string으로 저장
    importance_score = Column(Float)  # 0 ~ 1 (중요도)
    mentioned_entities = Column(Text)  # JSON string으로 저장 (인물, 기업 등)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    video = relationship("Video", back_populates="analysis")
    keyword = relationship("Keyword", back_populates="analyses")

class AnalysisCache(Base):
    """분석 캐시 관리를 위한 테이블"""
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.video_id"), unique=True, index=True)
    cache_key = Column(String, index=True)  # 캐시 키 (video_id + transcript_hash)
    is_valid = Column(Boolean, default=True)  # 캐시 유효성
    ai_model_version = Column(String)  # AI 모델 버전
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String)  # daily, weekly, monthly
    title = Column(String)
    content = Column(Text)
    summary = Column(Text)
    key_trends = Column(Text)  # JSON string으로 저장
    market_sentiment = Column(String)
    recommendations = Column(Text)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class PersonInfluencer(Base):
    __tablename__ = "person_influencers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    title = Column(String)  # 전문가, 유튜버, 애널리스트 등
    expertise_area = Column(String)  # 주식, 부동산, 경제 등
    channel_ids = Column(Text)  # JSON string으로 여러 채널 저장 가능
    bio = Column(Text)
    influence_score = Column(Float)  # 영향력 점수
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 데이터베이스 테이블 생성
def create_tables():
    Base.metadata.create_all(bind=engine)

# 데이터베이스 세션 생성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 