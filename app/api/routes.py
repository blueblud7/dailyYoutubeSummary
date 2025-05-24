from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from app.models.database import get_db
from app.services.data_collector import DataCollector
from app.services.report_service import ReportService
from app.services.scheduler import scheduler
from app.services.personalized_report_service import PersonalizedReportService
from app.services.notification_service import NotificationService
from app.services.telegram_bot_service import telegram_bot

router = APIRouter()
data_collector = DataCollector()
report_service = ReportService()
personalized_report_service = PersonalizedReportService()
notification_service = NotificationService()

# Pydantic 모델들
class ChannelRequest(BaseModel):
    channel_ids: List[str]

class KeywordRequest(BaseModel):
    keywords: List[str]
    category: str = "투자"

class CollectionRequest(BaseModel):
    channel_ids: List[str]
    keywords: List[str]
    days_back: int = 1

class ReportRequest(BaseModel):
    keywords: Optional[List[str]] = None
    target_date: Optional[date] = None

class PerspectiveRequest(BaseModel):
    topic: str
    keywords: List[str]
    days_back: int = 7

# 데이터 수집 관련 엔드포인트
@router.post("/collection/channels", summary="채널 추가")
async def add_channels(request: ChannelRequest, db: Session = Depends(get_db)):
    """새로운 채널들을 시스템에 추가합니다."""
    try:
        added_channels = []
        for channel_id in request.channel_ids:
            channel = data_collector.add_channel(channel_id, db)
            if channel:
                added_channels.append({
                    "channel_id": channel.channel_id,
                    "channel_name": channel.channel_name,
                    "subscriber_count": channel.subscriber_count
                })
        
        return {
            "success": True,
            "message": f"{len(added_channels)}개 채널이 추가되었습니다.",
            "channels": added_channels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collection/keywords", summary="키워드 추가")
async def add_keywords(request: KeywordRequest, db: Session = Depends(get_db)):
    """새로운 키워드들을 시스템에 추가합니다."""
    try:
        keywords = data_collector.add_keywords(request.keywords, request.category, db)
        return {
            "success": True,
            "message": f"{len(keywords)}개 키워드가 추가되었습니다.",
            "keywords": [{"keyword": k.keyword, "category": k.category} for k in keywords]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collection/run", summary="데이터 수집 실행")
async def run_collection(request: CollectionRequest, db: Session = Depends(get_db)):
    """지정된 채널과 키워드로 데이터 수집을 실행합니다."""
    try:
        result = data_collector.run_daily_collection(
            channel_ids=request.channel_ids,
            keywords=request.keywords,
            db=db
        )
        return {
            "success": True,
            "message": "데이터 수집이 완료되었습니다.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collection/status", summary="수집 상태 조회")
async def get_collection_status(db: Session = Depends(get_db)):
    """시스템의 현재 수집 상태를 조회합니다."""
    try:
        from app.models.database import Channel, Video, Transcript, Analysis
        
        channel_count = db.query(Channel).count()
        video_count = db.query(Video).count()
        transcript_count = db.query(Transcript).count()
        analysis_count = db.query(Analysis).count()
        
        # 최근 수집된 비디오
        recent_videos = db.query(Video).order_by(Video.created_at.desc()).limit(5).all()
        
        return {
            "statistics": {
                "total_channels": channel_count,
                "total_videos": video_count,
                "total_transcripts": transcript_count,
                "total_analyses": analysis_count
            },
            "recent_videos": [
                {
                    "title": video.title,
                    "channel_id": video.channel_id,
                    "published_at": video.published_at.isoformat(),
                    "view_count": video.view_count
                }
                for video in recent_videos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 리포트 관련 엔드포인트
@router.post("/reports/daily", summary="일일 리포트 생성")
async def generate_daily_report(request: ReportRequest, db: Session = Depends(get_db)):
    """일일 투자 인사이트 리포트를 생성합니다."""
    try:
        target_date = request.target_date
        if target_date:
            target_date = datetime.combine(target_date, datetime.min.time())
        
        report = report_service.generate_daily_report(
            db=db,
            target_date=target_date,
            keywords=request.keywords
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/weekly", summary="주간 리포트 생성")
async def generate_weekly_report(keywords: Optional[List[str]] = Body(None), db: Session = Depends(get_db)):
    """주간 투자 인사이트 리포트를 생성합니다."""
    try:
        report = report_service.generate_weekly_report(
            db=db,
            keywords=keywords
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/perspective", summary="관점 비교 리포트 생성")
async def generate_perspective_report(request: PerspectiveRequest, db: Session = Depends(get_db)):
    """특정 주제에 대한 채널별 관점 비교 리포트를 생성합니다."""
    try:
        report = report_service.generate_perspective_comparison_report(
            db=db,
            topic=request.topic,
            keywords=request.keywords,
            days_back=request.days_back
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/history", summary="리포트 히스토리 조회")
async def get_report_history(
    report_type: Optional[str] = Query(None, description="리포트 타입 (daily, weekly)"),
    limit: int = Query(20, description="조회할 개수"),
    db: Session = Depends(get_db)
):
    """생성된 리포트들의 히스토리를 조회합니다."""
    try:
        reports = report_service.get_report_history(db, report_type, limit)
        return {
            "reports": reports,
            "total": len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}", summary="특정 리포트 조회")
async def get_report_detail(report_id: int, db: Session = Depends(get_db)):
    """특정 리포트의 상세 내용을 조회합니다."""
    try:
        from app.models.database import Report
        import json
        
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
        
        return {
            "id": report.id,
            "report_type": report.report_type,
            "title": report.title,
            "content": json.loads(report.content) if report.content else {},
            "summary": report.summary,
            "key_trends": json.loads(report.key_trends) if report.key_trends else [],
            "market_sentiment": report.market_sentiment,
            "recommendations": json.loads(report.recommendations) if report.recommendations else [],
            "date_range": {
                "start": report.date_range_start.isoformat(),
                "end": report.date_range_end.isoformat()
            },
            "created_at": report.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 분석 관련 엔드포인트
@router.get("/analysis/trends", summary="트렌드 분석 조회")
async def get_trend_analysis(
    keywords: Optional[List[str]] = Query(None),
    days_back: int = Query(7, description="분석할 일수"),
    db: Session = Depends(get_db)
):
    """특정 기간의 트렌드 분석 결과를 조회합니다."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        analyses = report_service.get_period_analyses(db, start_date, end_date, keywords)
        
        if not analyses:
            return {"message": "분석할 데이터가 없습니다."}
        
        from app.services.analysis_service import AnalysisService
        analysis_service = AnalysisService()
        
        trend_analysis = analysis_service.generate_trend_analysis(
            analyses, keywords or [], f"최근 {days_back}일"
        )
        
        return {
            "period": f"{start_date.strftime('%Y.%m.%d')} - {end_date.strftime('%Y.%m.%d')}",
            "total_analyses": len(analyses),
            "trend_analysis": trend_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/videos", summary="비디오 분석 결과 조회")
async def get_video_analyses(
    limit: int = Query(50, description="조회할 개수"),
    channel_id: Optional[str] = Query(None, description="특정 채널만 조회"),
    min_importance: float = Query(0.0, description="최소 중요도 점수"),
    db: Session = Depends(get_db)
):
    """비디오 분석 결과들을 조회합니다."""
    try:
        from app.models.database import Video, Analysis, Channel
        
        query = db.query(Analysis).join(Video)
        
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
        
        if min_importance > 0:
            query = query.filter(Analysis.importance_score >= min_importance)
        
        analyses = query.order_by(Analysis.created_at.desc()).limit(limit).all()
        
        results = []
        for analysis in analyses:
            video = db.query(Video).filter(Video.video_id == analysis.video_id).first()
            channel = db.query(Channel).filter(Channel.channel_id == video.channel_id).first()
            
            results.append({
                "video_title": video.title,
                "channel_name": channel.channel_name if channel else "Unknown",
                "summary": analysis.summary,
                "sentiment_score": analysis.sentiment_score,
                "importance_score": analysis.importance_score,
                "published_at": video.published_at.isoformat(),
                "video_url": video.video_url
            })
        
        return {
            "analyses": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 스케줄러 관련 엔드포인트
@router.post("/scheduler/manual/collection", summary="수동 데이터 수집 실행")
async def run_manual_collection(
    channels: Optional[List[str]] = Body(None),
    keywords: Optional[List[str]] = Body(None)
):
    """스케줄러를 통해 수동으로 데이터 수집을 실행합니다."""
    try:
        result = scheduler.run_manual_collection(channels, keywords)
        return {
            "success": True,
            "message": "수동 데이터 수집이 완료되었습니다.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/manual/report", summary="수동 리포트 생성")
async def run_manual_report(
    report_type: str = Body("daily", description="리포트 타입 (daily, weekly)"),
    keywords: Optional[List[str]] = Body(None)
):
    """스케줄러를 통해 수동으로 리포트를 생성합니다."""
    try:
        result = scheduler.run_manual_report(report_type, keywords)
        return {
            "success": True,
            "message": f"수동 {report_type} 리포트 생성이 완료되었습니다.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 개인화된 리포트 엔드포인트
@router.post("/reports/personalized/keyword", summary="키워드 집중 리포트 생성")
async def generate_keyword_report(
    keyword: str = Body(..., description="분석할 키워드"),
    days_back: int = Body(1, description="분석 기간 (일)"),
    db: Session = Depends(get_db)
):
    """특정 키워드에 집중한 개인화된 리포트를 생성합니다."""
    try:
        report = personalized_report_service.generate_keyword_focused_report(
            db, keyword, days_back
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/personalized/channel", summary="채널 집중 리포트 생성")
async def generate_channel_report(
    channel_name: str = Body(..., description="분석할 채널명"),
    days_back: int = Body(7, description="분석 기간 (일)"),
    db: Session = Depends(get_db)
):
    """특정 채널에 집중한 개인화된 리포트를 생성합니다."""
    try:
        report = personalized_report_service.generate_channel_focused_report(
            db, channel_name, days_back
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/personalized/influencer", summary="인플루언서 언급 분석")
async def generate_influencer_report(
    influencer_name: str = Body(..., description="분석할 인플루언서명"),
    days_back: int = Body(7, description="분석 기간 (일)"),
    db: Session = Depends(get_db)
):
    """특정 인플루언서 언급에 집중한 리포트를 생성합니다."""
    try:
        report = personalized_report_service.generate_influencer_focused_report(
            db, influencer_name, days_back
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/personalized/multi", summary="다차원 개인화 리포트")
async def generate_multi_dimension_report(
    request: dict = Body(..., description="다차원 리포트 요청"),
    db: Session = Depends(get_db)
):
    """키워드, 채널, 인플루언서를 종합한 다차원 리포트를 생성합니다."""
    try:
        keywords = request.get('keywords', [])
        channels = request.get('channels', [])
        influencers = request.get('influencers', [])
        days_back = request.get('days_back', 7)
        
        report = personalized_report_service.generate_multi_dimension_report(
            db, keywords, channels, influencers, days_back
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 알림 테스트 엔드포인트
@router.post("/notifications/test", summary="알림 테스트")
async def test_notifications(
    notification_type: str = Body("email", description="알림 타입 (email, slack, telegram)"),
    test_message: str = Body("테스트 메시지입니다.", description="테스트 메시지")
):
    """알림 시스템을 테스트합니다."""
    try:
        if notification_type == "email":
            result = notification_service.send_email(
                "🧪 알림 테스트", 
                f"<h2>테스트 메시지</h2><p>{test_message}</p>"
            )
        elif notification_type == "slack":
            result = notification_service.send_slack_message(f"🧪 *테스트*\n{test_message}")
        elif notification_type == "telegram":
            result = notification_service.send_telegram_message(f"🧪 **테스트**\n{test_message}")
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 알림 타입입니다.")
        
        return {
            "success": result,
            "message": f"{notification_type} 알림 테스트 {'성공' if result else '실패'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/send-report", summary="리포트 알림 발송")
async def send_report_notification(
    report_type: str = Body("daily", description="리포트 타입 (daily, weekly)"),
    notification_types: List[str] = Body(["email"], description="알림 타입들")
):
    """최신 리포트를 지정된 채널로 발송합니다."""
    try:
        # 최신 리포트 조회 후 발송하는 로직
        # 여기서는 수동 리포트 생성 후 발송
        if report_type == "daily":
            report_result = scheduler.run_manual_report("daily")
            if report_result and not report_result.get('error'):
                notification_results = {}
                for ntype in notification_types:
                    if ntype == "email":
                        notification_results[ntype] = notification_service.send_daily_report_notifications(report_result).get('email', False)
                    elif ntype == "slack":
                        notification_results[ntype] = notification_service.send_daily_report_notifications(report_result).get('slack', False)
                
                return {
                    "success": True,
                    "message": "리포트 알림 발송 완료",
                    "notification_results": notification_results
                }
            else:
                raise HTTPException(status_code=500, detail="리포트 생성 실패")
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 리포트 타입입니다.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 텔레그램 봇 관련 엔드포인트
@router.post("/telegram/send", summary="텔레그램 메시지 발송")
async def send_telegram_message(
    message: str = Body(..., description="발송할 메시지"),
    chat_id: Optional[str] = Body(None, description="채팅 ID (선택사항)")
):
    """텔레그램으로 메시지를 발송합니다."""
    try:
        result = await telegram_bot.send_notification(message, chat_id)
        return {
            "success": result,
            "message": f"텔레그램 메시지 {'발송 성공' if result else '발송 실패'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/telegram/status", summary="텔레그램 봇 상태 확인")
async def get_telegram_bot_status():
    """텔레그램 봇의 상태를 확인합니다."""
    try:
        has_token = bool(telegram_bot.bot_token)
        return {
            "bot_configured": has_token,
            "bot_token_set": has_token,
            "status": "정상" if has_token else "설정 필요",
            "available_commands": [
                "/start", "/help", "/keyword", "/channel", "/influencer", 
                "/multi", "/daily", "/weekly", "/hot", "/trend"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 헬스체크
@router.get("/health", summary="시스템 상태 확인")
async def health_check():
    """시스템의 전반적인 상태를 확인합니다."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "투자 인사이트 분석 시스템이 정상 동작 중입니다."
    } 