"""
Answer Node
-----------

[역할]
사용자 답변을 현재 slot에 저장

[입력]
- user_answer: 사용자의 답변
- current_slot: 답변 대상 slot 번호
- slot_data: 기존 slot 데이터 (누적)

[출력]
- user_question: 사용자 답변 (state_check로 전달)
- slot_data: 업데이트된 slot 데이터 (누적)

[다음 노드]
→ state_check_node (slot 상태 재확인)

[데이터 누적 예시]
1차: slot_data = {"slot_1": "우울해요"}
2차: slot_data = {"slot_1": "우울해요", "slot_2": "2주"}
3차: slot_data = {"slot_1": "우울해요", "slot_2": "2주", "slot_3": "심각"}
"""


def answer_node(state):
    """
    사용자 답변을 받아 slot에 저장하는 노드
    """
    user_answer = state.get("user_answer", "")
    current_slot = state.get("current_slot")
    slot_data = state.get("slot_data", {})

    # 현재 slot에 사용자 답변 저장
    if current_slot:
        slot_data[current_slot] = user_answer

    return {
        "user_question": user_answer,
        "slot_data": slot_data,
    }
