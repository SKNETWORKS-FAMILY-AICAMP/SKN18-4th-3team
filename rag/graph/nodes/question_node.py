"""
[역할]
미충족 slot에 대한 질문 생성

[Slot별 질문 예시]
- *감정* - 요즘 어떤 감정을 자주 느끼시나요?
- *상황* - 언제부터 이런 감정이 드셨나요?
- *신체* - 수면, 식사, 피로감 변화 있으신가요?
- *사고* - 자신에 대한 생각이 달라지셨나요?
- *행동* - 이런 감정을 느낄 때 어떻게 반응하시나요?
- *관계* - 이런 이야기를 나눌 수 있는 사람이 있나요?
- *권유* - 이런 상태가 지속된다면 상담 받아보시는 건 어떤가요?

[입력]
- current_slot: 질문할 slot 번호
- initial_question: 최초 질문
- slot_data: 이미 수집된 slot 정보

[출력]
- bot_question: 생성된 질문 (화면에 표시할 텍스트)
- current_slot: 질문 대상 slot 번호
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


# Slot별 목적과 의도 정의
SLOT_DEFINITIONS = {
    "slot_1": {
        "name": "감정 상태",
        "purpose": "사용자가 현재 느끼는 감정 상태를 파악",
        "context": "우울함, 불안함, 무기력함, 짜증, 외로움 등의 감정",
        "tone": "부드럽고 공감적으로 감정을 표현할 수 있도록 유도"
    },
    "slot_2": {
        "name": "상황 및 시기",
        "purpose": "감정이 시작된 시기나 계기가 된 상황을 파악",
        "context": "언제부터 시작되었는지, 어떤 사건이나 상황과 관련이 있는지",
        "tone": "부담 없이 자연스럽게 상황을 이야기할 수 있도록 유도"
    },
    "slot_3": {
        "name": "신체적 변화",
        "purpose": "수면, 식사, 피로감 등 신체적 변화를 파악",
        "context": "불면증, 식욕 변화, 과식, 피로감, 두통, 신체 통증 등",
        "tone": "걱정하는 톤으로 신체 건강에 대해 물어보기"
    },
    "slot_4": {
        "name": "사고 패턴",
        "purpose": "자기 인식이나 생각의 변화를 파악",
        "context": "자책감, 부정적 사고, 무가치함, 집중력 저하, 의욕 저하 등",
        "tone": "조심스럽고 이해심 있게 내면의 생각을 표현할 수 있도록 유도"
    },
    "slot_5": {
        "name": "행동 패턴",
        "purpose": "행동 패턴의 변화를 파악",
        "context": "사회적 회피, 활동 감소, 외출 기피, 취미 상실, 일상 루틴 변화 등",
        "tone": "판단하지 않고 중립적으로 행동 변화에 대해 물어보기"
    },
    "slot_6": {
        "name": "대인관계",
        "purpose": "대인관계 상태와 지지 체계를 파악",
        "context": "가족, 친구, 동료와의 관계, 고립감, 사회적 지지 여부 등",
        "tone": "따뜻하고 지지적인 톤으로 관계에 대해 물어보기"
    },
    "slot_7": {
        "name": "전문 상담 의향",
        "purpose": "전문 상담이나 치료에 대한 의향과 태도를 파악",
        "context": "상담 의향, 병원 방문 의사, 전문가 도움에 대한 생각 등",
        "tone": "강요하지 않고 부드럽게 제안하는 톤으로 물어보기"
    }
}


def generate_question_with_llm(current_slot, initial_question, slot_data):
    """
    LLM을 사용하여 slot별로 상담하듯이 부드러운 질문을 생성

    Args:
        current_slot: 질문할 slot 번호
        initial_question: 사용자의 최초 질문
        slot_data: 이미 수집된 slot 정보

    Returns:
        str: 생성된 질문
    """
    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 현재 slot 정의 가져오기
    slot_def = SLOT_DEFINITIONS.get(current_slot, {})
    slot_name = slot_def.get("name", "추가 정보")
    slot_purpose = slot_def.get("purpose", "추가 정보 수집")
    slot_context = slot_def.get("context", "")
    slot_tone = slot_def.get("tone", "부드럽게 질문하기")

    # 이미 수집된 정보 요약
    collected_info = ""
    if slot_data:
        collected_info = "\n".join([
            f"- {SLOT_DEFINITIONS.get(slot, {}).get('name', slot)}: {info}"
            for slot, info in slot_data.items()
        ])

    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        당신은 따뜻하고 공감적인 전문 심리상담가입니다.
        사용자와 자연스럽고 부드러운 대화를 통해 필요한 정보를 수집하는 것이 목표입니다.

        **역할:**
        - 사용자의 감정을 존중하고 공감하는 태도로 질문
        - 강압적이거나 심문하는 느낌이 아닌, 자연스러운 대화 흐름 유지
        - 짧고 간결하면서도 따뜻한 질문 생성 (1-2문장)
        - 존댓말 사용 및 부드러운 어조 유지

        **주의사항:**
        - 질문만 생성하고 다른 설명이나 답변은 포함하지 마세요
        - 의학적 진단이나 전문 용어는 피하세요
        - 사용자가 이미 언급한 내용을 다시 묻지 마세요
        - 자연스럽고 대화체로 질문하세요
        """),

        ("user", """
        **현재 상황:**
        사용자의 최초 질문: {initial_question}

        **이미 수집된 정보:**
        {collected_info}

        **지금 질문해야 할 주제:**
        - 주제: {slot_name}
        - 목적: {slot_purpose}
        - 맥락: {slot_context}
        - 톤: {slot_tone}

        **요청:**
        위 정보를 바탕으로, 사용자에게 "{slot_name}"에 대해 부드럽고 자연스럽게 질문을 생성해주세요.
        사용자의 최초 질문과 이미 수집된 정보를 참고하여, 맥락에 맞는 질문을 만들어주세요.
        """)
    ])

    try:
        # LLM 체인 생성 및 호출
        chain = prompt | llm
        response = chain.invoke({
            "initial_question": initial_question or "처음 방문",
            "collected_info": collected_info if collected_info else "아직 수집된 정보가 없습니다.",
            "slot_name": slot_name,
            "slot_purpose": slot_purpose,
            "slot_context": slot_context,
            "slot_tone": slot_tone
        })

        # 생성된 질문 반환
        generated_question = response.content.strip()
        return generated_question

    except Exception as e:
        print(f"Error generating question with LLM: {e}")
        # LLM 호출 실패 시 출력
        return (current_slot, "좀 더 자세히 말씀해주시겠어요?")


def question_node(state):
    """
    미충족 slot에 대한 질문을 LLM을 통해 생성하는 노드
    """
    # state에서 필요한 정보 가져오기
    current_slot = state.get("current_slot")
    initial_question = state.get("initial_question", "")
    slot_data = state.get("slot_data", {})

    # LLM을 사용하여 맥락에 맞는 질문 생성
    bot_question = generate_question_with_llm(
        current_slot=current_slot,
        initial_question=initial_question,
        slot_data=slot_data
    )

    return {
        "bot_question": bot_question,  # 사용자에게 표시할 질문 텍스트
        "current_slot": current_slot,  # answer_node에서 사용할 slot 번호
    }
