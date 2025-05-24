import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.models.database import create_tables

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# FastAPI 앱 생성
app = FastAPI(
    title="투자 인사이트 분석 시스템",
    description="유튜브 콘텐츠를 분석하여 투자 인사이트를 제공하는 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에서는 특정 도메인만 허용하도록 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
app.include_router(router, prefix="/api/v1", tags=["Investment Insights"])

# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    logging.info("투자 인사이트 분석 시스템 시작")
    
    # 데이터베이스 테이블 생성
    create_tables()
    logging.info("데이터베이스 테이블 생성 완료")

# 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    logging.info("투자 인사이트 분석 시스템 종료")

# 기본 라우트
@app.get("/")
async def root():
    """루트 경로"""
    return {
        "message": "투자 인사이트 분석 시스템 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 