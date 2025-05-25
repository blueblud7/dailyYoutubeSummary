#!/usr/bin/env python3

from app.services.personalized_report_service import PersonalizedReportService
from app.services.notification_service import NotificationService
from app.models.database import SessionLocal
import json

def test_personalized_reports():
    """개인화된 리포트 시스템을 테스트합니다."""
    
    print("🎯 개인화된 리포트 시스템 테스트")
    print("="*50)
    
    db = SessionLocal()
    personalized_service = PersonalizedReportService()
    notification_service = NotificationService()
    
    try:
        # 1. 키워드 집중 리포트 테스트
        print("\n🔍 키워드 집중 리포트 테스트...")
        keyword_report = personalized_service.generate_keyword_focused_report(
            db, "주식", days_back=7
        )
        
        if keyword_report.get('message'):
            print(f"   ℹ️  {keyword_report['message']}")
        else:
            print(f"   ✅ 키워드 '{keyword_report['keyword']}' 리포트 생성 완료")
            print(f"   📊 분석 수: {keyword_report['statistics']['total_analyses']}개")
            print(f"   📺 채널 수: {keyword_report['statistics']['total_channels']}개")
            print(f"   😊 평균 감정: {keyword_report['statistics']['avg_sentiment']:.2f}")
        
        # 2. 채널 집중 리포트 테스트
        print("\n📺 채널 집중 리포트 테스트...")
        channel_report = personalized_service.generate_channel_focused_report(
            db, "체슬리TV", days_back=7
        )
        
        if channel_report.get('message'):
            print(f"   ℹ️  {channel_report['message']}")
        else:
            print(f"   ✅ 채널 '{channel_report['channel']}' 리포트 생성 완료")
            print(f"   📹 비디오 수: {channel_report['statistics']['total_videos']}개")
            print(f"   📊 분석 수: {channel_report['statistics']['total_analyses']}개")
            print(f"   👥 구독자: {channel_report['subscriber_count']:,}명")
        
        # 3. 인플루언서 언급 분석 테스트
        print("\n👤 인플루언서 언급 분석 테스트...")
        influencer_report = personalized_service.generate_influencer_focused_report(
            db, "박세익", days_back=7
        )
        
        if influencer_report.get('message'):
            print(f"   ℹ️  {influencer_report['message']}")
        else:
            print(f"   ✅ 인플루언서 '{influencer_report['influencer']}' 리포트 생성 완료")
            print(f"   💬 언급 수: {influencer_report['statistics']['total_mentions']}개")
            print(f"   😊 평균 감정: {influencer_report['statistics']['avg_sentiment']:.2f}")
            print(f"   📺 언급 채널: {influencer_report['statistics']['channels_mentioned']}개")
        
        # 4. 다차원 리포트 테스트
        print("\n📊 다차원 리포트 테스트...")
        multi_report = personalized_service.generate_multi_dimension_report(
            db,
            keywords=["주식", "투자"],
            channels=["체슬리TV"],
            influencers=["박세익"],
            days_back=7
        )
        
        if multi_report:
            print(f"   ✅ 다차원 리포트 생성 완료")
            print(f"   📅 기간: {multi_report['period']}")
            
            sections = multi_report['sections']
            if 'keywords' in sections:
                print(f"   🔍 키워드 섹션: {len(sections['keywords'])}개")
            if 'channels' in sections:
                print(f"   📺 채널 섹션: {len(sections['channels'])}개")
            if 'influencers' in sections:
                print(f"   👤 인플루언서 섹션: {len(sections['influencers'])}개")
        
        # 5. 알림 테스트
        print("\n📧 알림 시스템 테스트...")
        
        # 키워드 리포트가 있으면 알림 테스트
        if keyword_report and not keyword_report.get('message'):
            # 슬랙 알림 테스트
            slack_result = personalized_service.send_personalized_notification(
                keyword_report, "slack"
            )
            print(f"   📱 슬랙 알림: {'성공' if slack_result else '실패'}")
            
            # 이메일 알림 테스트 (설정이 있는 경우에만)
            email_result = personalized_service.send_personalized_notification(
                keyword_report, "email"
            )
            print(f"   📧 이메일 알림: {'성공' if email_result else '실패'}")
        
        # 6. 알림 서비스 직접 테스트
        print("\n🧪 알림 서비스 직접 테스트...")
        
        # 테스트 이메일 (설정이 있는 경우에만)
        test_email_result = notification_service.send_email(
            "🧪 개인화된 리포트 시스템 테스트",
            "<h2>테스트 메시지</h2><p>개인화된 리포트 시스템이 정상적으로 동작합니다!</p>"
        )
        print(f"   📧 테스트 이메일: {'전송 성공' if test_email_result else '전송 실패 (설정 확인 필요)'}")
        
        # 테스트 슬랙 메시지 (설정이 있는 경우에만)
        test_slack_result = notification_service.send_slack_message(
            "🧪 *개인화된 리포트 시스템 테스트*\n개인화된 리포트 시스템이 정상적으로 동작합니다!"
        )
        print(f"   📱 테스트 슬랙: {'전송 성공' if test_slack_result else '전송 실패 (설정 확인 필요)'}")
        
        print(f"\n✅ 개인화된 리포트 시스템 테스트 완료!")
        
        # 결과 요약
        print(f"\n📋 테스트 결과 요약:")
        print(f"- 키워드 리포트: {'성공' if not keyword_report.get('message') else '데이터 없음'}")
        print(f"- 채널 리포트: {'성공' if not channel_report.get('message') else '데이터 없음'}")
        print(f"- 인플루언서 리포트: {'성공' if not influencer_report.get('message') else '데이터 없음'}")
        print(f"- 다차원 리포트: {'성공' if multi_report else '실패'}")
        print(f"- 알림 시스템: 설정 확인 필요")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

def test_notification_settings():
    """알림 설정을 확인합니다."""
    
    print("\n🔧 알림 설정 확인")
    print("="*30)
    
    notification_service = NotificationService()
    
    # 이메일 설정 확인
    has_email = bool(notification_service.email_user and notification_service.email_password)
    print(f"📧 이메일 설정: {'✅ 완료' if has_email else '❌ 미설정'}")
    if has_email:
        print(f"   - SMTP 서버: {notification_service.smtp_server}")
        print(f"   - 발송자: {notification_service.email_user}")
        print(f"   - 수신자: {len(notification_service.email_recipients)}명")
    
    # 슬랙 설정 확인
    has_slack = bool(notification_service.slack_webhook_url)
    print(f"📱 슬랙 설정: {'✅ 완료' if has_slack else '❌ 미설정'}")
    
    # 텔레그램 설정 확인
    has_telegram = bool(notification_service.telegram_bot_token and notification_service.telegram_chat_id)
    print(f"📟 텔레그램 설정: {'✅ 완료' if has_telegram else '❌ 미설정'}")
    
    return {
        'email': has_email,
        'slack': has_slack,
        'telegram': has_telegram
    }

if __name__ == "__main__":
    # 알림 설정 확인
    settings = test_notification_settings()
    
    # 개인화된 리포트 테스트
    test_personalized_reports()
    
    # 설정 가이드
    if not any(settings.values()):
        print(f"\n💡 알림 설정 가이드:")
        print(f"config.env 파일에 다음 설정을 추가하세요:")
        print(f"""
# 이메일 설정
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com

# 슬랙 설정  
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# 텔레그램 설정
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
        """) 