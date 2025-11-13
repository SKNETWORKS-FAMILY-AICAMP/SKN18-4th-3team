# Chatbot App - 멘탈 헬스 챗봇

Django 기반의 멘탈 헬스 챗봇 애플리케이션입니다. 사용자와의 대화를 저장하고, AI 기반 감정 분석을 수행하며, 질환 관련 정보를 추출하여 대시보드로 시각화합니다.

## 목차

- [주요 기능](#주요-기능)
- [데이터베이스 구조](#데이터베이스-구조)
- [파일 구조](#파일-구조)
- [API 엔드포인트](#api-엔드포인트)
- [설치 및 설정](#설치-및-설정)
- [사용 방법](#사용-방법)
- [기술 스택](#기술-스택)

## 주요 기능

### 1. 대화 세션 관리
- 사용자별 대화 세션 생성 및 관리
- 두 가지 대화 타입 지원:
  - **정보형 (info)**: 질환 정보 검색 및 일반적인 정보 제공
  - **상담형 (counseling)**: 심리 상담 및 감정 지원

### 2. 메시지 저장
- 사용자와 챗봇 간 주고받은 모든 메시지 저장
- 타임스탬프를 통한 대화 이력 추적
- 세션별 메시지 그룹화

### 3. AI 감정 분석
- **HuggingFace Transformers** 기반 다국어 감정 분석
- 사용 모델: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- 감정 분류: 긍정(positive), 부정(negative), 중립(neutral)
- 감정 점수(0.0 ~ 1.0) 및 감정 키워드 추출
- 한국어 텍스트 지원

### 4. 질환명 추출
- 사용자 메시지에서 정신 건강 관련 질환명 자동 추출

### 5. 대시보드 및 통계
- 사용자별 대화 통계 시각화
- 7가지 차트 및 통계 제공:
  - KPI (총 대화 횟수, 총 메시지 수)
  - 최근 7일 대화 빈도
  - 시간대별 대화 패턴 히트맵
  - 감정 분포 파이차트
  - 감정 키워드 워드클라우드
  - 자주 검색한 질환 TOP 10
  - 주차별 질환 검색 추이

## 데이터베이스 구조

### ERD 관계

```
auth_user (Django 기본)
    ↓ (1:N)
chat_session
    ↓ (1:N)
message
    ↓ (1:1)         ↓ (1:N)
sentiment_analysis  disease_query
```

### 테이블 상세

#### 1. ChatSession (chat_session)
대화 세션 정보를 저장합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BigInt | 기본키 |
| user_id | BigInt | 사용자 ID (FK) |
| session_type | Varchar(20) | 대화 타입 (info/counseling) |
| created_at | DateTime | 세션 시작 시간 |
| updated_at | DateTime | 마지막 업데이트 시간 |
| is_active | Boolean | 활성 상태 |

#### 2. Message (message)
개별 메시지 정보를 저장합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BigInt | 기본키 |
| session_id | BigInt | 세션 ID (FK) |
| sender | Varchar(10) | 발신자 (user/bot) |
| content | Text | 메시지 내용 |
| created_at | DateTime | 생성 시간 |

#### 3. SentimentAnalysis (sentiment_analysis)
메시지의 감정 분석 결과를 저장합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BigInt | 기본키 |
| message_id | BigInt | 메시지 ID (FK, 1:1) |
| sentiment_type | Varchar(20) | 감정 타입 (positive/negative/neutral) |
| sentiment_score | Float | 감정 점수 (0.0~1.0) |
| keywords | JSON | 감정 키워드 배열 |
| analyzed_at | DateTime | 분석 수행 시간 |

#### 4. DiseaseQuery (disease_query)
질환 검색 기록을 저장합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BigInt | 기본키 |
| message_id | BigInt | 메시지 ID (FK) |
| disease_name | Varchar(100) | 질환명 |
| searched_at | DateTime | 검색 시간 |

**인덱스**: `(disease_name, searched_at)` 복합 인덱스로 질환별 검색 최적화

## 파일 구조

```
apps/chatbot/
├── admin.py                      # Django 관리자 페이지 설정
├── models.py                     # 데이터베이스 모델 정의
├── views.py                      # 뷰 및 API 엔드포인트
├── urls.py                       # URL 라우팅
├── utils.py                      # 유틸리티 함수 (감정 분석, 질환명 추출)
├── schema.sql                    # PostgreSQL 스키마 (참고용)
└── README.md                     # 이 문서
```

### 파일별 상세 설명

#### models.py
4개의 Django 모델을 정의합니다:
- `ChatSession`: 대화 세션 관리
- `Message`: 개별 메시지 저장
- `SentimentAnalysis`: 감정 분석 결과
- `DiseaseQuery`: 질환 검색 기록

각 모델은 Meta 클래스를 통해 테이블명, verbose_name, ordering 등을 설정합니다.

#### views.py
대시보드 페이지와 7개의 API 엔드포인트를 제공합니다:
- `dashboard_view`: 대시보드 메인 페이지
- `dashboard_api_kpi`: KPI 데이터 API
- `dashboard_api_conversation_frequency`: 최근 7일 대화 빈도
- `dashboard_api_hourly_pattern`: 시간대별 대화 패턴 (히트맵)
- `dashboard_api_sentiment_distribution`: 감정 분포 (파이차트)
- `dashboard_api_emotion_keywords`: 감정 키워드 (워드클라우드)
- `dashboard_api_top_diseases`: TOP 10 질환
- `dashboard_api_disease_trends`: 주차별 질환 검색 추이

**개발 노트**: 현재 로그인 기능이 완성되지 않아 `get_user_for_request()` 헬퍼 함수를 통해 임시로 첫 번째 사용자를 사용합니다. 로그인 기능 완성 후 `@login_required` 데코레이터를 추가해야 합니다.

#### utils.py
감정 분석 및 질환명 추출을 위한 유틸리티 함수를 제공합니다:

**주요 함수**:
- `get_sentiment_analyzer()`: HuggingFace 감정 분석 모델 로드 (싱글톤)
- `analyze_sentiment(text)`: 텍스트 감정 분석 수행
- `extract_emotion_keywords(text)`: 감정 키워드 추출
- `extract_disease_names(text)`: 질환명 추출

**감정 키워드 목록**:
- 긍정: 행복, 기쁨, 즐거움, 좋아, 감사, 사랑, 희망 등
- 부정: 우울, 슬픔, 불안, 걱정, 두려움, 스트레스, 화, 외로움 등

#### admin.py
Django 관리자 페이지 설정:
- 각 모델에 대한 관리자 클래스 등록
- `list_display`: 목록 페이지에 표시할 필드
- `list_filter`: 필터링 옵션
- `search_fields`: 검색 필드
- `date_hierarchy`: 날짜 계층 탐색

#### urls.py
URL 라우팅 설정:
- `app_name`: 'chatbot' (네임스페이스)
- 8개의 URL 패턴 정의
- 대시보드 페이지 및 7개 API 엔드포인트

#### schema.sql
PostgreSQL 데이터베이스 스키마 (참고용):
- Django 마이그레이션과 동일한 스키마
- 인덱스 및 제약조건 정의
- 트리거 함수 (updated_at 자동 업데이트)
- 유용한 뷰 3개 (v_user_sentiment_stats, v_popular_diseases, v_daily_session_stats)

## API 엔드포인트

모든 API는 JSON 형식으로 응답합니다.

### 1. KPI 데이터
```
GET /chatbot/api/kpi/
```

**응답 예시**:
```json
{
  "total_sessions": 42,
  "total_messages": 158
}
```

### 2. 대화 빈도 (최근 7일)
```
GET /chatbot/api/conversation-frequency/
```

**응답 예시**:
```json
{
  "labels": ["11/07", "11/08", "11/09", "11/10", "11/11", "11/12", "11/13"],
  "values": [3, 5, 2, 8, 4, 6, 7]
}
```

### 3. 시간대별 대화 패턴 (히트맵)
```
GET /chatbot/api/hourly-pattern/
```

**응답 예시**:
```json
{
  "heatmap_data": [
    [0, 0, 0, 0, 0, 0, 1, 2, 3, 5, 4, 3, 2, 1, 0, 0, 0, 1, 2, 3, 2, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 3, 4, 6, 5, 4, 3, 2, 1, 0, 0, 2, 3, 4, 3, 2, 0, 0],
    ...
  ],
  "weekdays": ["월", "화", "수", "목", "금", "토", "일"],
  "hours": [0, 1, 2, ..., 23]
}
```

### 4. 감정 분포 (파이차트)
```
GET /chatbot/api/sentiment-distribution/
```

**응답 예시**:
```json
{
  "labels": ["긍정", "부정", "중립"],
  "values": [45, 23, 32]
}
```

### 5. 감정 키워드 (워드클라우드)
```
GET /chatbot/api/emotion-keywords/
```

**응답 예시**:
```json
{
  "keywords": [
    {"text": "우울", "count": 15, "sentiment": "negative"},
    {"text": "불안", "count": 12, "sentiment": "negative"},
    {"text": "행복", "count": 8, "sentiment": "positive"},
    ...
  ]
}
```

### 6. TOP 10 질환
```
GET /chatbot/api/top-diseases/
```

**응답 예시**:
```json
{
  "labels": ["우울증", "불안장애", "공황장애", "PTSD", "강박장애", ...],
  "values": [25, 18, 12, 9, 7, ...]
}
```

### 7. 주차별 질환 검색 추이
```
GET /chatbot/api/disease-trends/
```

**응답 예시**:
```json
{
  "labels": ["1주차", "2주차", "3주차", "4주차"],
  "datasets": [
    {"label": "우울증", "data": [5, 8, 7, 9]},
    {"label": "불안장애", "data": [3, 5, 4, 6]},
    ...
  ]
}
```
--------------------------------------------------------------------------------------------------
## 설치 및 설정

### 1. 필수 패키지 설치

```bash
# Django 및 관련 패키지
pip install django>=5.0
pip install psycopg2-binary  # PostgreSQL 어댑터

# HuggingFace Transformers (감정 분석)
pip install transformers torch
```

또는 프로젝트 루트의 `requirements.txt`를 사용:
```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 설정

**config/settings.py**에서 PostgreSQL 설정을 확인합니다:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 3. 앱 등록

**config/settings.py**의 `INSTALLED_APPS`에 앱이 등록되어 있는지 확인:
```python
INSTALLED_APPS = [
    ...
    'apps.chatbot',
]
```

### 4. 마이그레이션 실행

```bash
# 마이그레이션 파일 생성 (이미 존재하므로 생략 가능)
python manage.py makemigrations chatbot

# 데이터베이스 적용
python manage.py migrate
```

### 6. 감정 분석 모델 다운로드

첫 실행 시 HuggingFace 모델이 자동으로 다운로드됩니다:
- 모델: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- 크기: 약 1.1GB
- 위치: `~/.cache/huggingface/`

## 사용 방법

### 1. 개발 서버 실행

```bash
python manage.py runserver
```

### 2. 대시보드 접속

브라우저에서 다음 URL로 접속:
```
http://localhost:8000/chatbot/dashboard/
```

### 3. 관리자 페이지 접속 (선택 사항)

```
http://localhost:8000/admin/
```

관리자 페이지에서 다음 모델을 관리할 수 있습니다:
- 대화 세션
- 메시지
- 감정 분석
- 질환 검색
