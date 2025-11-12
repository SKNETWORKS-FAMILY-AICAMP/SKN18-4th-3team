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


# memory_agent는 조건부 분기 없이 extract_node/chat_llm 노드로 통합된 전체 Text를 보냄