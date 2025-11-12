"""
그래프 시각화 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict


# State 정의
class GraphState(TypedDict):
    user_question: str
    question_type: Optional[str]
    retrieved_chunks: Optional[List[Dict]]
    verified_chunks: Optional[List[Dict]]
    related_images: Optional[List[str]]
    slot_status: Optional[Dict[str, bool]]
    slot_data: Optional[Dict[str, str]]
    current_slot: Optional[str]
    bot_question: Optional[str]
    user_answer: Optional[str]
    waiting_for_answer: Optional[bool]
    counseling_context: Optional[str]
    all_slots_filled: Optional[bool]
    extracted_symptoms: Optional[Dict]
    final_answer: Optional[str]


# 더미 노드 함수들
def classify_node(state):
    return state

def search_vectordb_node(state):
    return state

def eval_node(state):
    return state

def sql_search_node(state):
    return state

def chat_llm_node(state):
    return state

def state_check_node(state):
    return state

def question_node(state):
    return state

def answer_node(state):
    return state

def slot_memory_node(state):
    return state

def extract_node(state):
    return state


# 라우팅 함수들
def route_after_classify(state):
    question_type = state.get("question_type", "information")
    if question_type == "information":
        return "search_vectordb"
    elif question_type == "counseling":
        return "state_check"
    else:
        return "__end__"

def route_after_eval(state):
    verified_chunks = state.get("verified_chunks", [])
    if not verified_chunks:
        return "__end__"
    else:
        return "sql_search"

def route_after_state_check(state):
    slot_status = state.get("slot_status", {})
    all_filled = all(slot_status.values()) if slot_status else False
    return "slot_memory" if all_filled else "question"

def route_after_memory(state):
    all_slots_filled = state.get("all_slots_filled", False)
    return "extract" if all_slots_filled else "state_check"


def build_graph():
    """
    전체 그래프를 구성하는 함수
    """
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("classify", classify_node)
    workflow.add_node("search_vectordb", search_vectordb_node)
    workflow.add_node("eval", eval_node)
    workflow.add_node("sql_search", sql_search_node)
    workflow.add_node("state_check", state_check_node)
    workflow.add_node("question", question_node)
    workflow.add_node("answer", answer_node)
    workflow.add_node("slot_memory", slot_memory_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("chat_llm", chat_llm_node)
    
    # 엣지 추가
    workflow.set_entry_point("classify")
    
    # classify 후 라우팅 (분류 불가능한 질문은 END로)
    workflow.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "search_vectordb": "search_vectordb",
            "state_check": "state_check",
            "__end__": END
        }
    )
    
    # 정보형 플로우
    workflow.add_edge("search_vectordb", "eval")
    workflow.add_conditional_edges(
        "eval",
        route_after_eval,
        {
            "sql_search": "sql_search",
            "__end__": END
        }
    )
    # eval에서 검증된 chunk를 sql_search와 chat_llm 둘 다로 전달
    workflow.add_edge("eval", "chat_llm")
    workflow.add_edge("sql_search", "chat_llm")
    
    # 상담형 플로우 (순환 구조)
    workflow.add_conditional_edges(
        "state_check",
        route_after_state_check,
        {
            "question": "question",
            "slot_memory": "slot_memory"
        }
    )
    # question → answer → state_check 순환
    workflow.add_edge("question", "answer")
    workflow.add_edge("answer", "state_check")
    
    # 모든 slot 충족 시 - slot_memory에서 extract와 chat_llm로 동시 전달
    workflow.add_edge("slot_memory", "extract")
    workflow.add_edge("slot_memory", "chat_llm")
    workflow.add_edge("extract", "search_vectordb")
    # extract에서 chat_llm으로 가는 화살표 제거 (chat_llm은 sql_search, eval, slot_memory에서만 받음)
    workflow.add_edge("chat_llm", END)
    
    return workflow.compile()


if __name__ == "__main__":
    print("=" * 60)
    print("그래프 빌드 중...")
    print("=" * 60)
    
    app = build_graph()
    print("✓ 그래프 빌드 완료!\n")
    
    # Mermaid 다이어그램 출력
    try:
        print("=" * 60)
        print("그래프 구조 (Mermaid 다이어그램)")
        print("=" * 60)
        mermaid = app.get_graph().draw_mermaid()
        print(mermaid)
        print("\n")
    except Exception as e:
        print(f"Mermaid 다이어그램 생성 실패: {e}\n")
    
    # PNG 저장 시도
    try:
        print("=" * 60)
        print("PNG 파일로 저장 시도...")
        print("=" * 60)
        img = app.get_graph().draw_mermaid_png()
        with open("graph_structure.png", "wb") as f:
            f.write(img)
        print("✓ graph_structure.png 파일로 저장 완료!")
    except Exception as e:
        print(f"✗ PNG 저장 실패: {e}")
        print("  (graphviz 또는 관련 패키지 설치가 필요할 수 있습니다)")
