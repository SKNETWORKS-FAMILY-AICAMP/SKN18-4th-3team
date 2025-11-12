"""
Memory Agent
------------

[기능 설명]
- 모든 slot 데이터를 통합하고 관리하는 에이전트
- slot의 정보를 하나의 상담 컨텍스트로 결합
- extract_node와 chat_llm_node로 동시에 데이터 전달

[입력 State]
- slot_data: dict - 모든 slot에 수집된 데이터
  * slot_1: str -
  * slot_2: str - 
  * slot_3: str - 
  * slot_4: str - 
  * slot_5: str - 
  * slot_6: str - 
  * slot_7: str - 
- slot_status: dict - 모든 slot 충족 확인 (모두 True여야 함)

[출력 State]
- slot_data: dict - 통합된 slot 데이터 (전달)
- counseling_context: str - 모든 slot 데이터를 결합한 텍스트
  * 형식: "slot_1: 답변1\nslot_2: 답변2\n..."
  * LLM이 이해하기 쉬운 형태로 구조화
- all_slots_filled: bool - 모든 slot 충족 여부 (항상 True)

[데이터 흐름]
slot_memory 노드는 두 방향으로 동시에 데이터 전달:
1. extract 노드: 증상 추출 및 분석
2. chat_llm 노드: 최종 답변 생성

"""

from graph.nodes.slot_memory_node import slot_memory_node


def memory_agent(state):
    """
    Slot 데이터를 통합하는 에이전트
    
    Args:
        state: GraphState - slot_data, slot_status를 포함한 상태
        
    Returns:
        dict: slot_data, counseling_context, all_slots_filled를 포함한 상태
    """
    result = slot_memory_node(state)
    return result


def route_after_memory(state):
    """
    메모리 저장 후 다음 노드를 결정하는 라우팅 함수
    
    ※ 주의: 이 함수는 실제로 사용되지 않음
    ※ build_graph.py에서 직접 엣지로 연결됨
    
    Args:
        state: GraphState - all_slots_filled를 포함한 상태
        
    Returns:
        str: 다음 노드 이름 (이론상)
            - "extract": 모든 slot 충족 (정상 케이스)
            - "state_check": slot 미충족 (예외 케이스)
    """
    all_slots_filled = state.get("all_slots_filled", False)
    
    if all_slots_filled:
        # 정상: 증상 추출로 이동
        return "extract"
    else:
        # 예외: slot 재확인 (발생하지 않아야 함)
        return "state_check"
