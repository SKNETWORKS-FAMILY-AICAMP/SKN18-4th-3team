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
    memory_agent는 상담 도중 모인 정보를 보기 좋게 정리하는 간단한 전달자 역할을 합니다.

    우리가 하는 일은 아래 3단계로 끝입니다.
    1) 이미 다른 곳에서 모아 둔 slot 정보를 그대로 받아옵니다.
    2) 그 정보를 `slot_memory_node`에 넘겨 정리된 문장으로 바꿔 달라고 부탁합니다.
    3) 정리된 결과를 그대로 다음 단계(extract, chat LLM)에서 쓰도록 돌려줍니다.

    Args:
        state (GraphState): 상담에서 쌓인 정보를 담은 상자입니다.
            - state["slot_data"]: 질문별 사용자 답변 모음 (예: 이름, 증상, 기간 등)
            - state["slot_status"]: 모든 질문에 답했는지를 표시한 값

    Returns:
        dict: 다음 단계에서 바로 사용할 수 있는 깔끔한 정보 묶음입니다.
            - "slot_data": 원래 slot 정보 그대로
            - "counseling_context": slot 정보를 한 문서처럼 이어 붙인 문장
            - "all_slots_filled": 모든 slot이 채워졌는지 여부(True 또는 False)
    """

    # 실제 정리(문장 만들기)는 slot_memory_node에서 처리합니다.
    result = slot_memory_node(state)

    # 정리된 결과를 그대로 돌려줍니다.
    return result


# memory_agent는 조건부 분기 없이 extract_node/chat_llm 노드로 통합된 전체 Text를 보냄