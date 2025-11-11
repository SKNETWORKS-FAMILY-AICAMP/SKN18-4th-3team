# RAG (Retrieval-Augmented Generation)

RAG 시스템을 구성하는 폴더입니다.

## 📁 구조

```
rag/
├── llm_client.py      # LLM API 호출 (GPT, Claude)
├── vector_store.py    # CustomPGVector (벡터 DB 관리)
├── embedding.py       # 텍스트 → 벡터 변환
├── utils.py           # 유틸리티 함수
│
└── etl/               # 데이터 파이프라인
    ├── extract/       # 데이터 수집 (크롤링)
    │   ├── crawling_faq.py
    │   ├── crawling_info.py
    │   ├── extract_cli.py
    │   └── README.md
    │
    ├── transform/     # 데이터 변환
    │   ├── transform_faq.py
    │   ├── transform_info.py
    │   ├── transform_cli.py
    │   └── README.md
    │
    └── loader/        # 데이터 적재 (DB 저장)
        ├── loader.py
        └── README.md
```