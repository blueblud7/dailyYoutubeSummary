# 🚀 투자 인사이트 분석 시스템 설정 가이드

## 📋 사전 준비사항

### 1. 필수 API 키 준비
- **YouTube Data API v3 키** (여러 개 권장)
- **OpenAI API 키** (GPT-4o-mini 사용)
- **텔레그램 봇 토큰** (BotFather에서 생성)

### 2. 시스템 요구사항
- Python 3.8+
- pip 패키지 관리자
- Git

## 🔧 설치 및 설정

### 1단계: 프로젝트 클론
```bash
git clone https://github.com/blueblud7/dailyYoutubeSummary.git
cd dailyYoutubeSummary
```

### 2단계: 가상환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3단계: 의존성 설치
```bash
pip install -r requirements.txt
```

### 4단계: 환경변수 설정
```bash
# 설정 파일 복사
cp config.env.example config.env

# config.env 파일 편집
nano config.env  # 또는 선호하는 에디터 사용
```

#### config.env 필수 설정 항목:
```env
# YouTube API 키들 (여러 개 사용 권장)
YOUTUBE_API_KEYS=your_api_key_1,your_api_key_2,your_api_key_3

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key

# 텔레그램 봇 설정 (선택사항)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 5단계: 데이터베이스 초기화
```bash
# 시스템 테스트 (자동으로 DB 생성됨)
python test_system.py
```

## 🤖 텔레그램 봇 설정 (선택사항)

### 1. 봇 생성
1. 텔레그램에서 @BotFather 검색
2. `/newbot` 명령어 실행
3. 봇 이름과 사용자명 설정
4. 봇 토큰 복사

### 2. 채팅 ID 확인
1. 생성된 봇과 대화 시작
2. `/start` 메시지 전송
3. 다음 URL 방문하여 chat_id 확인:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

### 3. 봇 실행
```bash
python run_telegram_bot.py
```

자세한 텔레그램 봇 설정은 [telegram_bot_setup_guide.md](./telegram_bot_setup_guide.md)를 참고하세요.

## 🚀 시스템 실행

### 기본 실행 (웹 API)
```bash
python main.py
```
- API 문서: http://localhost:8000/docs

### 전체 시스템 실행
```bash
# 터미널 1: 웹 API 서버
python main.py

# 터미널 2: 스케줄러 (자동 데이터 수집)
python app/services/scheduler.py

# 터미널 3: 텔레그램 봇 (선택사항)
python run_telegram_bot.py
```

## 🔍 시스템 테스트

### 1. 기본 시스템 테스트
```bash
python test_system.py
```

### 2. 텔레그램 봇 테스트
```bash
python test_telegram_bot.py
```

### 3. API 테스트
```bash
# 서버 실행 후
curl http://localhost:8000/api/v1/collection/status
```

## 📝 추가 설정

### 채널 추가
등록할 YouTube 채널들을 `app/services/scheduler.py`에서 설정:
```python
self.default_channels = [
    "UC_channel_id_1",
    "UC_channel_id_2",
    # 추가 채널들...
]
```

### 키워드 설정
분석할 키워드들도 동일 파일에서 설정:
```python
self.default_keywords = [
    "투자", "주식", "부동산", "경제",
    # 추가 키워드들...
]
```

## 🎯 빠른 시작 체크리스트

- [ ] Python 3.8+ 설치
- [ ] 프로젝트 클론
- [ ] 가상환경 생성 및 활성화
- [ ] 의존성 설치 (`pip install -r requirements.txt`)
- [ ] YouTube API 키 발급
- [ ] OpenAI API 키 발급
- [ ] `config.env` 파일 설정
- [ ] 시스템 테스트 실행 (`python test_system.py`)
- [ ] 웹 서버 실행 (`python main.py`)
- [ ] [선택] 텔레그램 봇 설정 및 실행

## 🆘 문제 해결

### 자주 발생하는 문제들:

1. **YouTube API 할당량 초과**
   - 여러 API 키 사용
   - `config.env`에 여러 키를 콤마로 구분하여 입력

2. **OpenAI API 오류**
   - API 키 확인
   - 계정 잔액 확인

3. **텔레그램 봇이 응답하지 않음**
   - 봇 토큰 확인
   - 채팅 ID 확인
   - 봇이 실행 중인지 확인

4. **데이터베이스 오류**
   - 기존 DB 파일 삭제 후 재시작
   - `rm investment_insights.db`

## 📞 지원

- 문제 신고: [GitHub Issues](https://github.com/blueblud7/dailyYoutubeSummary/issues)
- 문서: [README.md](./README.md)
- 텔레그램 봇 가이드: [TELEGRAM_BOT_QUICK_START.md](./TELEGRAM_BOT_QUICK_START.md)

---

설정이 완료되면 텔레그램에서 `/start`를 입력하여 봇과 대화를 시작해보세요! 🎉 