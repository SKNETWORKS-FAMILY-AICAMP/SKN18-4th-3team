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
    # state 안에서 지금까지 모인 정보(slot_data)를 꺼냅니다.
    # 정보가 하나도 없다면 빈 딕셔너리({})를 사용합니다.
    slot_data = state.get("slot_data", {})

    # 각 slot이 채워졌는지(True/False) 상태를 꺼냅니다.
    # state에 값이 없으면 기본으로 모두 False로 시작합니다.
    slot_status = state.get(
        "slot_status",
        {
            "slot_1": False,
            "slot_2": False,
            "slot_3": False,
            "slot_4": False,
            "slot_5": False,
            "slot_6": False,
            "slot_7": False,
        },
    )
    
    # slot_data에 담긴 내용을 보기 좋은 문자열로 합칩니다.
    # 예) "slot_1: 사용자가 말한 내용"
    counseling_context = "\n".join([
        f"{slot}: {data}" 
        for slot, data in slot_data.items()
    ])
    
    # 모든 slot의 상태가 True인지 확인합니다.
    # 하나라도 False가 있으면 전체가 False가 됩니다.
    all_slots_filled = all(slot_status.values()) if slot_status else False
    
    # 다음 노드에서 사용할 값을 한 번에 돌려줍니다.
    return {
        "slot_data": slot_data,
        "counseling_context": counseling_context,
        "all_slots_filled": all_slots_filled
    }
