"""
[역할]
미충족 slot에 대한 질문 생성

[Slot별 질문 예시]
- 감정	요즘 어떤 감정을 자주 느끼시나요?
- 상황	언제부터 이런 감정이 드셨나요?
- 신체	수면, 식사, 피로감 변화 있으신가요?
- 사고	자신에 대한 생각이 달라지셨나요?
- 행동	이런 감정을 느낄 때 어떻게 반응하시나요?
- 관계	이런 이야기를 나눌 수 있는 사람이 있나요?
- 권유	이런 상태가 지속된다면 상담 받아보시는 건 어떤가요?

[입력]
- current_slot: 질문할 slot 번호
# - slot_status: 각 slot 충족 여부

[출력]
- bot_question: 생성된 질문 (화면에 표시할 텍스트)
- current_slot: 질문 대상 slot 번호
"""

def question_node(state):
    """
    미충족 slot에 대한 질문을 생성하는 노드
    """

    # state_check_node에서 전달받은 현재 질문할 slot 번호
    current_slot = state.get("current_slot")
    
    # current_slot에 맞는 질문 생성
    slot_questions = {
        "slot_1": "요즘 어떤 감정을 자주 느끼시나요?",
        "slot_2": "언제부터 이런 감정이 드셨나요?",
        "slot_3": "수면, 식사, 피로감 등에 변화가 있으신가요?",
        "slot_4": "자신에 대한 생각이 달라지셨나요?",
        "slot_5": "이런 감정을 느낄 때 어떻게 반응하시나요?",
        "slot_6": "이런 이야기를 나눌 수 있는 사람이 있나요?",
        "slot_7": "이런 상태가 지속된다면 전문 상담을 받아보시는 건 어떤가요?",
    }

    # current_slot에 해당하는 질문을 가져옴
    bot_question = slot_questions.get(current_slot, "추가 정보를 알려주세요.")
    
    return {
        "bot_question": bot_question,  # 사용자에게 표시할 질문 텍스트
        "current_slot": current_slot,  # answer_node에서 사용할 slot 번호
    }
