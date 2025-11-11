# 정신건강 상담 챗봇 (Mental Health Chatbot)


## 🏗️ 프로젝트 구조

```
SKN18-4th-3team/
├── apps/                      # Django 앱
│   ├── chatbot/              # 챗봇 메인 앱
│   ├── emotionreports/       # 감정 리포트
│   └── users/                # 사용자 관리
│
├── config/                    # Django 설정
│   ├── settings.py           # 프로젝트 설정
│   ├── urls.py               # URL 라우팅
│   └── wsgi.py               # WSGI 설정
│
├── graph/                     # LangGraph 워크플로우
│   ├── agents/               # 에이전트 (서브그래프)
│   │   ├── classifiy_agent.py       # 쿼리 분류
│   │   ├── information_agent.py     # 정보형 처리
│   │   ├── counseling_agent.py      # 상담형 처리
│   │   └── retrieval_agent.py       # 검색 에이전트
│   ├── nodes/                # 실행 노드
│   │   ├── query_classifier_node.py
│   │   ├── search_rdb_node.py
│   │   ├── search_vector_db_node.py
│   │   ├── evaluate_node.py
│   │   ├── create_answer_node.py
│   │   ├── guideline_checker_node.py
│   │   ├── symptom_extractor_node.py
│   │   └── follow_up_question_node.py
│   ├── build_graph.py        # 그래프 빌드
│   └── README.md             # Graph 상세 문서
│
├── services/                  # 핵심 서비스 로직
│   ├── etl/                  # ETL 파이프라인
│   │   ├── extract/          # 데이터 크롤링
│   │   ├── transform/        # 데이터 변환
│   │   └── loader/           # 데이터 로딩
│   ├── llm_client.py         # LLM API 클라이언트
│   ├── utils.py              # 공통 유틸리티
│   ├── vector_store.py       # Vector DB 관리
│   └── README.md             # Services 상세 문서
│
├── static/                    # 정적 파일
│   ├── css/
│   └── js/
│
├── templates/                 # Django 템플릿
│   ├── chatbot/
│   └── users/
│
├── .env                       # 환경 변수
├── docker-compose.yml         # Docker 설정
├── manage.py                  # Django 관리 스크립트
├── requirements.txt           # Python 의존성
└── README.md                  # 프로젝트 문서 (이 파일)
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (크롤링용)
playwright install chromium
```

### 2. 데이터베이스 실행

```bash
# Docker로 PostgreSQL + pgvector 실행
docker-compose up -d
```

### 4. 데이터 수집 및 변환

```bash
# 1. 데이터 크롤링 (FAQ + 질환 정보)
python services/etl/extract/extract_cli.py

# 2. 데이터 변환 (청킹 및 메타데이터 생성)
python services/etl/transform/transform_cli.py
```

