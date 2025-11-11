# Graph

LangGraph 기반 메디컬 챗봇 시스템을 구성하는 폴더입니다.

## 📁 구조

```
graph/
├── build_graph.py             # 메인 그래프 정의
│
├── nodes/                     # 실행 노드들
│   ├── query_classifier_node.py      # 쿼리 분류 (정보형/상담형)
│   ├── search_rdb_node.py            # RDB 검색 (이미지 데이터)
│   ├── search_vector_db_node.py      # VectorDB 검색 (텍스트)
│   ├── evaluate_node.py              # 검색 결과 평가
│   ├── create_answer_node.py         # 최종 응답 생성
│   ├── guideline_checker_node.py     # 가이드라인 체크
│   ├── symptom_extractor_node.py     # 증상 추출
│   └── follow_up_question_node.py    # 추가 질문 생성
│
└── agents/                    # 에이전트 (서브그래프)
    ├── classifiy_agent.py     # 쿼리 분류 (정보형/상담형)
    ├── information_agent.py   # 정보형 쿼리 처리
    ├── counseling_agent.py    # 상담형 쿼리 처리
    └── retrieval_agent.py     # 검색 에이전트 (RDB + VectorDB)
```

```
💬 User Input
   │
   ▼
🧠 QueryClassifierNode (query_classifier_node.py)
   ├── [정보형] → InformationAgent (information_agent.py)
   │     │
   │     ▼
   │   🤖 RetrievalAgent (retrieval_agent.py)
   │     ├── 🗄️ SearchRDBNode (search_rdb_node.py)  ← RDB 기반 검색 (이미지 데이터)
   │     └── 🔍 SearchVectorDBNode (search_vector_db_node.py)  ← VectorDB 기반 검색 (비정형 텍스트)
   │     │
   │     ▼
   │   🧾 EvaluateNode (evaluate_node.py)  ← 검색 결과 평가
   │     │
   │     ▼
   │   ✏️ CreateAnswerNode (create_answer_node.py)  ← 최종 응답 생성
   │     │
   │     ▼
   │   ✅ End
   │
   └── [상담형] → CounselingAgent (counseling_agent.py)
         │
         ▼
      📋 GuidelineCheckerNode (guideline_checker_node.py)
         ├── (충족)
         │     │
         │     ▼
         │   💬 SymptomExtractorNode (symptom_extractor_node.py)
         │     │
         │     ▼
         │   🤖 RetrievalAgent (retrieval_agent.py)
         │     ├── 🗄️ SearchRDBNode (search_rdb_node.py)
         │     └── 🔍 SearchVectorDBNode (search_vector_db_node.py)
         │     │
         │     ▼
         │   🧾 EvaluateNode (evaluate_node.py)
         │     │
         │     ▼
         │   🧠 CreateAnswerNode (create_answer_node.py)
         │     │
         │     ▼
         │   ✅ End
         │
         └── (미충족)
               │
               ▼
            ❓ FollowUpQuestionNode (follow_up_question_node.py)
               │
               ▼
            ↩️ GuidelineCheckerNode 로 루프

```