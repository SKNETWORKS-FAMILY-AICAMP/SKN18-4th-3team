# Services 폴더 구조

## 📁 파일 구조

```
services/
├── etl/                   # ETL 파이프라인
│   ├── extract/           # 데이터 크롤링
│   │   ├── crawling_faq.py       # FAQ 데이터 크롤링
│   │   ├── crawling_info.py      # 질환 정보 크롤링
│   │   └── extract_cli.py        # 크롤링 실행 관리 CLI
│   ├── transform/         # 데이터 변환
│   │   ├── transform_faq.py      # FAQ 청킹 및 변환
│   │   ├── transform_info.py     # 질환 정보 변환
│   │   └── transform_cli.py      # Transform 실행 관리 CLI
│   └── loader/            # 
├── llm_client.py          # LLM 
├── utils.py               # 공통 유틸리티
└── vector_store.py        # Vector DB 관리
```