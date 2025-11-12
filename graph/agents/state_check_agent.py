"""
State Check Agent
-----------------

[역할]
state_check_node 실행 후 slot 충족 여부에 따라 다음 노드로 라우팅

[라우팅 로직]
1. 모든 slot 충족 (all True)
   → slot_memory 노드
   → 수집 완료, 데이터 통합 단계로 이동
   
2. 미충족 slot 존재 (하나라도 False)
   → question 노드
   → 추가 정보 수집 필요
"""

from graph.nodes.state_check_node import state_check_node


def state_check_agent(state):
    """Node 실행"""
    return state_check_node(state)


def route_after_state_check(state):
    """
    라우팅 함수
    
    Returns:
        "slot_memory": 모든 slot 충족
        "question": 미충족 slot 존재
    """
    slot_status = state.get("slot_status", {})
    all_filled = all(slot_status.values()) if slot_status else False
    
    return "slot_memory" if all_filled else "question"
