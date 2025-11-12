# SKN18-4th-3team

## 목차

- [환경 설정](#환경-설정)
- [RAG ETL 파이프라인](#rag-etl-파이프라인)
  - [1. Extraction (추출)](#1-extraction-추출)
  - [2. Transform & Chunking (변환 및 청킹)](#2-transform--chunking-변환-및-청킹)
  - [3. Loader (적재)](#3-loader-적재)

---

## 환경 설정

### 1. 가상환경 설치 및 의존성 설치

```bash
# 가상환경 생성
uv venv .venv python3.12

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
uv pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 환경 변수 설정

```bash
# 환경 변수 파일 복사
cp .env.sample .env
```

`.env` 파일에서 다음 항목을 설정하세요:

- **API 키**: OpenAI API 키 설정
- **PostgreSQL 설정**: 데이터베이스 연결 정보 설정

#### PostgreSQL 포트 확인

```bash
# 포트 5432 사용 여부 확인
lsof -i :5432
```

- 포트 5432가 사용 중이 아닌 경우: `PG_PORT=5432` 사용
- 포트 5432가 사용 중인 경우: `PG_PORT=5433` 사용

### 3. 데이터베이스 실행

```bash
# Docker Compose로 PostgreSQL 실행
docker-compose up -d
```

### 4. 데이터베이스 연결 확인

DBeaver 또는 다른 데이터베이스 클라이언트에서 연결 설정을 확인하세요.

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
python services/etl/extract/extract_cli.py
```

**결과 확인:**

- `data/raw/` 디렉토리에 크롤링된 데이터 파일 저장 확인

---

### 2. Transform & Chunking (변환 및 청킹)

**처리 내용:**

- LangChain splitter를 이용한 청킹 진행
- 자가진단테스트/참고문헌 데이터 삭제
- 테이블을 텍스트로 전환
- 이미지 메타데이터 생성
- 텍스트 카테고리 파악 후 `content_type` 추가

**실행:**

```bash
python services/etl/transform/transform_cli.py
```

---

### 3. Loader (적재)

**적재 내용:**

- 테이블 생성
- OpenAI `text-embedding-3-large` (3072차원) 임베딩 생성 및 적재

#### 3.1. 데이터베이스 테이블 생성

```bash
python services/etl/loader/init_db.py
```

**옵션:**

- `--reset`: 기존 테이블 삭제 후 재생성
- `--info`: 테이블 정보만 출력

#### 3.2. 이미지 RDB 적재

```bash
python services/etl/loader/load_rdb.py
```

#### 3.3. Vector DB 적재

```bash
python services/etl/loader/load_vectordb.py
```

---

## 📝 참고사항

- 모든 ETL 단계는 순차적으로 실행해야 합니다 (Extraction → Transform → Loader)
- 각 단계 실행 후 결과 파일이 올바르게 생성되었는지 확인하세요
- OpenAI API 키가 올바르게 설정되어 있어야 임베딩 생성이 가능합니다
