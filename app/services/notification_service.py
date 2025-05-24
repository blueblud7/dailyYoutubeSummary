import os
import json
import logging
import smtplib
import requests
from datetime import datetime
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

load_dotenv('config.env')

class NotificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 이메일 설정
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        # 슬랙 설정
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        
        # 텔레그램 설정
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # 수신자 목록
        self.email_recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")
        self.email_recipients = [email.strip() for email in self.email_recipients if email.strip()]
    
    def format_daily_report_email(self, report_data: Dict) -> tuple:
        """일일 리포트를 이메일 형식으로 포맷팅합니다."""
        
        date = report_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        daily_report = report_data.get('daily_report', {})
        trend_analysis = report_data.get('trend_analysis', {})
        statistics = report_data.get('statistics', {})
        
        subject = f"📈 투자 인사이트 일일 리포트 ({date})"
        
        # HTML 형식의 본문
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px; }}
                .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 5px; }}
                .highlight {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .stats {{ display: flex; justify-content: space-around; text-align: center; }}
                .stat-item {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .neutral {{ color: #6c757d; }}
                ul {{ padding-left: 20px; }}
                li {{ margin: 5px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding: 20px; background: #f1f3f4; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📈 투자 인사이트 일일 리포트</h1>
                <p>{date} ({datetime.now().strftime('%A')})</p>
            </div>
            
            <div class="section">
                <h2>📊 오늘의 핵심 요약</h2>
                <div class="highlight">
                    <strong>{daily_report.get('executive_summary', '요약 정보가 없습니다.')}</strong>
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 시장 하이라이트</h2>
                <ul>
        """
        
        for highlight in daily_report.get('market_highlights', []):
            html_body += f"<li>{highlight}</li>"
        
        html_body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>🔥 주요 동향</h2>
                <ul>
        """
        
        for development in daily_report.get('key_developments', []):
            html_body += f"<li>{development}</li>"
        
        # 시장 감정 표시
        sentiment = trend_analysis.get('market_sentiment', 0)
        if isinstance(sentiment, (int, float)):
            if sentiment > 0.1:
                sentiment_class = "positive"
                sentiment_text = f"긍정적 ({sentiment:.2f})"
                sentiment_emoji = "📈"
            elif sentiment < -0.1:
                sentiment_class = "negative"
                sentiment_text = f"부정적 ({sentiment:.2f})"
                sentiment_emoji = "📉"
            else:
                sentiment_class = "neutral"
                sentiment_text = f"중립적 ({sentiment:.2f})"
                sentiment_emoji = "➡️"
        else:
            sentiment_class = "neutral"
            sentiment_text = str(sentiment)
            sentiment_emoji = "📊"
        
        html_body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>💭 오늘의 시장 감정</h2>
                <div class="highlight">
                    <span class="{sentiment_class}"><strong>{sentiment_emoji} {sentiment_text}</strong></span>
                </div>
            </div>
            
            <div class="section">
                <h2>👀 주목할 포인트</h2>
                <ul>
        """
        
        for item in daily_report.get('watch_list', []):
            html_body += f"<li>{item}</li>"
        
        html_body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>⚠️ 위험 요소</h2>
                <ul>
        """
        
        for risk in daily_report.get('risk_alert', []):
            html_body += f"<li>{risk}</li>"
        
        html_body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>🔮 내일 전망</h2>
                <div class="highlight">
                    {daily_report.get('tomorrow_outlook', '전망 정보가 없습니다.')}
                </div>
            </div>
            
            <div class="section">
                <h2>✅ 액션 아이템</h2>
                <ul>
        """
        
        for action in daily_report.get('action_items', []):
            html_body += f"<li>{action}</li>"
        
        html_body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>📈 분석 통계</h2>
                <div class="stats">
                    <div class="stat-item">
                        <h3>{statistics.get('total_videos_analyzed', 0)}</h3>
                        <p>분석된 영상</p>
                    </div>
                    <div class="stat-item">
                        <h3>{statistics.get('total_channels', 0)}</h3>
                        <p>분석 채널</p>
                    </div>
                    <div class="stat-item">
                        <h3>{statistics.get('avg_sentiment', 0):.2f}</h3>
                        <p>평균 감정 점수</p>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 AI 투자 인사이트 분석 시스템</p>
                <p><small>이 리포트는 자동으로 생성되었습니다. • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
            </div>
        </body>
        </html>
        """
        
        return subject, html_body
    
    def format_weekly_report_email(self, report_data: Dict) -> tuple:
        """주간 리포트를 이메일 형식으로 포맷팅합니다."""
        
        period = report_data.get('period', '최근 1주')
        trend_analysis = report_data.get('trend_analysis', {})
        weekly_statistics = report_data.get('weekly_statistics', {})
        
        subject = f"📊 투자 인사이트 주간 리포트 ({period})"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; text-align: center; border-radius: 10px; }}
                .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #28a745; border-radius: 5px; }}
                .highlight {{ background: #d1ecf1; border: 1px solid #bee5eb; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .entity-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
                .entity-tag {{ background: #007bff; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.9em; }}
                ul {{ padding-left: 20px; }}
                li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 투자 인사이트 주간 리포트</h1>
                <p>{period}</p>
            </div>
            
            <div class="section">
                <h2>📝 주간 요약</h2>
                <div class="highlight">
                    <strong>{trend_analysis.get('summary', '주간 요약이 없습니다.')}</strong>
                </div>
            </div>
            
            <div class="section">
                <h2>🔥 핫 키워드 TOP 10</h2>
                <div class="entity-list">
        """
        
        for entity in weekly_statistics.get('top_entities', [])[:10]:
            html_body += f'<span class="entity-tag">{entity["entity"]} ({entity["count"]})</span>'
        
        html_body += f"""
                </div>
            </div>
            
            <div class="section">
                <h2>📈 감정 분포</h2>
                <ul>
                    <li>긍정적: {weekly_statistics.get('sentiment_distribution', {}).get('positive', 0)}개</li>
                    <li>중립적: {weekly_statistics.get('sentiment_distribution', {}).get('neutral', 0)}개</li>
                    <li>부정적: {weekly_statistics.get('sentiment_distribution', {}).get('negative', 0)}개</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>🎯 주요 테마</h2>
                <ul>
        """
        
        for theme in trend_analysis.get('key_themes', []):
            html_body += f"<li>{theme}</li>"
        
        html_body += f"""
                </ul>
            </div>
        </body>
        </html>
        """
        
        return subject, html_body
    
    def send_email(self, subject: str, html_body: str, recipients: List[str] = None) -> bool:
        """이메일을 발송합니다."""
        
        if not self.email_user or not self.email_password:
            self.logger.warning("이메일 설정이 없어 이메일 발송을 건너뜁니다.")
            return False
        
        if not recipients:
            recipients = self.email_recipients
        
        if not recipients:
            self.logger.warning("이메일 수신자가 설정되지 않았습니다.")
            return False
        
        try:
            # 이메일 메시지 작성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = ', '.join(recipients)
            
            # HTML 부분 추가
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                
                for recipient in recipients:
                    server.send_message(msg, to_addrs=[recipient])
                    self.logger.info(f"이메일 발송 완료: {recipient}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"이메일 발송 실패: {e}")
            return False
    
    def send_slack_message(self, message: str, channel: str = None) -> bool:
        """슬랙으로 메시지를 발송합니다."""
        
        if not self.slack_webhook_url:
            self.logger.warning("슬랙 설정이 없어 슬랙 발송을 건너뜁니다.")
            return False
        
        try:
            payload = {
                "text": message,
                "username": "Investment Insights Bot",
                "icon_emoji": ":chart_with_upwards_trend:"
            }
            
            if channel:
                payload["channel"] = channel
            
            response = requests.post(self.slack_webhook_url, json=payload)
            
            if response.status_code == 200:
                self.logger.info("슬랙 메시지 발송 완료")
                return True
            else:
                self.logger.error(f"슬랙 발송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"슬랙 발송 오류: {e}")
            return False
    
    def send_telegram_message(self, message: str) -> bool:
        """텔레그램으로 메시지를 발송합니다."""
        
        if not self.telegram_bot_token or not self.telegram_chat_id:
            self.logger.warning("텔레그램 설정이 없어 텔레그램 발송을 건너뜁니다.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                self.logger.info("텔레그램 메시지 발송 완료")
                return True
            else:
                self.logger.error(f"텔레그램 발송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"텔레그램 발송 오류: {e}")
            return False
    
    def format_slack_daily_report(self, report_data: Dict) -> str:
        """슬랙용 일일 리포트 메시지를 포맷팅합니다."""
        
        date = report_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        daily_report = report_data.get('daily_report', {})
        statistics = report_data.get('statistics', {})
        
        message = f"""
📈 *투자 인사이트 일일 리포트* ({date})

💡 *핵심 요약*
{daily_report.get('executive_summary', '요약 없음')}

📊 *오늘의 통계*
• 분석 영상: {statistics.get('total_videos_analyzed', 0)}개
• 분석 채널: {statistics.get('total_channels', 0)}개  
• 평균 감정: {statistics.get('avg_sentiment', 0):.2f}

🎯 *주요 포인트*
"""
        
        for i, highlight in enumerate(daily_report.get('market_highlights', [])[:3], 1):
            message += f"{i}. {highlight}\n"
        
        message += f"\n🔮 *내일 전망*\n{daily_report.get('tomorrow_outlook', '전망 없음')}"
        
        return message
    
    def send_daily_report_notifications(self, report_data: Dict) -> Dict[str, bool]:
        """일일 리포트를 모든 설정된 채널로 발송합니다."""
        
        results = {}
        
        try:
            # 이메일 발송
            if self.email_recipients:
                subject, html_body = self.format_daily_report_email(report_data)
                results['email'] = self.send_email(subject, html_body)
            
            # 슬랙 발송
            if self.slack_webhook_url:
                slack_message = self.format_slack_daily_report(report_data)
                results['slack'] = self.send_slack_message(slack_message)
            
            # 텔레그램 발송
            if self.telegram_bot_token and self.telegram_chat_id:
                telegram_message = self.format_slack_daily_report(report_data)  # 슬랙과 동일한 형식 사용
                results['telegram'] = self.send_telegram_message(telegram_message)
            
            self.logger.info(f"알림 발송 결과: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"알림 발송 중 오류: {e}")
            return {"error": str(e)}
    
    def send_weekly_report_notifications(self, report_data: Dict) -> Dict[str, bool]:
        """주간 리포트를 모든 설정된 채널로 발송합니다."""
        
        results = {}
        
        try:
            # 주간 리포트는 이메일로만 발송 (내용이 길어서)
            if self.email_recipients:
                subject, html_body = self.format_weekly_report_email(report_data)
                results['email'] = self.send_email(subject, html_body)
            
            # 슬랙에는 요약만 발송
            if self.slack_webhook_url:
                period = report_data.get('period', '최근 1주')
                summary = report_data.get('trend_analysis', {}).get('summary', '주간 요약 없음')
                slack_message = f"📊 *주간 리포트 생성 완료* ({period})\n\n{summary}\n\n📧 자세한 내용은 이메일을 확인해주세요."
                results['slack'] = self.send_slack_message(slack_message)
            
            return results
            
        except Exception as e:
            self.logger.error(f"주간 리포트 알림 발송 중 오류: {e}")
            return {"error": str(e)} 