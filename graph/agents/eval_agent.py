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

[임계값]
- score >= 0.7: 관련성 높은 chunk (통과)
- score < 0.7: 관련성 낮음 (제외)
"""

from typing import Dict, Any, List
from graph.nodes.eval_node import eval_node


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


def route_after_eval(state):
    """
    라우팅 함수
    
    Returns:
        "__end__": chunk 없음 (답변 불가)
        "sql_search": chunk 있음 + 이미지 검색 필요
        "chat_llm": chunk 있음 + 이미지 검색 불필요 (바로 답변)
        
    Note: 
        - 검증된 chunk가 존재하면:
          * chunk_id가 있으면 → sql_search (이미지 검색)
          * chunk_id가 없으면 → chat_llm (바로 답변)
        - sql_search를 거치면 자동으로 chat_llm으로 이동
    """
    verified_chunks: List[Dict[str, Any]] = state.get("verified_chunks") or []
    
    if not verified_chunks:
        # 검증된 chunk 없음 → 답변 불가 → 종료
        return "__end__"
    
    # chunk_id가 있는지 확인 (이미지 검색 가능 여부)
    has_chunk_id = any(
        chunk.get("chunk_id") or chunk.get("metadata", {}).get("chunk_id")
        for chunk in verified_chunks
    )
    
    if has_chunk_id:
        # chunk_id 있음 → 이미지 검색 후 답변
        return "sql_search"
    else:
        # chunk_id 없음 → 바로 답변
        return "chat_llm"
        