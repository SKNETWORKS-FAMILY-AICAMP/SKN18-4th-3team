"""
Answer Node
-----------

[역할]
사용자 답변을 현재 slot에 저장

[입력]
- user_answer: 사용자의 답변
- current_slot: 답변 대상 slot 번호
- slot_data: 기존 slot 데이터 (누적)
- slot_status: 기존 slot 상태

[출력]
- user_question: 사용자 답변 (state_check로 전달용)
- slot_data: 업데이트된 slot 데이터 (누적)
- slot_status: 업데이트된 slot 상태 (답변한 slot은 True)

[다음 노드]
→ state_check_node (slot 상태 재확인)

[데이터 누적 예시]
1차: slot_data = {"slot_1": "우울해요"}, slot_status = {"slot_1": True, ...}
2차: slot_data = {"slot_1": "우울해요", "slot_2": "2주"}, slot_status = {"slot_1": True, "slot_2": True, ...}
3차: slot_data = {"slot_1": "우울해요", "slot_2": "2주", "slot_3": "심각"}, slot_status = {"slot_1": True, "slot_2": True, "slot_3": True, ...}
"""


def answer_node(state):
    """
    사용자 답변을 받아 slot에 저장하는 노드
    """
    user_answer = state.get("user_answer", "")
    current_slot = state.get("current_slot")
    slot_data = state.get("slot_data", {})
    slot_status = state.get("slot_status", {})

    # 현재 slot에 사용자 답변 저장 및 상태 업데이트
    if current_slot and user_answer:
        slot_data[current_slot] = user_answer
        slot_status[current_slot] = True

    return {
        "user_question": user_answer,  # state_check로 전달용
        "slot_data": slot_data,
        "slot_status": slot_status,
    }
