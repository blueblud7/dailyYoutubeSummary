# 투자 인사이트 분석 시스템

유튜브 콘텐츠를 분석하여 투자 인사이트를 제공하는 자동화 시스템입니다.

## 🎯 주요 기능

### 1. 데이터 수집
- **유튜브 채널 모니터링**: 특정 채널의 최신 비디오 자동 수집
- **키워드 기반 검색**: 투자 관련 키워드로 비디오 검색 및 수집
- **자막 수집**: 수동/자동 생성 자막 모두 지원
- **메타데이터 저장**: 조회수, 좋아요 수, 댓글 수 등 상세 정보 저장

### 2. AI 분석
- **GPT-4o-mini 활용**: 고품질 투자 인사이트 분석
- **감정 분석**: 시장 전망에 대한 긍정/부정 감정 점수
- **중요도 평가**: 콘텐츠의 투자적 중요도 자동 평가
- **엔티티 추출**: 언급된 기업, 인물, 경제지표 자동 식별

### 3. 리포트 생성
- **일일 리포트**: 매일 투자 인사이트 요약
- **주간 리포트**: 주간 트렌드 분석 및 전망
- **관점 비교**: 특정 주제에 대한 채널별 견해 비교
- **자동 분배**: 스케줄에 따른 자동 리포트 생성

### 4. 관점 비교 분석
- **다각도 분석**: 동일 주제에 대한 여러 전문가 견해 비교
- **합의점 식별**: 전문가들이 동의하는 부분 추출
- **이견 분석**: 상반된 의견과 그 근거 분석

### 5. 텔레그램 봇 기능 🤖
- **양방향 상호작용**: 실시간 키워드 분석 요청
- **개인화 리포트**: 원하는 키워드/채널/인물 맞춤 분석
- **즉시 피드백**: 5초 내 분석 결과 제공
- **자연어 지원**: "오늘 주식 시장 어때?" 같은 자연어 질문
- **모바일 최적화**: 언제 어디서나 스마트폰으로 접근

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

`config.env.example`을 참고하여 환경변수를 설정하세요:

```bash
# config.env 파일 생성
cp config.env.example config.env

# 필수 설정 값들
YOUTUBE_API_KEYS=your_api_key_1,your_api_key_2,your_api_key_3
OPENAI_API_KEY=your_openai_api_key
```

### 3. 애플리케이션 실행

```bash
# 웹 API 서버 실행
python main.py

# 스케줄러 실행 (별도 터미널)
python app/services/scheduler.py

# 텔레그램 봇 실행 (별도 터미널)
python run_telegram_bot.py
```

## 📊 API 사용 가이드

### 기본 URL
```
http://localhost:8000
```

### 주요 엔드포인트

#### 1. 채널 추가
```bash
curl -X POST "http://localhost:8000/api/v1/collection/channels" \
-H "Content-Type: application/json" \
-d '{
  "channel_ids": [
    "UC7RQon_YwCnp_LbPtEwW65w",
    "UCMeDFTyb74jGWBb6nWvq2MA"
  ]
}'
```

#### 2. 키워드 추가
```bash
curl -X POST "http://localhost:8000/api/v1/collection/keywords" \
-H "Content-Type: application/json" \
-d '{
  "keywords": ["투자", "주식", "부동산", "경제"],
  "category": "투자"
}'
```

#### 3. 데이터 수집 실행
```bash
curl -X POST "http://localhost:8000/api/v1/collection/run" \
-H "Content-Type: application/json" \
-d '{
  "channel_ids": ["UC7RQon_YwCnp_LbPtEwW65w"],
  "keywords": ["투자", "주식"],
  "days_back": 1
}'
```

#### 4. 일일 리포트 생성
```bash
curl -X POST "http://localhost:8000/api/v1/reports/daily" \
-H "Content-Type: application/json" \
-d '{
  "keywords": ["투자", "주식", "부동산"]
}'
```

#### 5. 관점 비교 분석
```bash
curl -X POST "http://localhost:8000/api/v1/reports/perspective" \
-H "Content-Type: application/json" \
-d '{
  "topic": "금리 인하의 영향",
  "keywords": ["금리", "인하", "부동산", "주식"],
  "days_back": 7
}'
```

## 🤖 텔레그램 봇 사용 가이드

### 빠른 시작
1. 텔레그램에서 봇과 대화 시작
2. `/start` 명령어로 환영 메시지 확인
3. `/help` 명령어로 사용법 확인

### 주요 명령어

#### 📊 분석 명령어
```
/keyword 주식        # 주식 키워드 분석
/channel 체슬리TV    # 특정 채널 분석
/influencer 홍춘욱   # 인물 언급 분석
/multi 주식 체슬리TV 홍춘욱  # 다차원 종합 분석
```

#### 📈 리포트 명령어
```
/daily              # 오늘의 일일 리포트
/weekly             # 주간 종합 리포트
/hot                # 현재 핫한 키워드 TOP 10
/trend              # 최근 3일 트렌드 분석
```

#### 💬 자연어 지원
```
"오늘 주식 시장 어때?"     # 주식 관련 분석
"부동산 소식 알려줘"       # 부동산 관련 분석
"핫한 키워드 보여줘"       # 인기 키워드 분석
```

### 등록된 채널들
- 체슬리TV, Understanding, 오종태의 투자병법
- 김준송TV, 소수몽키, Mkinvest
- 한경 글로벌마켓, 홍춘욱의 경제강의노트

