"""
Slot Memory Node
----------------

[기능 설명]
- 모든 slot이 충족되었을 때 실행되는 노드
- 수집된 모든 slot 데이터를 통합하여 저장
- extract_node와 chat_llm_node로 데이터 전달

[입력 State]
- slot_data: dict - 모든 slot에 수집된 데이터
  - slot_1: 
  - slot_2:
  - slot_3:
  - slot_4: 
  - slot_5: 
  - slot_6: 
  - slot_7: 
- slot_status: dict - 모든 slot 충족 확인

[출력 State]
- slot_data: dict - 통합된 slot 데이터 (전달)
- counseling_context: str - 상담 컨텍스트 (모든 slot 데이터 결합)
- all_slots_filled: bool - 모든 slot 충족 여부 (true)

[다음 노드]
- extract_node (증상 추출)
- chat_llm_node (최종 답변 생성)
"""

def slot_memory_node(state):
    """
    모든 slot 데이터를 통합하여 저장하는 노드
    """
    slot_data = state.get("slot_data", {})
    slot_status = state.get("slot_status", {})
    
    # 모든 slot 데이터를 하나의 컨텍스트로 결합
    counseling_context = "\n".join([
        f"{slot}: {data}" 
        for slot, data in slot_data.items()
    ])
    
    # TODO: 모든 slot이 충족되었는지 
    
    return {
        "slot_data": slot_data,
        "counseling_context": counseling_context,
        "all_slots_filled": all_slots_filled
    }
