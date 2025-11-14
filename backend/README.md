# Django Backend 구현 가이드

## 목차

- [서버 실행](#서버-실행)
- [프로젝트 구조](#프로젝트-구조)
- [미들웨어](#미들웨어)
- [Serializer](#serializer)
- [Form](#form)
- [구현된 앱](#구현된-앱)
  - [users 앱](#users-앱)
  - [chatbot 앱](#chatbot-앱)
  - [profiles 앱](#profiles-앱)

---

## 서버 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치 (프로젝트 루트의 docker/requirements.txt 사용)
pip install -r ../docker/requirements.txt

# 데이터베이스 마이그레이션
python manage.py migrate

# 서버 실행
python manage.py runserver
```

**참고:**

- 서버는 기본적으로 `localhost:8000`에서 실행됩니다
- `.env` 파일에서 데이터베이스 연결 정보를 설정해야 합니다
- PostgreSQL 데이터베이스가 실행 중이어야 합니다 (`docker-compose up -d`)

---

## 프로젝트 구조

```
config/
├── settings.py      # Django 설정 (DB, 미들웨어, DRF, CORS 등)
├── urls.py          # URL 라우팅
└── README.md        # 이 문서

apps/
├── users/           # 사용자 인증 앱
├── chatbot/         # 챗봇 대화 관리 앱
└── profiles/        # 프로필 관리 앱
```

---

## 미들웨어

Django의 미들웨어는 모든 HTTP 요청/응답에 대해 전역적으로 처리

### 주요 역할

- **CorsMiddleware**: 리액트 프론트엔드(`localhost:3000`)와의 CORS 처리
- **AuthenticationMiddleware**: `request.user` 객체 자동 주입
- **CsrfViewMiddleware**: CSRF 토큰 검증으로 보안 강화

---

## Serializer

DRF(Django REST Framework) Serializer를 사용하여 API 요청 데이터 검증 처리

### users 앱 Serializer

**위치**: `apps/users/serializers.py`

- **UserSignupSerializer**: 회원가입 데이터 검증
  - 이메일 중복 확인
  - 비밀번호 일치 확인
  - Django 비밀번호 유효성 검사
- **UserLoginSerializer**: 로그인 데이터 검증
- **EmailCheckSerializer**: 이메일 중복 확인

### profiles 앱 Serializer

**위치**: `apps/profiles/serializers.py`

- **ProfileUpdateSerializer**: 프로필 수정 데이터 검증
- **ChangePasswordSerializer**: 비밀번호 변경 데이터 검증
  - 새 비밀번호 일치 확인
  - Django 비밀번호 유효성 검사

### 검증 계층 구조

1. **Serializer**: 입력 데이터 형식 및 비즈니스 규칙 검증
2. **Django Validators**: 비밀번호 강도 검증 (settings.py의 `AUTH_PASSWORD_VALIDATORS`)
3. **모델 제약조건**: DB 레벨 제약 (unique, null 등)

---

## Form

Django Form은 주로 Admin 패널에서 사용

### users 앱 Form

**위치**: `apps/users/admin.py`

- **UserAdmin.get_form()**: Admin 패널에서 이메일 기반 로그인을 위한 폼 커스터마이징
  - `username` 필드 라벨을 '사용자명'으로 변경
  - 이메일을 로그인 필드로 사용하도록 설정

---

## 구현된 앱

### users 앱

**이메일 기반 인증 시스템** 구현

#### 주요 기능

- **회원가입**: 이메일 중복 검증, 비밀번호 유효성 검사, 프로필 이미지 업로드 지원
- **로그인/로그아웃**: 세션 기반 인증
- **이메일 중복 확인**: 실시간 검증 API 제공

#### API 엔드포인트

- `POST /users/signup/` - 회원가입
- `POST /users/signup/check-email/` - 이메일 중복 확인(DB내 검증)
- `POST /users/login/` - 로그인
- `POST /users/logout/` - 로그아웃

#### 모델

- **User**: Django `AbstractUser` 확장
  - `email`: 로그인 필드 (`USERNAME_FIELD = 'email'`)
  - `profile_image`: 프로필 이미지
  - `first_name`, `last_name` 필드 제거

#### Serializer

- `UserSignupSerializer`: 회원가입 검증
- `UserLoginSerializer`: 로그인 검증
- `EmailCheckSerializer`: 이메일 중복 확인

---

### chatbot 앱

**대화 세션 및 메시지 관리** 구현

#### 주요 기능

- **대화 세션 관리**: 로그인 사용자의 대화 세션 저장 및 조회
- **자동 제목 생성**: Signal 활용하여 첫 챗봇 응답 시 대화 제목 자동 생성
- **게스트 모드**: 비로그인 사용자도 대화 가능 (저장 안됨)
- **페이지네이션**: 대화 세션 목록 조회 시 페이지네이션 지원 (기본 20개, 최대 100개)

#### API 엔드포인트

- `GET /chatbot/` - 채팅 메인 페이지 (인증 상태 확인)
- `GET /chatbot/api/conversations/` - 대화 세션 목록 조회
- `POST /chatbot/api/conversations/` - 새 대화 세션 생성
- `GET /chatbot/api/conversations/<id>/` - 대화 세션 상세 조회
- `DELETE /chatbot/api/conversations/<id>/` - 대화 세션 삭제
- `GET /chatbot/api/conversations/<id>/messages/` - 메시지 목록 조회
- `POST /chatbot/api/conversations/<id>/messages/` - 메시지 전송 및 챗봇 응답
- `POST /chatbot/api/chat/` - 게스트 대화 (저장 안됨)

#### 모델

- **Conversation**: 대화 세션
  - `user`: 사용자 (ForeignKey)
  - `title`: 대화 제목 (자동 생성)
  - `created_at`, `updated_at`: 타임스탬프
- **Message**: 개별 메시지
  - `conversation`: 대화 세션 (ForeignKey)
  - `role`: 역할 ('user' 또는 'assistant')
  - `content`: 메시지 내용 (암호화 저장)
  - `thinking_process`: 랭그래프 노드 진행 과정 (JSON)
  - `get_decrypted_content()`: 암호화된 내용 복호화 메서드
- **SentimentAnalysis**: 감정 분석 결과
  - `message`: 메시지 (OneToOneField)
  - `sentiment_type`: 감정 타입 ('positive', 'negative', 'neutral')
  - `sentiment_score`: 감정 점수 (0.0 ~ 1.0)
  - `keywords`: 감정 키워드 (JSON)
  - `analyzed_at`: 분석 시간
- **DiseaseQuery**: 질환 검색 기록
  - `message`: 메시지 (ForeignKey)
  - `disease_name`: 질환명
  - `searched_at`: 검색 시간

#### Signal

- **encrypt_message_content**: 메시지 저장 전 content 필드 자동 암호화
- **auto_generate_conversation_title**: 챗봇의 첫 응답 생성 시 대화 제목 자동 생성

#### 보안 기능

- **메시지 암호화**: 모든 메시지 내용은 저장 시 자동으로 암호화됨 (`encryption.py` 사용)
  - 암호화된 메시지는 `get_decrypted_content()` 메서드로 복호화하여 조회
  - Signal을 통해 저장 전 자동 암호화 처리

---

### profiles 앱

**사용자 프로필 관리 및 통계** 구현

#### 주요 기능

- **프로필 조회/수정**: 사용자명 변경, 프로필 이미지 업로드
- **비밀번호 변경**: 현재 비밀번호 확인 후 변경
- **계정 삭제**: 비밀번호 확인 후 계정 삭제
- **사용자 통계**: 주간/월간/전체 대화 세션 및 메시지 수 통계 제공

#### API 엔드포인트

**프로필 관리:**

- `GET /profiles/` - 프로필 조회
- `PUT /profiles/update/` - 프로필 수정 (사용자명 변경)
- `PUT /profiles/password/` - 비밀번호 변경
- `DELETE /profiles/delete/` - 계정 삭제
- `POST /profiles/upload-image/` - 프로필 이미지 업로드

**대시보드 통계 API:**

- `GET /profiles/api/kpi/` - KPI 데이터 (총 대화 횟수, 총 메시지 수)
- `GET /profiles/api/conversation-frequency/` - 최근 7일 대화 빈도
- `GET /profiles/api/hourly-pattern/` - 시간대별 대화 패턴 (히트맵)
- `GET /profiles/api/sentiment-distribution/` - 감정 분포 (파이 차트)
- `GET /profiles/api/emotion-keywords/` - 감정 키워드 (워드 클라우드)
- `GET /profiles/api/top-diseases/` - 자주 검색한 질환 TOP 10

#### Serializer

- `ProfileUpdateSerializer`: 프로필 수정 검증
- `ChangePasswordSerializer`: 비밀번호 변경 검증

---

## 설정 파일

### settings.py 주요 설정

- **AUTH_USER_MODEL**: `'users.User'` (커스텀 User 모델)
- **CORS_ALLOWED_ORIGINS**: 리액트 개발 서버 (`localhost:3000`)
- **REST_FRAMEWORK**: DRF 기본 설정 (페이지네이션, 인증 등)
- **AUTH_PASSWORD_VALIDATORS**: 비밀번호 유효성 검사 규칙