### 등록된 인물들
- 오건영, 박세익, 김준송, 오종태
- 성상현, 문홍철, 홍춘욱, 이선엽, 윤지호

### 설정 방법
자세한 텔레그램 봇 설정 방법은 다음 문서를 참고하세요:
- [텔레그램 봇 설정 가이드](./telegram_bot_setup_guide.md)
- [빠른 시작 가이드](./TELEGRAM_BOT_QUICK_START.md)

## 🗂️ 프로젝트 구조

```
summary_news/
├── app/
│   ├── models/
│   │   └── database.py              # 데이터베이스 모델
│   ├── services/
│   │   ├── youtube_service.py       # YouTube API 서비스
│   │   ├── analysis_service.py      # AI 분석 서비스
│   │   ├── data_collector.py        # 데이터 수집 조율
│   │   ├── report_service.py        # 리포트 생성
│   │   ├── personalized_report_service.py # 개인화 리포트
│   │   ├── telegram_bot_service.py  # 텔레그램 봇 서비스
│   │   ├── notification_service.py  # 알림 서비스
│   │   └── scheduler.py             # 스케줄러
│   └── api/
│       └── routes.py                # API 엔드포인트
├── data/                            # 데이터 파일
├── reports/                         # 생성된 리포트
├── tests/                           # 테스트 파일들
├── main.py                          # 메인 애플리케이션
├── run_telegram_bot.py              # 텔레그램 봇 실행
├── requirements.txt                 # 의존성
├── config.env.example              # 환경변수 예시
├── telegram_bot_setup_guide.md     # 텔레그램 봇 설정 가이드
├── TELEGRAM_BOT_QUICK_START.md     # 텔레그램 봇 빠른 시작
└── README.md
```

## 🔧 설정 및 커스터마이징

### 1. 분석 대상 채널 추가

기본 채널은 `app/services/scheduler.py`의 `default_channels`에서 설정할 수 있습니다:

```python
self.default_channels = [
    "UC7RQon_YwCnp_LbPtEwW65w",  # 슈카월드
    "UCMeDFTyb74jGWBb6nWvq2MA",  # 리더스의 눈
    "UCIFBHMwAT8wJBwxkLwNBbLg",  # 한국경제TV
    # 추가할 채널 ID들...
]
```

### 2. 분석 키워드 설정

기본 키워드도 동일한 파일에서 설정 가능합니다:

```python
self.default_keywords = [
    "투자", "주식", "부동산", "경제", "금리", "인플레이션",
    "달러", "환율", "코스피", "나스닥", "반도체", "AI",
    # 추가 키워드들...
]
```

### 3. 스케줄 조정

데이터 수집 및 리포트 생성 스케줄을 변경하려면:

```python
# 일일 데이터 수집: 매일 오전 6시
schedule.every().day.at("06:00").do(self.daily_collection_task)

# 일일 리포트 생성: 매일 오전 9시
schedule.every().day.at("09:00").do(self.daily_report_task)

# 주간 리포트 생성: 매주 월요일 오전 10시
schedule.every().monday.at("10:00").do(self.weekly_report_task)
```

## 📈 사용 시나리오

### 시나리오 1: 일일 모니터링
1. 매일 오전 6시에 자동으로 새로운 비디오 수집
2. 오전 9시에 일일 투자 인사이트 리포트 생성
3. 주요 이슈와 시장 전망을 요약하여 제공

### 시나리오 2: 특정 이슈 추적
1. 특정 키워드(예: "금리 인상")에 대한 비디오 검색
2. 관련 채널들의 견해 수집 및 분석
3. 찬반 의견과 근거를 정리한 비교 리포트 생성

### 시나리오 3: 주간 트렌드 분석
1. 주간 단위로 축적된 데이터 종합 분석
2. 주요 투자 테마와 핫 토픽 식별
3. 시장 감정 변화와 전문가 합의 여부 파악

## 🎛️ API 문서

서버 실행 후 다음 URL에서 상세한 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 대시보드 활용

### 시스템 상태 확인
```bash
curl http://localhost:8000/api/v1/collection/status
```

### 리포트 히스토리 조회
```bash
curl http://localhost:8000/api/v1/reports/history?report_type=daily&limit=10
```

### 트렌드 분석 조회
```bash
curl "http://localhost:8000/api/v1/analysis/trends?keywords=투자&keywords=주식&days_back=7"
```

## ⚠️ 주의사항

1. **API 할당량**: YouTube Data API v3의 일일 할당량을 확인하고 여러 API 키를 준비하세요
2. **토큰 비용**: OpenAI API 사용량에 따른 비용이 발생할 수 있습니다
3. **저작권**: 수집된 콘텐츠의 저작권을 준수하여 사용하세요
4. **데이터 보안**: 민감한 API 키는 환경변수로 관리하고 공개하지 마세요

## 🔮 향후 개선 계획

- [ ] 웹 대시보드 UI 개발
- [ ] 실시간 알림 기능 추가
- [ ] 더 많은 소스 (팟캐스트, 뉴스 등) 지원
- [ ] 포트폴리오 추천 기능
- [ ] 모바일 앱 개발

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 등록해 주세요.

---

**투자 인사이트 분석 시스템**으로 더 스마트한 투자 결정을 내리세요! 🚀📊 