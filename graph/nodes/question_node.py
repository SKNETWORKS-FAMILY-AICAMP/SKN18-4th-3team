"""
Question Node
-------------

[역할]
미충족 slot에 대한 질문 생성

[Slot별 질문 예시]

[입력]
- current_slot: 질문할 slot 번호
- slot_status: 각 slot 충족 여부

[출력]
- bot_question: 생성된 질문 (화면에 표시할 텍스트)
- current_slot: 질문 대상 slot 번호
"""

def question_node(state):
    """
    미충족 slot에 대한 질문을 생성하는 노드
    """
    current_slot = state.get("current_slot")
    slot_status = state.get("slot_status", {})
    
    # TODO: current_slot에 맞는 질문 생성 (+ LLM 사용)
    slot_questions = {
        "slot_1": "",
        "slot_2": "",
        "slot_3": "",
        "slot_4": "",
        "slot_5": "",
        "slot_6": "",
        "slot_7": "",
    }
    
    bot_question = slot_questions.get(current_slot, "추가 정보를 알려주세요.")
    
    return {
        "bot_question": bot_question,
        "current_slot": current_slot,
    }
