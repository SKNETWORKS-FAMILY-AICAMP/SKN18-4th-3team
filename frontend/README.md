# MindCare - AI 기반 심리 상담 챗봇

> AI를 활용한 정신건강 상담 서비스

---

## 📋 목차

1. [프로젝트 소개](#-프로젝트-소개)
2. [기술 스택](#-기술-스택)
3. [주요 기능](#-주요-기능)
4. [화면 구성](#-화면-구성)
5. [백엔드 구조](#-백엔드-구조)
6. [프론트엔드 구조](#-프론트엔드-구조)
7. [실행 방법](#-실행-방법)

---

## 🎯 프로젝트 소개

MindCare는 AI 기반 심리 상담 챗봇으로, 사용자의 감정을 분석하고 맞춤형 상담을 제공합니다.

- **LangGraph** 기반 대화 흐름 관리
- **감정 분석**을 통한 사용자 감정 상태 추적
- **대시보드**를 통한 감정 변화 시각화
- **백그라운드 실행**으로 끊김 없는 상담 경험

---

## 🛠 기술 스택

### Backend

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST-ff1709?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

### Frontend

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

### AI & ML

![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)

---

## ✨ 주요 기능

### 1️⃣ 이메일 기반 회원 인증

- 3단계 회원가입 프로세스
- 실시간 이메일 중복 확인
- 프로필 이미지 업로드

![회원가입 화면](../assets/user/가입화면_1.png)
![회원가입 화면](../assets/user/가입화면_2.png)
![회원가입 화면](../assets/user/가입화면_3.png)

### 2️⃣ AI 챗봇 상담

- **LangGraph** 기반 대화 흐름 관리
- **스트리밍 효과**로 실시간 응답
- 질환 정보 자동 검색 및 이미지 제공
- 게스트 모드 지원 (비로그인 사용자)

![메인 화면](../assets/main/Main.png)
![대화 화면](../assets/main/대화화면_1.png)
![대화 화면](../assets/main/대화화면_2.png)

### 3️⃣ 백그라운드 실행

- 페이지를 벗어나도 응답 처리 계속
- 완료 시 **토스트 알림**으로 사용자에게 알림
- 끊김 없는 상담 경험

![백그라운드 실행](../assets/main/백그라운드%20실행.png)

### 4️⃣ 감정 분석

- 각 메시지마다 감정 분석 수행
- 긍정/중립/부정 감정 분류
- 감정 키워드 추출

**감정 분석 타이밍:**
- **트리거 시점:** AI 응답(Assistant 메시지)이 저장된 직후 (Django `post_save` 시그널)
- **실행 방식:** 비동기 백그라운드 스레드로 실행
- **성능 최적화:** 대화 응답 속도에 영향 없음
- **분석 대상:** 해당 대화의 사용자 메시지 중 아직 감정 분석이 안 된 메시지들 (`sentiment__isnull=True`)

### 5️⃣ 대시보드 통계

** 연희님 작성 내용 추가**

---

## 🖼 화면 구성

### 화면 설계

![화면설계](../assets/web_planning/화면설계.jpg)
![화면설계](../assets/web_planning/화면설계2.jpg)
![화면설계](../assets/web_planning/화면설계3.jpg)
![화면설계](../assets/web_planning/화면설계4.jpg)
![화면설계](../assets/web_planning/화면설계5.jpg)
![화면설계](../assets/web_planning/화면설계6.jpg)
![화면설계](../assets/web_planning/화면설계7.jpg)

---

## 🔧 백엔드 구조

### 프로젝트 구성

```
backend/
├── config/              # Django 설정
│   ├── settings.py      # 메인 설정 파일
│   └── urls.py          # 전역 URL 라우팅
└── apps/                # Django 앱
    ├── users/           # 사용자 인증
    ├── chatbot/         # 챗봇 대화 관리
    └── profiles/        # 프로필 및 대시보드
```

### 1️⃣ Users 앱 - 사용자 인증

**URL Prefix:** `/users/`

#### 모델

- **User** (AbstractUser 확장)
  - `email` - 이메일 (로그인 필드)
  - `username` - 사용자명
  - `profile_image` - 프로필 이미지

#### API 엔드포인트

| Method | Endpoint                     | 설명             |
| ------ | ---------------------------- | ---------------- |
| POST   | `/users/signup/`             | 회원가입         |
| POST   | `/users/signup/check-email/` | 이메일 중복 확인 |
| POST   | `/users/login/`              | 로그인           |
| POST   | `/users/logout/`             | 로그아웃         |

#### 주요 기능

- 이메일 기반 인증 시스템
- 3단계 회원가입 프로세스
- 실시간 이메일 중복 검증
- 프로필 이미지 업로드

#### Admin 설정

- 이메일 기반 로그인 지원
- 사용자 목록 검색 및 필터링

---

### 2️⃣ Chatbot 앱 - AI 대화 관리

**URL Prefix:** `/chatbot/`

#### 모델

- **Conversation** - 대화 세션

  - `user` - 사용자 (ForeignKey)
  - `title` - 대화 제목 (자동 생성)

- **Message** - 메시지

  - `conversation` - 대화 세션 (ForeignKey)
  - `role` - 역할 ('user' / 'assistant')
  - `content` - 메시지 내용 (암호화 저장)
  - `thinking_process` - LangGraph 노드 진행 과정
  - `related_images` - 관련 이미지 메타데이터

- **SentimentAnalysis** - 감정 분석

  - `message` - 메시지 (OneToOneField)
  - `sentiment_type` - 'positive' / 'negative' / 'neutral'
  - `sentiment_score` - 감정 점수 (0.0 ~ 1.0)
  - `keywords` - 감정 키워드

- **DiseaseQuery** - 질환 검색

  - `message` - 메시지 (ForeignKey)
  - `disease_name` - 질환명

#### API 엔드포인트

| Method | Endpoint                                    | 설명             |
| ------ | ------------------------------------------- | ---------------- |
| GET    | `/chatbot/api/conversations/`               | 대화 목록 조회   |
| POST   | `/chatbot/api/conversations/`               | 새 대화 생성     |
| GET    | `/chatbot/api/conversations/<id>/`          | 대화 상세 조회   |
| DELETE | `/chatbot/api/conversations/<id>/`          | 대화 삭제        |
| GET    | `/chatbot/api/conversations/<id>/messages/` | 메시지 목록 조회 |
| POST   | `/chatbot/api/conversations/<id>/messages/` | 메시지 전송      |
| POST   | `/chatbot/api/chat/`                        | 게스트 대화      |

#### 주요 기능

- **LangGraph 기반 AI 응답 생성**

  - 상담형 대화 흐름 관리
  - 질환명 자동 추출
  - 관련 이미지 검색
  - 사고 과정(thinking_process) 시각화

- **메시지 암호화/복호화**

  - Signal을 이용한 자동 암호화
  - DB에 암호화된 상태로 저장

- **감정 분석 백그라운드 처리**

  - HuggingFace 모델 사용
  - 비동기 스레드로 처리

- **대화 제목 자동 생성**

  - 첫 메시지 기반으로 자동 생성

#### Admin 설정

- Conversation, Message, SentimentAnalysis, DiseaseQuery 등록
- 대화 내 메시지 인라인 표시

---

### 3️⃣ Profiles 앱 - 프로필 및 대시보드

**URL Prefix:** `/profiles/`

#### API 엔드포인트

**프로필 관리:**

| Method | Endpoint                  | 설명                 |
| ------ | ------------------------- | -------------------- |
| GET    | `/profiles/`              | 프로필 조회          |
| PUT    | `/profiles/update/`       | 프로필 수정          |
| PUT    | `/profiles/password/`     | 비밀번호 변경        |
| DELETE | `/profiles/delete/`       | 계정 삭제            |
| POST   | `/profiles/upload-image/` | 프로필 이미지 업로드 |

**대시보드 통계 API:**

| Method | Endpoint                                | 설명                         |
| ------ | --------------------------------------- | ---------------------------- |
| GET    | `/profiles/api/kpi/`                    | KPI 데이터 (대화수/메시지수) |
| GET    | `/profiles/api/conversation-frequency/` | 최근 7일 대화 빈도           |
| GET    | `/profiles/api/hourly-pattern/`         | 시간대별 대화 패턴           |
| GET    | `/profiles/api/sentiment-distribution/` | 감정 분포                    |
| GET    | `/profiles/api/emotion-keywords/`       | 감정 키워드 TOP 30           |
| GET    | `/profiles/api/top-diseases/`           | 자주 검색한 질환 TOP 10      |

#### 주요 기능

- 프로필 CRUD
- 비밀번호 변경 (현재 비밀번호 검증)
- 계정 삭제 (비밀번호 확인)
- 6가지 대시보드 차트 데이터 제공
- 시간대별/요일별 대화 패턴 분석
- 감정 분석 통계
- 질환 검색 통계

---

## 💻 프론트엔드 구조

### 프로젝트 구성

```
frontend/src/
├── api/                    # API 통신
│   ├── axios.js           # Axios 설정
│   ├── auth.js            # 인증 API
│   ├── chat.js            # 채팅 API
│   └── profile.js         # 프로필 API
├── components/            # 재사용 컴포넌트
│   ├── Header.js          # 헤더
│   ├── Dashboard.js       # 대시보드 차트
│   ├── Sphere2D.js        # 메인 애니메이션
│   └── SphereAvatar.js    # 채팅 아바타
├── contexts/              # React Context
│   └── ToastContext.js    # 토스트 알림
├── pages/                 # 페이지
│   ├── MainPage.js        # 메인
│   ├── LoginPage.js       # 로그인
│   ├── SignupPage.js      # 회원가입
│   ├── ChatPage.js        # 채팅
│   └── ProfilePage.js     # 프로필/대시보드
└── App.js                 # 라우팅
```

### 주요 페이지

#### 1️⃣ 회원가입 (SignupPage.js)

- 3단계 프로세스
  - Step 1: 사용자명 + 프로필 이미지
  - Step 2: 이메일 + 비밀번호 (실시간 중복 확인)
  - Step 3: 정보 확인 및 제출
- 프로필 이미지 미리보기

#### 2️⃣ 메인 (MainPage.js)

- 타이핑 효과 인사말
- 애니메이션 구체 (Sphere2D)
- 대화 목록 사이드바
- 감정 분석 퍼센테이지 바
- 백그라운드 요청 폴링

#### 3️⃣ 채팅 (ChatPage.js)

**핵심 기능:**

- **대화 관리:** 생성/조회/삭제
- **스트리밍 효과:** 글자 하나씩 표시 (30ms 간격)
- **백그라운드 실행:** 페이지를 벗어나도 응답 처리
- **토스트 알림:** 응답 완료 시 알림
- **Thinking Process 표시:** LangGraph 노드 진행 과정
- **관련 이미지 표시:** 질환 정보 이미지

#### 4️⃣ 프로필/대시보드 (ProfilePage.js & Dashboard.js)

**프로필 관리:**

- 사용자명 변경
- 비밀번호 변경
- 계정 탈퇴

**대시보드 통계:**

- KPI 카드
- 대화 빈도 라인 차트
- 감정 분포 파이 차트
- 시간대별 패턴 히트맵
- 감정 키워드 워드 클라우드
- 자주 검색한 질환 바 차트

---

## 📌 주요 특징 정리

### 🎯 사용자 경험

- **3단계 회원가입** - 단계별 검증
- **백그라운드 실행** - 끊김 없는 상담
- **스트리밍 효과** - 실시간 응답
- **게스트 모드** - 로그인 없이 체험 가능

### 🔒 보안

- 메시지 암호화/복호화
- CSRF 보호
- 비밀번호 검증
- 이메일 unique 제약

### 📊 데이터 분석

- 감정 분석 (HuggingFace)
- 6가지 대시보드 차트
- 질환 검색 통계
- 시간대별 패턴 분석

### 🤖 AI 기능

- LangGraph 기반 대화 흐름
- 사고 과정 시각화
- 질환명 자동 추출
- 관련 이미지 자동 검색
