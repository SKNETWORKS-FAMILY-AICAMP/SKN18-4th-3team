"""
[역할]
사용자 입력에서 정보를 추출하여 slot에 저장

[처리 로직]
1. 사용자 입력 분석 (LLM 사용)
2. 입력에서 slot에 해당하는 정보 추출
3. 추출된 정보를 slot_data에 저장
4. 해당 slot_status를 True로 업데이트
5. 다음 미충족 slot 찾기

[입력]
- user_question: 사용자의 현재 입력 (최초 질문 또는 답변)
- initial_question: 최초 질문 (보관용)
- slot_status: 각 slot 충족 여부 (초기: 모두 False)
- slot_data: 각 slot에 저장된 정보 (초기: 빈 dict)

[출력]
- initial_question: 최초 질문 보관
- slot_status: 업데이트된 충족 여부 (정보 추출된 slot은 True)
- slot_data: 추출된 정보 저장 (예: {"slot_1": "우울하고 불안해요"})
- current_slot: 다음 미충족 slot 번호
"""

from graph.agents.state_check_agent import extract_slot_info

def state_check_node(state):
    """
    사용자 입력에서 정보를 추출하여 slot에 저장하는 노드
    """
    user_input = state.get("user_question", "")
    initial_question = state.get("initial_question")
    current_slot = state.get("current_slot")  # 현재 질문 중인 slot
    
    # 최초 질문 보관 (첫 실행 시에만) -> 이후 loop에서는 initial_question가 계속 유지됨
    if not initial_question:
        initial_question = user_input
    
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
    # 예: {"slot_1": "우울하고 불안해요", } 형태로 저장
    slot_data = state.get("slot_data", {})

    # 초기 질문이거나 answer_node를 거쳐온 경우에만 정보 추출
    # (question_node를 거치지 않은 경우는 초기 질문)
    if not current_slot or state.get("user_answer"):
        # LLM을 사용하여 사용자 입력에서 slot 정보 추출
        extracted_info = extract_slot_info(user_input, slot_status)

        for slot_num, info in extracted_info.items():
            if info:
                slot_data[slot_num] = info
                slot_status[slot_num] = True

    # 다음 미충족 slot 찾기(slot_1부터 확인)
    next_slot = None
    for slot_num, is_filled in slot_status.items():
        if not is_filled:
            next_slot = slot_num
            break

    # 업데이트 상태 반환
    return {
        "initial_question": initial_question,
        "slot_status": slot_status,
        "slot_data": slot_data,
        "current_slot": next_slot,
    }
