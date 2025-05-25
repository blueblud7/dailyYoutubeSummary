#!/usr/bin/env python3
"""
AI 분석 기능 테스트
"""

from smart_subscription_reporter_v2 import SmartSubscriptionReporterV2
import openai

def test_ai_analysis():
    """AI 분석 기능 테스트"""
    
    print("🧪 AI 분석 기능 테스트 시작\n")
    
    # OpenAI 라이브러리 확인
    print(f"📚 OpenAI 버전: {openai.__version__}")
    
    # 리포터 초기화 테스트
    try:
        print("⚙️ 리포터 초기화 중...")
        reporter = SmartSubscriptionReporterV2()
        print("✅ 리포터 초기화 성공")
        
        # AI 분석 테스트 (올바른 파라미터)
        print("\n🤖 AI 분석 테스트 중...")
        test_result = reporter.analyze_content_with_ai(
            title='투자 관련 테스트 영상',
            transcript='''
            안녕하세요, 오늘은 주식 투자의 기본에 대해 알아보겠습니다.
            주식 투자를 할 때 가장 중요한 것은 분산 투자입니다.
            한 종목에만 집중하지 말고 여러 종목에 나누어 투자하는 것이 리스크를 줄이는 방법입니다.
            또한 장기적인 관점에서 투자하는 것이 중요합니다.
            단기적인 등락에 휘둘리지 말고 기업의 펀더멘털을 분석해야 합니다.
            특히 삼성전자, SK하이닉스 같은 대형주는 안정적인 투자처로 여겨집니다.
            하지만 최근 반도체 시장의 변화로 인해 주의깊게 지켜봐야 할 상황입니다.
            비트코인과 같은 암호화폐도 포트폴리오의 일부로 고려할 수 있지만 높은 변동성을 고려해야 합니다.
            부동산 시장도 금리 변화에 따라 크게 영향을 받고 있습니다.
            ''',
            channel_name='테스트 채널',
            video_id='test_video_001'
        )
        
        if test_result:
            print("✅ AI 분석 기능 정상 작동")
            print(f"\n📊 분석 결과 구성 요소:")
            for key, value in test_result.items():
                if value and str(value).strip():
                    print(f"   • {key}: ✅")
                    # 값이 너무 길면 일부만 표시
                    value_str = str(value)
                    if len(value_str) > 150:
                        print(f"     - {value_str[:150]}...")
                    else:
                        print(f"     - {value_str}")
                else:
                    print(f"   • {key}: ❌ (값 없음)")
            
            # 종합 요약 전체 표시
            if 'executive_summary' in test_result and test_result['executive_summary']:
                print(f"\n📝 종합 요약:")
                print(f"   {test_result['executive_summary']}")
            
            # 투자 시사점 표시
            if 'investment_implications' in test_result and test_result['investment_implications']:
                print(f"\n💰 투자 시사점:")
                print(f"   {test_result['investment_implications']}")
            
            # 핵심 키워드 표시
            if 'topics' in test_result and test_result['topics']:
                print(f"\n🏷️ 핵심 키워드:")
                print(f"   {test_result['topics']}")
                    
        else:
            print("❌ AI 분석 결과가 없습니다")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analysis() 