# 📱 텔레그램 봇 설정 가이드

양방향 개인화된 투자 인사이트 리포트를 위한 텔레그램 봇 설정 방법입니다.

## 🤖 1. 텔레그램 봇 생성

### 1.1 BotFather에서 봇 생성
```
1. 텔레그램에서 @BotFather 검색
2. /newbot 명령 입력
3. 봇 이름 설정 (예: "투자 인사이트 분석봇")
4. 봇 사용자명 설정 (예: "investment_insight_bot")
5. 받은 토큰을 저장 (예: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)
```

### 1.2 봇 설정
```
/setdescription - 봇 설명 설정
/setabouttext - 봇 정보 설정
/setcommands - 명령어 목록 설정
```

## ⚙️ 2. 환경 설정

### 2.1 config.env 파일 설정
```bash
# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=your-chat-id
```

### 2.2 채팅 ID 확인 방법
```
1. 생성한 봇과 대화 시작
2. @userinfobot에게 /start 명령
3. 표시되는 Chat ID를 복사
4. config.env에 TELEGRAM_CHAT_ID로 설정
```

## 📦 3. 패키지 설치

```bash
pip install python-telegram-bot==20.7
```

## 🚀 4. 봇 실행

### 4.1 테스트 실행
```bash
python test_telegram_bot.py
```

### 4.2 봇 실행
```bash
python run_telegram_bot.py
```

## 📱 5. 사용 가능한 명령어

### 5.1 기본 명령어
- `/start` - 봇 시작 및 환영 메시지
- `/help` - 상세 사용법 안내

### 5.2 분석 명령어
- `/keyword [키워드]` - 특정 키워드 분석
  ```
  /keyword 주식
  /keyword 부동산
  /keyword 금리
  ```

- `/channel [채널명]` - 특정 채널 분석
  ```
  /channel 체슬리TV
  /channel Understanding
  ```

- `/influencer [인물명]` - 인물 언급 분석
  ```
  /influencer 박세익
  /influencer 오건영
  ```

### 5.3 종합 리포트
- `/daily` - 오늘의 일일 리포트
- `/weekly` - 주간 종합 리포트

### 5.4 트렌드 분석
- `/hot` - 현재 핫한 키워드 TOP 10
- `/trend` - 최근 3일 트렌드 분석

### 5.5 다차원 분석
- `/multi [키워드] [채널] [인물]` - 종합 분석
  ```
  /multi 주식 체슬리TV 박세익
  /multi 부동산 체슬리TV
  ```

### 5.6 자연어 질문
일반 메시지로도 질문 가능:
```
"오늘 주식 시장 어때?"
"부동산 소식 알려줘"
"핫한 키워드 보여줘"
```

## 💡 6. 실제 사용 예시

### 6.1 키워드 분석 예시
```
사용자: /keyword 주식
봇: 🔍 '주식' 키워드 분석 리포트

📊 분석 통계
• 분석 수: 18개
• 채널 수: 2개
• 평균 감정: 0.19

😊 감정 분포
• 긍정: 12개
• 중립: 4개
• 부정: 2개

🎯 주요 분석 영상 (상위 3개)
1. 미국 증시 전망과 투자 전략...
   📺 체슬리TV | 중요도: 0.92
```

### 6.2 일일 리포트 예시
```
사용자: /daily
봇: 📊 오늘의 투자 인사이트

💡 핵심 요약
오늘은 미국 증시 상승과 함께 국내 주식시장도...

📈 오늘의 통계
• 분석 영상: 25개
• 분석 채널: 7개
• 평균 감정: 0.15

🎯 주요 하이라이트
• 엔비디아 실적 발표 앞두고 반도체주 강세
• 금리 인하 기대감으로 성장주 부각
• 부동산 정책 변화 관련 논의 증가
```

## 🔧 7. 고급 설정

### 7.1 명령어 목록 설정
BotFather에서 `/setcommands` 후 다음 입력:
```
start - 봇 시작
help - 사용법 안내
keyword - 키워드 분석
channel - 채널 분석
influencer - 인플루언서 언급 분석
daily - 일일 리포트
weekly - 주간 리포트
hot - 핫한 키워드
trend - 트렌드 분석
multi - 다차원 분석
```

### 7.2 자동 알림 설정
scheduler.py에서 텔레그램 자동 알림도 설정 가능:
```python
# 매일 오전 9시에 일일 리포트 자동 발송
schedule.every().day.at("09:00").do(send_daily_telegram_report)
```

## 🛠️ 8. 문제 해결

### 8.1 일반적인 오류
- **"Unauthorized"**: 봇 토큰이 잘못됨
- **"Chat not found"**: 채팅 ID가 잘못됨
- **"Bad Request"**: 메시지 형식 오류

### 8.2 로그 확인
```bash
tail -f telegram_bot.log
```

### 8.3 테스트 명령
```bash
# 봇 상태 확인
python test_telegram_bot.py

# API를 통한 상태 확인
curl http://localhost:8000/telegram/status
```

## 🎯 9. 장점

### 9.1 즉시성
- 원하는 키워드 입력 즉시 분석 결과 수신
- 실시간 투자 인사이트 확인

### 9.2 개인화
- 관심 키워드별 맞춤 분석
- 특정 채널, 인플루언서 집중 분석

### 9.3 편의성
- 이메일보다 빠른 접근성
- 모바일에서 간편한 사용
- 자연어 질문 지원

이제 텔레그램으로 언제든지 "/keyword 주식" 같은 명령어를 보내면 실시간으로 맞춤형 투자 인사이트를 받을 수 있습니다! 🚀 