"""
Eval Agent
----------

[역할]
eval_node 실행 후 검증된 chunk 유무에 따라 라우팅

[데이터 흐름]
eval에서 verified_chunks를 두 방향으로 동시 전달:
1. sql_search → 이미지 검색(RDB)
2. chat_llm 노드   → 검증된 chunk를 바로 전달

[라우팅 로직]
1. verified_chunks 없음 (빈 리스트)
→ __end__ (종료)
→ "관련 정보를 찾을 수 없습니다." 메시지 반환

2. verified_chunks 있음 (1개 이상)
→ sql_search 노드 (조건부 엣지)
→ 메타데이터로 RDB에서 관련 이미지 검색
동시에 eval → chat_llm (직접 엣지)
→ 검증된 chunk 직접 전달

[최종 결과]
chat_llm은 verified_chunks와 related_images 둘 다 받아서 답변 생성

[점수 정책]
- eval_node에서 chunk별로 다음 두 점수를 계산:
  - question_relevance (0.0 ~ 0.3)
  - answer_helpfulness (0.0 ~ 0.3)
- 두 점수의 합(total_score)을 기준으로 임계값(THRESHOLD) 이상인 것만 verified_chunks에 포함.
"""

from typing import Dict, Any, List
from rag.graph.nodes.eval_node import eval_node


def eval_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    eval_node를 호출하여 검색된 chunk의 관련도를 검증하는 에이전트.
    
    Input:
      - state['user_question']: str
      - state['retrieved_chunks']: List[Dict]
    
    Output:
      - state['user_question']: str
      - state['verified_chunks']: List[Dict]
    """
    return eval_node(state)


def route_after_eval(state: Dict[str, Any]) -> str:
    """
    라우팅 함수
    
    Returns:
        "__end__": chunk 없음 (답변 불가)
        "sql_search": chunk 있음 + 이미지 검색 필요
        "chat_llm": chunk 있음 + 이미지 검색 불필요 (바로 답변)
    """
    verified_chunks: List[Dict[str, Any]] = state.get("verified_chunks") or []

    if not verified_chunks:
        return "__end__"
    else:
        return "sql_search"
        