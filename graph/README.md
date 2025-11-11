# Graph

LangGraph 기반 메디컬 챗봇 시스템을 구성하는 폴더입니다.

## 📁 구조

```
graph/
├── build_graph.py             # 메인 그래프 정의
├── state.py                   # 그래프 상태 스키마
│
├── nodes/                     # 실행 노드들
│   ├── query_classifier_node.py      # 쿼리 분류
│   ├── search_vector_db_node.py      # 벡터 검색
│   ├── create_answer_node.py         # 답변 생성
│   ├── guideline_checker_node.py     # 가이드라인 체크
│   ├── symptom_extractor_node.py     # 증상 추출
│   ├── validation_node.py            # 정보 검증
│   └── follow_up_question_node.py    # 추가 질문 생성
│
└── agents/                  
    ├── query_agent.py         # 쿼리 타입 분기 (정보형/상담형)
    └── counseling_agent.py    # 상담 흐름 관리
```

