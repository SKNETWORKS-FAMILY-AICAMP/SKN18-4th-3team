# Graph 폴더 구조

LangGraph 기반 정신건강 챗봇 시스템의 대화 플로우를 구성하는 폴더입니다.

## 📁 파일 구조

```
graph/
├── build_graph.py                    # 전체 그래프 구조 정의 및 컴파일
│
├── nodes/                            # 실행 노드들
│   ├── classify_node.py              # 질문 분류 (정보형/상담형/무관)
│   ├── search_vectordb_node.py       # Vector DB 검색
│   ├── eval_node.py                  # 검색 결과 검증
│   ├── sql_search_node.py            # RDB 이미지 검색
│   ├── state_check_node.py           # Slot 상태 확인
│   ├── question_node.py              # 추가 질문 생성
│   ├── answer_node.py                # 사용자 답변 저장
│   ├── slot_memory_node.py           # Slot 데이터 통합
│   ├── extract_node.py               # 증상 키워드 추출
│   └── chat_llm_node.py              # 최종 답변 생성
│
└── agents/                           # 라우팅 에이전트
    ├── classify_agent.py             # 질문 분류 후 라우팅
    ├── eval_agent.py                 # 검증 결과 기반 라우팅
    ├── state_check_agent.py          # Slot 충족 여부 라우팅
    └── memory_agent.py               # Slot 데이터 통합 (라우팅 없음)
```