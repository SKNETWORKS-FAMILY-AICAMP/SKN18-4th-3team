# MindCare ∞ | 정신건강 AI 상담 파트너

> 정신건강 정보 검색과 감정 코칭을 하나의 대화 경험으로 엮은 LangGraph 기반 하이브리드 챗봇 서비스
---

## 📑 목차

- [서비스 소개](#-서비스-소개)
- [핵심 기능](#-핵심-기능)
- [시스템 아키텍처](#-시스템-아키텍처)
- [데이터 출처](#-데이터-출처)
- [상담형 대화 처리](#-상담형-대화-처리)
- [로컬 실행](#-로컬-실행)
- [기술 스택](#-기술-스택)

---

## 🎯 서비스 소개

### 목표
국가정신건강정보포털 데이터 기반 **신뢰할 수 있는 질환 정보** + **사용자 감정 맥락** 동시 케어

### 타깃
- 2030 직장인 · 취준생
- 심리 상담이 부담스러운 초입 사용자

### 해결하는 문제

| 문제 | 기존 한계 | MindCare 해법 |
|------|----------|--------------|
| 🚧 감정 표현 어려움 | 맥락 기억 불가 | **LangGraph 슬롯 메모리** (7개 질문) |
| ⚠️ 정보 신뢰도 | 출처 불분명 | **국가정신정보포털 → pgvector RAG** |
| 🔒 내용 노출 우려 | Plain text 저장 | **Fernet 암호화 + 게스트 모드** |

---

## ✨ 핵심 기능

### 1️⃣ 듀얼 플로우 AI 상담

- **정보형**: "우울증이란?" → Vector DB + SQL 이미지 검색
- **상담형**: "요즘 우울해요" → 7개 질문으로 감정 슬롯 수집

### 2️⃣ 상담형 대화 (7개 슬롯)

1. **감정 상태**: 우울함, 불안함, 무기력함
2. **상황/시기**: 언제부터, 어떤 계기
3. **신체 변화**: 수면, 식사, 피로감
4. **사고 패턴**: 자책감, 부정적 사고
5. **행동 패턴**: 사회적 회피, 활동 감소
6. **대인관계**: 가족, 친구, 지지 체계
7. **상담 의향**: 전문 상담/치료 의향

### 3️⃣ 보안 & 인사이트

- **Fernet 암호화**: 모든 대화 암호화 저장
- **대시보드**: 감정 분포, 시간대 히트맵, 키워드 클라우드
- **게스트 모드**: 로그인 없이 익명 상담

---

## 📊 데이터 출처

1. **질환별 정보 (Disease Information)**
   - URL: [국가정신건강정보포털 질환별 정보](https://www.mentalhealth.go.kr/portal/disease/diseaseList.do)
   - 포함 내용:  약 44개 정신건강 질환 정보(질환 설명, 증상, 원인, 치료법, 예방법)

2. **자주 찾는 질문 (FAQ)**
   - URL: [국가정신건강정보포털 FAQ](https://www.mentalhealth.go.kr/portal/faq/portalFaqList.do)
   - 포함 내용: 정신건강 관련 질문-답변 쌍


###  데이터 선정 이유
- 국가 공식 기관 데이터로 신뢰성 보장
- 정기적으로 업데이트되는 최신 정보
- 저작권 문제 없는 공공 데이터

### 데이터 수집 방법 (Crawling Pipeline)
- **Playwright**: 동적 웹페이지 크롤링
- **BeautifulSoup4**: HTML 파싱 및 데이터 추출
- **asyncio**: 비동기 병렬 크롤링으로 성능 최적화

---

## 🏗️ 시스템 아키텍처

```
사용자
  ↓
React Frontend (포트 3000)
  ↓ REST API
Django Backend (포트 8000)
  ↓
LangGraph (AI 대화 엔진)
  ↓
pgvector DB + OpenAI GPT-5
```

---

## 🖼️ 서비스 스크린샷

### LangSmith 트레이스 캡처
- 정보형
![Smith_정보형](assets\LangSmith\LangSmith_정보형.png)

- 상담형
![Smith_상담형](assets\LangSmith\LangSmith_상담형.png)


### 챗봇 화면
- 정보형
![챗봇_정보형](assets\chatbot\챗봇_정보형.png)

- 상담형
![챗봇_상담형1](assets\chatbot\챗봇_상담형1.png)
![챗봇_상담형2](assets\chatbot\챗봇_상담형2.png)
![챗봇_상담형3](assets\chatbot\챗봇_상담형3.png)

---

### 대시보드
> **서비스 활성도 + 이용 패턴 + 정서 상태 + 관심 질환**을 살펴 보는 운영용 대시보드

![Dashboard](assets/dashboard/1.나의대화통계.png)
- 'KPI 카드'와 '최근 7일 대화 빈도 차트'를 함께 보면 전 날 대비 대화량이 증가했는지, 특정 이벤트 이후 급감했는지 확인 가능

![Dashboard](assets/dashboard/2.시간대별%20대화기록.png)
- '시간대 히트맵'은 사용자가 언제 가장 많이 찾아오는지(예: 밤 10시 이후) 피크 타임에 대한 패턴 파악 가능

![Dashboard](assets/dashboard/3.감정분포.png)
![Dashboard](assets/dashboard/4.감정%20키워드.png)
- '감정 분포'와 '감정 키워드'는 최근에 어떤 정서가 늘었는지, 어떤 표현이 자주 언급되는지 파악 가능

- 감정 분류 모델 사용
  | 구분 | 값 |
  | --- | --- |
  | 기반 모델 | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` |
  | 토크나이저 | transformers 기본 토크나이저 (512 토큰) |
  | 결과 레이블 | `positive`, `negative`, `neutral` |
  | score 범위 | 0.0 ~ 1.0 (HuggingFace pipeline confidence) |
  | 모델 선정 이유 | 한국어 지원, 감정 데이터에 특화된 학습으로 섬세한 감정 구분 가능 | 

![Dashboard](assets/dashboard/5.자주%20검색한%20질환.png)
- '자주 검색한 질환 TOP 10'으로 이용자가 반복적으로 찾는 질환·증상 목록 파악 가능
- 질환명의 표기를 통일하기 위해서 한 질병에 대한 다양한 표기를(ex: 우울, 우울증, 우울장애) 하나의 대표 질병(ex: 우울장애)으로 매핑

---

## 🔄 상담형 대화 처리

> 백엔드는 상태 저장 안 함(stateless), 프론트가 `conversation_state` 메모리 보관

### 상태 관리

| 위치 | 저장 내용 | 목적 |
|------|----------|------|
| **DB** | 메시지 (암호화) | 대화 기록 |
| **프론트 메모리** | conversation_state | 대화 상태 유지 |

**conversation_state 구조**:
```javascript
{
  slot_data: {
    slot_1: "우울하고 무기력해요",  // 감정
    slot_2: "2주 전부터",           // 시기
    slot_3: null,                   // 미수집
    // ... slot_7까지
  },
  slot_status: {
    slot_1: true,   // 완료
    slot_2: true,   // 완료
    slot_3: false,  // 미완료
  },
  current_slot: "slot_3",
  initial_question: "요즘 우울해요",
  question_type: "counseling"
}
```

### 대화 흐름

#### Turn 1: 첫 질문
```
사용자: "요즘 우울해요"
  ↓
백엔드: 그래프 실행 (classify → state_check → question)
  ↓
응답: {
  bot_question: "언제부터 우울하셨나요?",
  conversation_state: { slot_1 완료 },
  requires_answer: true
}
  ↓
프론트: conversation_state 메모리 저장 ✅
```

#### Turn 2: 사용자 답변
```
사용자: "2주 전부터요"
  ↓
프론트: 저장된 conversation_state + 답변 전송
  ↓
백엔드: 상태 복원 → 그래프 실행
  ↓
응답: {
  bot_question: "수면은 어떠신가요?",
  conversation_state: { slot_1,2 완료 },
  requires_answer: true
}
  ↓
프론트: 업데이트된 상태 저장 ✅
```

#### Turn 3~7: 반복
7개 슬롯 완료까지 반복

#### 최종: 모든 슬롯 완료
```
백엔드: slot_memory → extract → search → chat_llm
  ↓
응답: {
  final_answer: "증상 분석 결과...",
  requires_answer: false
}
  ↓
프론트: conversation_state = null (종료) ✅
```

### 핵심 포인트

- ✅ 백엔드는 상태 저장 안 함 (stateless)
- ✅ 프론트가 `conversation_state` 메모리 보관
- ✅ 매 요청마다 프론트가 상태 전송
- ✅ `requires_answer` 플래그로 답변 필요 여부 판단

---

## 🚀 로컬 실행 (처음부터 끝까지)

### 사전 준비
- Python 3.12 이상
- Node.js 18 이상
- Docker Desktop (PostgreSQL용)
- uv 패키지 매니저 ([설치 가이드](https://docs.astral.sh/uv/getting-started/installation/))

---

### 1️⃣ 프로젝트 클론
```bash
git clone <repository-url>
cd SKN18-4th-3team
```

### 2️⃣ 환경 변수 설정
```bash
# .env 파일 생성
cp .env.sample .env
cp frontend/.env.sample frontend/.env
```

**.env 파일 편집** (필수!):
```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=your-openai-api-key-here

# 암호화 키 생성 (Python으로 생성)
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-generated-encryption-key

# 데이터베이스 (기본값 사용 가능)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mindcare
```

### 3️⃣ Python 가상환경 & 패키지 설치
```bash
# 가상환경 생성
uv venv .venv

# 가상환경 활성화
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 패키지 설치
uv pip install -r docker/requirements.txt
```

### 4️⃣ PostgreSQL 실행 (Docker)
```bash
# Docker Compose로 PostgreSQL 시작
docker-compose up -d

# 실행 확인
docker ps
```

### 5️⃣ 데이터베이스 마이그레이션 ⭐
```bash
# 마이그레이션 파일 생성
python backend/manage.py makemigrations

# 마이그레이션 적용 (DB 테이블 생성)
python backend/manage.py migrate

# 슈퍼유저 생성 (Admin 접속용)
python backend/manage.py createsuperuser
# Username, Email, Password 입력
```

### 6️⃣ 프론트엔드 패키지 설치
```bash
cd frontend
npm install
cd ..
```

### 7️⃣ 서버 실행

**터미널 1 - 백엔드**:
```bash
# 가상환경 활성화 상태에서
python backend/manage.py runserver 0.0.0.0:8000
```

**터미널 2 - 프론트엔드**:
```bash
cd frontend
npm start
```

### 8️⃣ 접속 확인
- 🌐 **프론트엔드**: http://localhost:3000
- 🔧 **백엔드 API**: http://localhost:8000
- 📊 **Admin 페이지**: http://localhost:8000/admin

---

### 🔧 문제 해결

**포트가 이미 사용 중인 경우**:
```bash
# Windows
netstat -ano | findstr "8000 3000"
taskkill /PID <PID번호> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

**마이그레이션 오류**:
```bash
# DB 초기화 후 다시 시도
python backend/manage.py flush
python backend/manage.py migrate
```

**OpenAI API 키 오류**:
- .env 파일에 `OPENAI_API_KEY` 확인
- 키 앞뒤 공백 제거
- 따옴표 없이 입력

---

### 📦 선택사항: RAG 데이터 준비

벡터 DB와 이미지 데이터를 사용하려면:

```bash
# 1. 데이터 추출 (크롤링)
python -m rag.services.etl.extract.extract_cli

# 2. 데이터 변환 (청킹)
python -m rag.services.etl.transform.transform_cli

# 3. RDB 로드 (이미지)
python -m rag.services.etl.loader.load_rdb

# 4. Vector DB 로드 (임베딩)
python -m rag.services.etl.loader.load_vectordb

# 5. 그래프 검증
python rag/build_graph.py
```

---

## 🛠️ 기술 스택

| 영역 | 기술 |
|------|------|
| **Frontend** | ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB) ![React Router](https://img.shields.io/badge/React_Router-CA4245?style=for-the-badge&logo=react-router&logoColor=white) ![Framer Motion](https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white) |
| **Backend** | ![Django](https://img.shields.io/badge/Django_5-092E20?style=for-the-badge&logo=django&logoColor=white) ![Django REST Framework](https://img.shields.io/badge/DRF-ff1709?style=for-the-badge&logo=django&logoColor=white&labelColor=ff1709) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white) |
| **AI/ML** | ![LangGraph](https://img.shields.io/badge/LangGraph-0A66C2?style=for-the-badge) ![OpenAI GPT-5](https://img.shields.io/badge/OpenAI_GPT--5-412991?style=for-the-badge&logo=openai&logoColor=white) ![text-embedding-3-large](https://img.shields.io/badge/text--embedding--3--large-10A37F?style=for-the-badge&logo=openai&logoColor=white) |
| **Database** |![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white) ![pgvector](https://img.shields.io/badge/pgvector-4169E1?style=for-the-badge) |
| **Security** |![Fernet](https://img.shields.io/badge/Fernet_Encryption-000000?style=for-the-badge) ![Django Session Auth](https://img.shields.io/badge/Django_Session_Auth-092E20?style=for-the-badge&logo=django&logoColor=white)|



---

## 📚 추가 문서

- [상담형 대화 테스트](rag/RUN_COUNSELING_TEST.md)
- [그래프 구조](rag/graph_structure.png)

---

<div align="center">

**Made with ❤️ by SKN18-4th-3team**

</div>
