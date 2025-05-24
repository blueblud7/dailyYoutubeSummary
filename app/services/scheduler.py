import schedule
import time
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, create_tables
from app.services.data_collector import DataCollector
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService
from app.services.personalized_report_service import PersonalizedReportService
import os
from dotenv import load_dotenv

load_dotenv('config.env')

class TaskScheduler:
    def __init__(self):
        self.data_collector = DataCollector()
        self.report_service = ReportService()
        self.notification_service = NotificationService()
        self.personalized_report_service = PersonalizedReportService()
        self.logger = logging.getLogger(__name__)
        
        # 기본 설정
        self.default_channels = [
            "UCXST0Hq6CAmG0dmo3jgrlEw",  # 체슬리TV
            "UCIUni4ScRp4mqPXsxy62L5w",  # 언더스탠딩 : 세상의 모든 지식
            "UCSVtOfGvhtz2QosSIM_3WoQ",  # 오종태의 투자병법
            "UC18feVzOBjtLU9trm8A788g",  # 김준송TV
            "UCC3yfxS5qC6PCwDzetUuEWg",  # 소수몽키
            "UCr29QUcfio3Y_EX0T4DHCJQ",  # Mkinvest
            "UCWskYkV4c4S9D__rsfOl2JA",  # 한경 글로벌마켓
        ]
        
        self.default_keywords = [
            "투자", "주식", "부동산", "경제", "금리", "인플레이션",
            "달러", "환율", "코스피", "나스닥", "반도체", "AI",
            "테슬라", "삼성전자", "미국주식", "한국주식"
        ]
        
        # 개인화 리포트 설정
        self.personalized_keywords = ["주식", "부동산", "금리"]
        self.personalized_channels = ["체슬리TV", "Understanding"]
        self.personalized_influencers = ["오건영", "박세익"]
    
    def daily_collection_task(self):
        """일일 데이터 수집 작업을 실행합니다."""
        self.logger.info("일일 데이터 수집 작업 시작")
        
        try:
            db = SessionLocal()
            
            # 데이터 수집 실행
            result = self.data_collector.run_daily_collection(
                channel_ids=self.default_channels,
                keywords=self.default_keywords,
                db=db
            )
            
            self.logger.info(f"데이터 수집 완료: {result}")
            
        except Exception as e:
            self.logger.error(f"데이터 수집 중 오류 발생: {e}")
        finally:
            db.close()
    
    def daily_report_task(self):
        """일일 리포트 생성 및 알림 발송 작업을 실행합니다."""
        self.logger.info("일일 리포트 생성 작업 시작")
        
        try:
            db = SessionLocal()
            
            # 일일 리포트 생성
            report = self.report_service.generate_daily_report(
                db=db,
                keywords=self.default_keywords
            )
            
            self.logger.info(f"일일 리포트 생성 완료: {report.get('report_id')}")
            
            # 알림 발송
            if report and not report.get('error'):
                notification_results = self.notification_service.send_daily_report_notifications(report)
                self.logger.info(f"일일 리포트 알림 발송 결과: {notification_results}")
            
        except Exception as e:
            self.logger.error(f"일일 리포트 생성 중 오류 발생: {e}")
        finally:
            db.close()
    
    def personalized_daily_report_task(self):
        """개인화된 일일 리포트 생성 작업을 실행합니다."""
        self.logger.info("개인화된 일일 리포트 생성 작업 시작")
        
        try:
            db = SessionLocal()
            
            # 키워드별 개인화 리포트 생성
            for keyword in self.personalized_keywords:
                report = self.personalized_report_service.generate_keyword_focused_report(
                    db, keyword, days_back=1
                )
                
                if report and not report.get('message'):
                    self.personalized_report_service.send_personalized_notification(report, "slack")
                    self.logger.info(f"'{keyword}' 키워드 일일 리포트 완료")
            
            # 다차원 리포트 생성 (주요 키워드만)
            multi_report = self.personalized_report_service.generate_multi_dimension_report(
                db, 
                keywords=self.personalized_keywords[:2],  # 상위 2개 키워드만
                channels=self.personalized_channels[:2],  # 상위 2개 채널만
                days_back=1
            )
            
            if multi_report:
                self.personalized_report_service.send_personalized_notification(multi_report, "email")
                self.logger.info("다차원 개인화 일일 리포트 완료")
            
        except Exception as e:
            self.logger.error(f"개인화된 일일 리포트 생성 중 오류 발생: {e}")
        finally:
            db.close()
    
    def weekly_report_task(self):
        """주간 리포트 생성 및 알림 발송 작업을 실행합니다."""
        self.logger.info("주간 리포트 생성 작업 시작")
        
        try:
            db = SessionLocal()
            
            # 주간 리포트 생성
            report = self.report_service.generate_weekly_report(
                db=db,
                keywords=self.default_keywords
            )
            
            self.logger.info(f"주간 리포트 생성 완료: {report.get('report_id')}")
            
            # 알림 발송
            if report and not report.get('error'):
                notification_results = self.notification_service.send_weekly_report_notifications(report)
                self.logger.info(f"주간 리포트 알림 발송 결과: {notification_results}")
            
        except Exception as e:
            self.logger.error(f"주간 리포트 생성 중 오류 발생: {e}")
        finally:
            db.close()
    
    def setup_schedule(self):
        """스케줄을 설정합니다."""
        
        # 일일 데이터 수집: 매일 오전 6시
        schedule.every().day.at("06:00").do(self.daily_collection_task)
        
        # 일일 리포트 생성: 매일 오전 9시
        schedule.every().day.at("09:00").do(self.daily_report_task)
        
        # 개인화된 일일 리포트: 매일 오전 9시 30분
        schedule.every().day.at("09:30").do(self.personalized_daily_report_task)
        
        # 주간 리포트 생성: 매주 월요일 오전 10시
        schedule.every().monday.at("10:00").do(self.weekly_report_task)
        
        self.logger.info("스케줄 설정 완료")
        self.logger.info("- 일일 데이터 수집: 매일 06:00")
        self.logger.info("- 일일 리포트 생성: 매일 09:00")
        self.logger.info("- 개인화된 일일 리포트: 매일 09:30")
        self.logger.info("- 주간 리포트 생성: 매주 월요일 10:00")
    
    def run_scheduler(self):
        """스케줄러를 실행합니다."""
        self.logger.info("스케줄러 시작")
        
        # 데이터베이스 테이블 생성
        create_tables()
        
        # 스케줄 설정
        self.setup_schedule()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 확인
            except KeyboardInterrupt:
                self.logger.info("스케줄러 종료")
                break
            except Exception as e:
                self.logger.error(f"스케줄러 오류: {e}")
                time.sleep(60)
    
    def run_manual_collection(self, channels: List[str] = None, 
                            keywords: List[str] = None):
        """수동으로 데이터 수집을 실행합니다."""
        self.logger.info("수동 데이터 수집 시작")
        
        channels = channels or self.default_channels
        keywords = keywords or self.default_keywords
        
        try:
            db = SessionLocal()
            
            result = self.data_collector.run_daily_collection(
                channel_ids=channels,
                keywords=keywords,
                db=db
            )
            
            self.logger.info(f"수동 데이터 수집 완료: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"수동 데이터 수집 중 오류 발생: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def run_manual_report(self, report_type: str = "daily", 
                         keywords: List[str] = None):
        """수동으로 리포트를 생성합니다."""
        self.logger.info(f"수동 {report_type} 리포트 생성 시작")
        
        keywords = keywords or self.default_keywords
        
        try:
            db = SessionLocal()
            
            if report_type == "daily":
                report = self.report_service.generate_daily_report(
                    db=db, keywords=keywords
                )
            elif report_type == "weekly":
                report = self.report_service.generate_weekly_report(
                    db=db, keywords=keywords
                )
            else:
                raise ValueError(f"지원하지 않는 리포트 타입: {report_type}")
            
            self.logger.info(f"수동 {report_type} 리포트 생성 완료")
            return report
            
        except Exception as e:
            self.logger.error(f"수동 리포트 생성 중 오류 발생: {e}")
            return {"error": str(e)}
        finally:
            db.close()

# 스케줄러 인스턴스
scheduler = TaskScheduler()

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    # 스케줄러 실행
    scheduler.run_scheduler() 