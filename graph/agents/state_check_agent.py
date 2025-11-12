"""
[역할]
state_check_node 실행 후 slot 충족 여부에 따라 다음 노드로 라우팅

[라우팅 로직]
1. state_check_node에서 모든 slot 충족 (all 채워짐)
    → slot_memory_node로 이동
    → 수집 완료, 데이터 통합 단계로 이동

2. 미충족 slot 존재 (하나라도 비어있으면)
    → question_node로 이동
    → 추가 정보 수집 필요
"""

import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


def extract_slot_info(user_input, slot_status):
    """
    LLM을 사용하여 사용자 입력에서 slot 정보 추출

    Args:
        user_input: 사용자 입력 텍스트
        slot_status: 현재 slot 충족 상태 (dict)

    Returns:
        dict: 추출된 slot 정보 (예: {"slot_1": "우울하고 불안해요"})
    """
    # 이미 채워진 slot 제외 - all 채워지면 slot은 건너뛰고, 비워진 slot만 추출 대상으로 설정
    unfilled_slots = [slot for slot, filled in slot_status.items() if not filled]
    # 모든 slot이 채워졌으면 빈 {} 반환
    if not unfilled_slots:
        return {}

    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        당신은 정신건강 상담 챗봇의 정보 추출 전문가입니다.
        사용자의 입력을 분석하여 다음 7가지 slot 카테고리에 해당하는 정보를 추출해야 합니다:

        **Slot 정의:**
        - slot_1 (감정): 사용자가 느끼는 감정 상태
        예: 우울함, 불안함, 무기력함, 짜증남, 외로움 등

        - slot_2 (상황): 감정이 시작된 시기나 계기가 된 상황
        예: 2주 전부터, 실직 후, 이별 후, 최근에, 한 달 전 등

        - slot_3 (신체): 수면, 식사, 피로감 등 신체적 변화
        예: 불면증, 식욕 감퇴, 과식, 피로감, 두통 등

        - slot_4 (사고): 자기 인식이나 생각의 변화
        예: 자책감, 부정적 사고, 무가치함, 집중력 저하 등

        - slot_5 (행동): 행동 패턴의 변화
        예: 사회적 회피, 활동 감소, 외출 기피, 취미 상실 등

        - slot_6 (관계): 대인관계 상태
        예: 가족 관계 좋음, 친구 없음, 외톨이, 지지자 있음 등

        - slot_7 (권유): 전문 상담에 대한 의향이나 태도
        예: 상담 받고 싶음, 병원 가기 싫음, 도움 필요함 등

        **작업 지침:**
        1. 사용자 입력에서 위 7개 slot에 해당하는 정보를 추출하세요.
        2. 정보가 명확하게 포함된 slot만 추출하세요.
        3. 추측하거나 지어내지 마세요. 입력에 없는 정보는 빈 문자열로 반환하세요.
        4. 각 slot의 정보는 사용자 입력을 요약하여 핵심만 간결하게 작성하세요.
        5. 반드시 JSON 형식으로만 반환하세요.

        **반환 형식 (JSON만):**
        {{
            "slot_1": "추출된 감정 정보 또는 빈 문자열",
            "slot_2": "추출된 상황 정보 또는 빈 문자열",
            "slot_3": "추출된 신체 정보 또는 빈 문자열",
            "slot_4": "추출된 사고 정보 또는 빈 문자열",
            "slot_5": "추출된 행동 정보 또는 빈 문자열",
            "slot_6": "추출된 관계 정보 또는 빈 문자열",
            "slot_7": "추출된 권유 정보 또는 빈 문자열"
        }}

        **주의:**
        - JSON 형식만 반환하고, 다른 설명이나 텍스트는 포함하지 마세요.
        - 코드 블록(```)을 사용하지 마세요."""),
                
        ("user", """사용자 입력: {user_input}

        현재 채워지지 않은 slot: {unfilled_slots}

        위 입력에서 정보를 추출해주세요.""")
    ])

    # LLM 체인 생성
    chain = prompt | llm
    try:
        # LLM 호출 - 사용자 입력과 미충족 slot 리스트를 전달
        response = chain.invoke({
            "user_input": user_input,
            "unfilled_slots": ", ".join(unfilled_slots)
        })
        
        # JSON 파싱
        result = json.loads(response.content)

        # 빈 문자열인 slot 제거 
        extracted_info = {
            slot: info
            for slot, info in result.items()
            if info and info.strip() # 빈 문자열이나 공백이 있으면 제외
        }
        return extracted_info

    except Exception as e:
        print(f"Error extracting slot info: {e}")
        return {}


def route_after_state_check(state):
    """
    라우팅 함수
    
    Returns:
        "slot_memory": 모든 slot 충족(7개 모두 True)
        "question": 미충족 slot 존재(하나라도 False)
    """
    slot_status = state.get("slot_status", {})

    # 모두 채워지면 채워진 state 반환
    all_filled = all(slot_status.values()) if slot_status else False

    # 모든 slot 충족 시 ->  slot_memory, 아니면 -> question
    return "slot_memory" if all_filled else "question"
