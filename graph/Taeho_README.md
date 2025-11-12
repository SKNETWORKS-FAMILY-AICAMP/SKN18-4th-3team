핵심 변경사항 요약

그래프 엔트리: classify (별도의 input 노드 없음)

모델 매핑: eval 노드만 gpt-5-mini, 나머지 노드는 gpt-5-nano (추가 파라미터 없음)

정의 파일 3종을 표준 경로에 고정

YAML 스펙: graph/specs/counseling_rag.graph.yaml

Mermaid: graph/specs/counseling_rag.flow.mmd

Edges CSV: graph/specs/counseling_rag.edges.csv

로더 스크립트: graph/Taeho_build_graph.py (YAML→LangGraph 컴파일)

폴더 구조
graph/
├─ agents/                         # 4개 에이전트 파일 (그대로 유지)
├─ nodes/                          # 10개 노드 파일 (그대로 유지)
│  ├─ classify.py
│  ├─ search_vectordb.py
│  ├─ eval.py
│  ├─ sql_search.py
│  ├─ state_check.py
│  ├─ question.py
│  ├─ answer.py
│  ├─ slot_memory.py
│  ├─ extract.py
│  └─ chat_llm.py
├─ specs/                          # ⬅️ 그래프 정의/다이어그램/엣지표
│  ├─ counseling_rag.graph.yaml    # 엔트리=classify
│  ├─ counseling_rag.flow.mmd
│  └─ counseling_rag.edges.csv
└─ Taeho_build_graph.py            # ⬅️ YAML 로더/컴파일러


규칙: 정의 파일 3종은 반드시 graph/specs/에 위치합니다.

그래프 스펙 요약

노드(10): classify, search_vectordb, eval, sql_search, state_check, question, answer, slot_memory, extract, chat_llm

주요 분기

classify: information → search_vectordb, counseling → state_check, else → END

eval: verified_chunks 없으면 END, 있으면 sql_search (+항상 chat_llm 팬아웃)

상담 루프: state_check ↔ question → answer, 모두 충족 시 slot_memory

slot_memory는 chat_llm과 extract로 팬아웃, extract → search_vectordb 재검색 합류

정상 종료는 chat_llm → END 경로

모델 매핑

eval 노드: gpt-5-mini

그 외 모든 노드: gpt-5-nano

모든 LLM 파라미터: 기본값 사용 (추가 설정 없음)

각 노드 파일 내부에서 모델을 선택하도록 구현되어야 합니다. (예: eval.py만 mini, 나머지 nano)

실행 방법

프로젝트 루트에서:

python -m graph.Taeho_build_graph
# 또는
python graph/Taeho_build_graph.py


성공 시:

“Graph compiled from: …” 메시지 출력

환경이 지원하면 Mermaid 다이어그램 텍스트도 콘솔에 출력

파일 상세
1) graph/specs/counseling_rag.graph.yaml

정적 연결 정의(엔트리, 노드 id, 엣지 목록)를 담습니다.

로더는 nodes[].id 와 edges[](문자열 "A -> B")만 사용합니다.

조건/가드는 CSV나 노드 내부 로직에서 처리하세요.

2) graph/specs/counseling_rag.flow.mmd

Mermaid 다이어그램 소스입니다.

렌더는 VS Code 플러그인 또는 CLI(mmdc) 사용 권장.

산출물 PNG가 필요하면 graph/assets/를 만들어 저장(커밋은 선택).

3) graph/specs/counseling_rag.edges.csv

컬럼: from,to,condition,notes

코드 리뷰/테스트에서 분기 조건을 사람이 읽기 쉽게 확인하는 용도.

핵심 경로 존재 여부를 테스트에서 어설션합니다.

로더(컴파일러) 개요 — graph/Taeho_build_graph.py

counseling_rag.graph.yaml을 읽어 StateGraph(dict) 생성

nodes/*.py에서 동일 이름의 *_node(state) 함수를 import 후 바인딩

"A -> B" 형태의 엣지를 순회하며 LangGraph에 등록

END는 LangGraph 전용 심볼로 변환

노드 파일명과 YAML의 id는 1:1 매칭을 권장합니다. 이름이 다르면 NODE_IMPL 매핑만 맞추면 됩니다.

테스트 가이드(선택)

간단한 스냅샷 테스트 예시:

# tests/test_graph_paths.py
from graph.Taeho_build_graph import get_app

def test_core_paths_exist():
    app = get_app()
    g = app.get_graph()
    edges = {(e[0], e[1]) for e in g.edges}
    assert ("classify", "search_vectordb") in edges
    assert ("classify", "state_check") in edges
    assert ("search_vectordb", "eval") in edges
    assert ("eval", "chat_llm") in edges
    assert any(dst == "END" for (_, dst) in edges)

팀 운영 규칙(권장)

정의 수정 PR엔 반드시 3종 파일(YAML/Mermaid/CSV) 동시 업데이트 포함

노드/에이전트 코드 변경 시, 이름/매핑 유지 또는 NODE_IMPL 갱신

모델 정책 변경 시: 해당 노드 파일 내 모델 지정만 수정 (스펙 파일은 그대로)

PNG 등 산출물은 필요할 때만 커밋 (용량 증가 방지)

FAQ

Q. 조건부 엣지를 YAML에 직접 넣을 수 없나요?
A. 현재 로더는 단순/안정성을 위해 정적 엣지만 읽습니다. 조건은 CSV/노드 로직에서 관리합니다. 필요하면 조건부 엣지 파서를 확장할 수 있습니다.

Q. 왜 엔트리가 classify인가요?
A. 입력 전처리를 그래프 밖(호출자 레이어)에서 처리한다는 팀 합의에 따른 것입니다.

Q. Mermaid가 콘솔에 안 나와요.
A. 환경에 따라 다릅니다. 다이어그램은 .flow.mmd 파일을 에디터/CLI에서 렌더하세요.