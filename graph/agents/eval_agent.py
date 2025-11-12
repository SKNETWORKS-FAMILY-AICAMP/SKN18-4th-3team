"""
Eval Agent
----------

[역할]
eval_node 실행 후 검증된 chunk 유무에 따라 라우팅

[데이터 흐름]
eval에서 verified_chunks를 두 방향으로 동시 전달:
1. sql_search → 이미지 검색
2. chat_llm → 원본 chunk 전달

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

from graph.nodes.eval_node import eval_node


def eval_agent(state):
    """Node 실행"""
    return eval_node(state)


def route_after_eval(state):
    """
    라우팅 함수
    
    Returns:
        "__end__": chunk 없음 (답변 불가)
        "sql_search": chunk 있음 (이미지 검색)
        
    Note: 
        chunk 있을 때 eval → chat_llm 직접 엣지도 있음 (build_graph.py에서 정의)
    """
    verified_chunks = state.get("verified_chunks", [])
    
    if not verified_chunks:
        # 검증된 chunk 없음 → 답변 불가 → 종료
        return "__end__"
    else:
        # 검증된 chunk 있음 → 이미지 검색
        # (동시에 eval → chat_llm 직접 엣지로 chunk도 전달됨)
        return "sql_search"
