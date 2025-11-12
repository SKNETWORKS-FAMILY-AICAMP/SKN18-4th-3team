"""
Classify Agent
--------------

[기능 설명]
- 사용자 질문을 분류하고 적절한 노드로 라우팅하는 에이전트
- LLM을 사용하여 질문의 의도를 파악하고 3가지 유형으로 분류
1. 정신질환 정보형: 정신질환에 대한 지식, 정보를 요청하는 질문
2. 상담형: 개인의 증상이나 상태에 대한 상담을 원하는 질문
3. 분류 불가: 정신건강과 무관하거나 부적절한 질문

[입력 State]
- user_question: str - 사용자가 입력한 질문 (필수)

[출력 State]
- user_question: str - 사용자 질문 (다음 노드로 전달)
- question_type: str - 질문 유형
  * "information": 정보형 질문
  * "counseling": 상담형 질문
  * "unknown": 분류 불가능한 질문

[분기 조건 (route_after_classify)]
1. question_type == "information"
→ search_vectordb 노드로 이동
→ Vector DB에서 관련 정보 검색 시작

2. question_type == "counseling"
→ state_check 노드로 이동
→ 상담을 위한 slot 수집 프로세스 시작

3. question_type == "unknown" 또는 기타
→ __end__ (종료)
→ "죄송합니다. 정신건강 관련 질문만 답변 가능합니다." 메시지 반환
"""

from graph.nodes.classify_node import classify_node


def classify_agent(state):
    """
    질문을 분류하고 라우팅하는 에이전트
    
    Args:
        state: GraphState - user_question을 포함한 상태
        
    Returns:
        dict: user_question, question_type을 포함한 업데이트된 상태
    """
    result = classify_node(state)
    return result


def route_after_classify(state):
    """
    분류 결과에 따라 다음 노드를 결정하는 라우팅 함수
    
    Args:
        state: GraphState - question_type을 포함한 상태
        
    Returns:
        str: 다음 노드 이름
            - "search_vectordb": 정보형 질문 처리
            - "state_check": 상담형 질문 처리
            - "__end__": 분류 불가능한 질문 (종료)
    """
    question_type = state.get("question_type", "")
    
    if question_type == "information":
        # 정보형: Vector DB 검색으로 이동
        return "search_vectordb"
    elif question_type == "counseling":
        # 상담형: Slot 수집 프로세스로 이동
        return "state_check"
    else:
        # 분류 불가능: 즉시 종료
        return "__end__"
