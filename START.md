# SKN18-4th-3team

## 목차

- [환경 설정](#환경-설정)
  - [macOS](#macos)
  - [Windows](#windows)
- [서버 실행](#서버-실행)
- [RAG ETL 파이프라인](#rag-etl-파이프라인)
  - [1. Extraction (추출)](#1-extraction-추출)
  - [2. Transform &amp; Chunking (변환 및 청킹)](#2-transform--chunking-변환-및-청킹)
  - [3. Loader (적재)](#3-loader-적재)

---

## 환경 설정

### macOS

### 1. 가상환경 설치 및 의존성 설치

```bash
# 가상환경 생성
uv venv .venv python3.12

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
uv pip install -r docker/requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 환경 변수 설정

```bash
# 환경 변수 파일 복사
cp .env.sample .env
cp frontend/.env.sample frontend/.env
```

`.env` 파일에서 다음 항목을 설정하세요:

- **API 키**: OpenAI API 키 설정
- **PostgreSQL 설정**: 데이터베이스 연결 정보 설정

#### PostgreSQL 포트 확인

**macOS:**

```bash
# 포트 5432 사용 여부 확인
lsof -i :5432
```

**Windows:**

```cmd
# 포트 5432 사용 여부 확인
netstat -ano | findstr :5432
```

- 포트 5432가 사용 중이 아닌 경우: `PG_PORT=5432` 사용
- 포트 5432가 사용 중인 경우: `PG_PORT=5433` 사용

#### Django/React 포트 확인

백엔드와 프론트엔드 서버의 기본 포트 사용 여부를 확인합니다.

**macOS:**

```bash
# 백엔드 포트 확인 (기본: 8000)
lsof -i :8000

# 프론트엔드 포트 확인 (기본: 3000)
lsof -i :3000
```

**Windows:**

```cmd
# 백엔드 포트 확인 (기본: 8000)
netstat -ano | findstr :8000

# 프론트엔드 포트 확인 (기본: 3000)
netstat -ano | findstr :3000
```

- 포트가 사용 중이면 `.env` 파일에서 다른 포트 번호로 설정하세요.
- 백엔드 포트: `DJANGO_PORT` (기본값: 8000)
- 프론트엔드 포트: `REACT_PORT` 또는 `PORT` (기본값: 3000)

### 3. 데이터베이스 실행

```bash
# Docker Compose로 PostgreSQL 실행
docker-compose up -d
```

### 4. 데이터베이스 연결 확인

DBeaver 또는 다른 데이터베이스 클라이언트에서 연결 설정을 확인하세요.

---

### Windows

### 1. 가상환경 설치 및 의존성 설치

**PowerShell 또는 CMD 사용:**

```powershell
# 가상환경 생성
uv venv .venv python3.12

# 가상환경 활성화 (PowerShell)
.venv\Scripts\Activate.ps1

# 가상환경 활성화 (CMD)
.venv\Scripts\activate.bat

# 의존성 설치
uv pip install -r docker/requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

**참고:**

- PowerShell에서 실행 정책 오류가 발생하면: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- CMD에서는 `activate.bat` 사용

### 2. 환경 변수 설정

```powershell
# 환경 변수 파일 복사
Copy-Item .env.sample .env
Copy-Item frontend\.env.sample frontend\.env
```

또는 CMD:

```cmd
copy .env.sample .env
copy frontend\.env.sample frontend\.env
```

`.env` 파일에서 다음 항목을 설정하세요:

- **API 키**: OpenAI API 키 설정
- **PostgreSQL 설정**: 데이터베이스 연결 정보 설정

#### PostgreSQL 포트 확인

**Windows:**

```cmd
# 포트 5432 사용 여부 확인
netstat -ano | findstr :5432
```

- 포트 5432가 사용 중이 아닌 경우: `PG_PORT=5432` 사용
- 포트 5432가 사용 중인 경우: `PG_PORT=5433` 사용

#### Django/React 포트 확인

백엔드와 프론트엔드 서버의 기본 포트 사용 여부를 확인합니다.

**Windows:**

```cmd
# 백엔드 포트 확인 (기본: 8000)
netstat -ano | findstr :8000

# 프론트엔드 포트 확인 (기본: 3000)
netstat -ano | findstr :3000
```

- 포트가 사용 중이면 `.env` 파일에서 다른 포트 번호로 설정하세요.
- 백엔드 포트: `DJANGO_PORT` (기본값: 8000)
- 프론트엔드 포트: `REACT_PORT` 또는 `PORT` (기본값: 3000)

### 3. 데이터베이스 실행

```powershell
# Docker Compose로 PostgreSQL 실행
docker-compose up -d
```

### 4. 데이터베이스 연결 확인

DBeaver 또는 다른 데이터베이스 클라이언트에서 연결 설정을 확인하세요.

**Windows 환경변수 주의사항:**

1. **`frontend/.env` 파일 필수 확인:**

   ```
   PORT=3001
   REACT_APP_DJANGO_HOST=localhost
   REACT_APP_DJANGO_PORT=8080
   ```

2. **환경변수 형식:**

   - 공백 없이 작성: `REACT_APP_DJANGO_PORT=8080` (O)
   - 공백 있으면 안됨: `REACT_APP_DJANGO_PORT= 8080` (X)

3. **환경변수 변경 후:**
   - React 서버를 완전히 종료(Ctrl+C) 후 재시작해야 합니다.
   - 브라우저 캐시 문제가 있으면 시크릿 모드로 테스트하세요.

---

## 서버 실행

### 1. Django 마이그레이션

```bash
# 의존성 설치 (프로젝트 루트의 docker/requirements.txt 사용)
uv pip install -r docker/requirements.txt

# 마이그레이션 파일 생성
python backend/manage.py makemigrations

# 마이그레이션 실행
python backend/manage.py migrate
```

**오류 발생 시:**

마이그레이션 오류가 발생하면 다음 가이드를 참고하세요:

1. `docs/MIGRATION_GUIDE.md` 파일을 읽어보세요.
2. `docs/fix_migration_history.py` 스크립트를 실행하세요.

```bash
python docs/fix_migration_history.py
```

### 3. Django 관리자 계정 생성

```bash
python backend/manage.py createsuperuser
```

관리자 계정 생성 후 `http://localhost:8000/admin`에 접속하면 관리자 페이지에 진입할 수 있습니다.

### 4. 프론트엔드 서버 시작

```bash
cd frontend
npm install
npm start
```

### 5. 백엔드 서버 시작

```bash
cd backend
python manage.py runserver
```

서버 실행 후 `http://localhost:{REACT_PORT}` (기본값: 3000)에 접속하면 메인 페이지에 진입할 수 있습니다.

---

## RAG ETL 파이프라인

### 1. Extraction (추출)

**크롤링 대상:**

- [국가정신정보포털 - 질환별 정보](https://www.mentalhealth.go.kr/portal/disease/diseaseList.do)
- [국가정신정보포털 - 자주찾는 질문(FAQ)](https://www.mentalhealth.go.kr/portal/faq/portalFaqList.do)

**크롤링 규칙:**

- 이미지 정보는 RDB에 저장
- `alt`와 `description`이 없는 단순 일러스트 이미지는 크롤링에서 제외
- 두 크롤링 작업을 병렬로 진행

**실행:**

```bash
python -m rag.services.etl.extract.extract_cli
```

**결과 확인:**

- `rag/data/raw/` 디렉토리에 크롤링된 데이터 파일 저장 확인

---

### 2. Transform & Chunking (변환 및 청킹)

**처리 내용:**

- LangChain splitter를 이용한 청킹 진행
- FAQ/질병 정보 청킹 기본값: `chunk_size=1500`, `chunk_overlap=200` (약 1,500자 청크, 200자 오버랩)
- 자가진단테스트/참고문헌 데이터 삭제
- 테이블을 텍스트로 전환
- 이미지 메타데이터 생성
- 텍스트 카테고리 파악 후 `content_type` 추가

**실행:**

```bash
python -m rag.services.etl.transform.transform_cli
```

---

### 3. Loader (적재)

**적재 내용:**

- 테이블 생성
- OpenAI `text-embedding-3-large` (3072차원) 임베딩 생성 및 적재

#### 3.1. 데이터베이스 테이블 생성

```bash
python -m rag.services.etl.loader.init_db
```

**옵션:**

- `--reset`: 기존 테이블 삭제 후 재생성
- `--info`: 테이블 정보만 출력

#### 3.2. 이미지 RDB 적재

```bash
python -m rag.services.etl.loader.load_rdb
```

#### 3.3. Vector DB 적재

```bash
python -m rag.services.etl.loader.load_vectordb
```

---

## 📝 참고사항

- 모든 ETL 단계는 순차적으로 실행해야 합니다 (Extraction → Transform → Loader)
- 각 단계 실행 후 결과 파일이 올바르게 생성되었는지 확인하세요
- OpenAI API 키가 올바르게 설정되어 있어야 임베딩 생성이 가능합니다
