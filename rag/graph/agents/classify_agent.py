"""
Classify Agent
--------------

[기능 설명]
- 사용자 질문을 분류하고 적절한 노드로 라우팅하는 에이전트
- LLM/규칙 기반으로 질문 의도를 3가지 유형으로 분류

[입력 State]
- user_question: str (필수)

[출력 State]
- user_question: str
- question_type: "information" | "counseling" | "unknown"
"""

from typing import Dict, Any
from rag.graph.nodes.classify_node import classify_node

_ALLOWED = {"information", "counseling", "unknown"}

def _normalize_question_type(value: Any) -> str:
    v = (str(value or "").strip().lower())
    return v if v in _ALLOWED else "unknown"

def classify_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    질문을 분류하고 라우팅 키(question_type)를 설정합니다.
    """
    if not isinstance(state, dict):
        state = {}

    # classify_node가 내부적으로 분류해 state["question_type"]을 채움
    result = classify_node(state) or {}
    result["question_type"] = _normalize_question_type(result.get("question_type"))

    # user_question 누락/공백 대응(안전)
    uq = result.get("user_question")
    if not isinstance(uq, str) or not uq.strip():
        result["question_type"] = "unknown"

    return result

def route_after_classify(state: Dict[str, Any]) -> str:
    """
    분류 결과에 따라 다음 노드를 결정
      - "search_vectordb": 정보형
      - "state_check": 상담형
      - "__end__": 분류 불가
    """
    qtype = _normalize_question_type(state.get("question_type"))

    if qtype == "information":
        return "search_vectordb"
    elif qtype == "counseling":
        return "state_check"
    else:
        return "__end__"
