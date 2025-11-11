# SKN18-4th-3team

## 프로젝트 소개

LangGraph와 RAG(Retrieval-Augmented Generation)를 활용한 메디컬 챗봇 시스템입니다.
Django 프레임워크 기반으로 구축되었으며, pgvector를 사용한 벡터 검색과 LLM 기반 답변 생성을 제공합니다.

## 주요 기능

- **정보형 질의**: 질병 정보, FAQ 검색 및 답변 생성
- **상담형 질의**: 감정/증상 기반 상담 및 후속 질문 생성
- **벡터 검색**: pgvector 기반 의미론적 유사도 검색
- **ETL 파이프라인**: 데이터 수집, 변환, 임베딩 생성 및 저장

## 기술 스택

- **Backend**: Django 5.2.8, Python
- **AI/ML**: LangChain, LangGraph, OpenAI Embeddings
- **Database**: PostgreSQL + pgvector
- **Crawling**: Playwright
- **Infrastructure**: Docker Compose

## 프로젝트 구조

```
.
├── apps/                          # Django 애플리케이션
│   ├── chatbot/                   # 챗봇 기능
│   └── users/                     # 사용자 관리
│
├── config/                        # Django 설정
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── graph/                         # LangGraph 시스템
│   ├── build_graph.py             # 그래프 정의
│   ├── state.py                   # 상태 스키마
│   ├── agents/                    # 라우팅 에이전트
│   │   ├── query_agent.py         # 쿼리 타입 분기
│   │   └── counseling_agent.py    # 상담 흐름 관리
│   └── nodes/                     # 실행 노드
│       ├── query_classifier_node.py
│       ├── search_vector_db_node.py
│       ├── create_answer_node.py
│       ├── guideline_checker_node.py
│       ├── symptom_extractor_node.py
│       ├── validation_node.py
│       └── follow_up_question_node.py
│
├── rag/                           # RAG 시스템
│   ├── llm_client.py              # LLM API 호출
│   ├── vector_store.py            # 벡터 DB 관리
│   ├── embedding.py               # 임베딩 생성
│   ├── utils.py                   # 유틸리티
│   └── etl/                       # 데이터 파이프라인
│       ├── extract/               # 크롤링
│       ├── transform/             # 전처리 및 임베딩
│       └── loader/                # DB 저장
│
├── data/                          # 데이터 저장소
│   ├── raw/                       # 원본 데이터
│   ├── RDB/                       # 메타데이터
│   └── vectorDB/                  # 임베딩 데이터
│
├── static/                        # 정적 파일 (CSS, JS)
├── templates/                     # HTML 템플릿
└── docker-compose.yml             # Docker 구성
```

## 시작하기

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# PostgreSQL
PG_DB=your_database
PG_USER=your_user
PG_PASSWORD=your_password
PG_HOST=localhost
PG_PORT=5432

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Django
SECRET_KEY=your_secret_key
DEBUG=True
```

### 3. 데이터베이스 실행

```bash
# Docker Compose로 PostgreSQL + pgvector 실행
docker-compose up -d

# 데이터베이스 마이그레이션
python manage.py migrate
```

### 4. 데이터 수집 및 처리

```bash
# 1. 데이터 크롤링
python rag/etl/extract/extract_cli.py --all

# 2. 데이터 변환 및 임베딩 생성
python rag/etl/transform/transform_cli.py --all

# 3. 벡터 DB에 저장
python rag/etl/loader/loader.py --all
```

### 5. 서버 실행

```bash
python manage.py runserver
```

브라우저에서 `http://localhost:8000` 접속

## 시스템 아키텍처

### LangGraph 플로우

**정보형 질의**
```
사용자 입력 → 쿼리 분류 → 벡터 검색 → 답변 생성
```

**상담형 질의**
```
사용자 입력 → 가이드라인 체크 → 증상 추출 → 검증 → 벡터 검색 → 답변 생성
                    ↓ (불충분)
              후속 질문 생성
```

### RAG 파이프라인

```
질의 → 임베딩 변환 → 벡터 검색 → 관련 문서 검색 → LLM 답변 생성
```

## 개발 가이드

### 새로운 노드 추가

`graph/nodes/` 폴더에 새 노드를 추가하고 `build_graph.py`에서 연결하세요.

```python
# graph/nodes/my_node.py
def my_node(state):
    # 노드 로직
    return state

# graph/build_graph.py
graph.add_node("my_node", my_node)
graph.add_edge("previous_node", "my_node")
```

### 새로운 데이터 소스 추가

1. `rag/etl/extract/`에 크롤러 추가
2. `rag/etl/transform/`에 변환 로직 추가
3. `rag/etl/loader/`에서 DB 저장

## 문서

- [Graph 시스템 상세](graph/README.md)
- [RAG 시스템 상세](rag/README.md)
- [ETL Extract](rag/etl/extract/README.md)
- [ETL Transform](rag/etl/transform/README.md)
- [ETL Loader](rag/etl/loader/README.md)

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.