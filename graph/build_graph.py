"""
build_graph.py
--------------
- 전체 LangGraph 구조를 초기화하고, 각 Agent들을 연결하여 대화 플로우를 구성하는 진입점(entrypoint).
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict

# Nodes import
from graph.nodes.classify_node import classify_node
from graph.nodes.search_vectordb_node import search_vectordb_node
from graph.nodes.eval_node import eval_node
from graph.nodes.sql_search_node import sql_search_node
from graph.nodes.chat_llm_node import chat_llm_node
from graph.nodes.state_check_node import state_check_node
from graph.nodes.question_node import question_node
from graph.nodes.answer_node import answer_node
from graph.nodes.slot_memory_node import slot_memory_node
from graph.nodes.extract_node import extract_node

# Agents import
from graph.agents.classify_agent import route_after_classify
from graph.agents.state_check_agent import route_after_state_check
from graph.agents.eval_agent import route_after_eval


# State 정의
class GraphState(TypedDict):
    # 공통
    user_question: str
    initial_question: Optional[str]  # 최초 질문 보관용
    
    # 정보형 질문 관련
    question_type: Optional[str]
    retrieved_chunks: Optional[List[Dict]]
    verified_chunks: Optional[List[Dict]]
    related_images: Optional[List[str]]
    
    # 상담형 질문 관련
    slot_status: Optional[Dict[str, bool]]
    slot_data: Optional[Dict[str, str]]
    current_slot: Optional[str]
    bot_question: Optional[str]
    user_answer: Optional[str]
    waiting_for_answer: Optional[bool]
    counseling_context: Optional[str]
    all_slots_filled: Optional[bool]
    extracted_symptoms: Optional[Dict]
    
    # 최종 답변
    final_answer: Optional[str]


def build_graph():
    """
    전체 그래프를 구성하는 함수
    """
    # StateGraph 초기화
    workflow = StateGraph(GraphState)
    
    # ===== 노드 추가 =====
    # 1. 질문 분류
    workflow.add_node("classify", classify_node)
    
    # 2. 정보형 질문 플로우
    workflow.add_node("search_vectordb", search_vectordb_node)
    workflow.add_node("eval", eval_node)
    workflow.add_node("sql_search", sql_search_node)
    
    # 3. 상담형 질문 플로우
    workflow.add_node("state_check", state_check_node)
    workflow.add_node("question", question_node)
    workflow.add_node("answer", answer_node)
    workflow.add_node("slot_memory", slot_memory_node)
    workflow.add_node("extract", extract_node)
    
    # 4. 공통 최종 답변
    workflow.add_node("chat_llm", chat_llm_node)
    
    # ===== 엣지 추가 =====
    # 시작점
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
    
    # 최종 답변 후 종료
    workflow.add_edge("chat_llm", END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


if __name__ == "__main__":
    """
    그래프 시각화 테스트
    """
    print("그래프 빌드 중...")
    app = build_graph()
    print("그래프 빌드 완료!")
    
    # 그래프 구조 출력
    try:
        # Mermaid 다이어그램으로 시각화
        print("\n=== 그래프 구조 (Mermaid) ===")
        print(app.get_graph().draw_mermaid())
    except Exception as e:
        print(f"시각화 오류: {e}")
    
    # PNG로 저장 (graphviz 설치 필요)
    try:
        from IPython.display import Image
        print("\n그래프를 PNG로 저장 중...")
        img = app.get_graph().draw_mermaid_png()
        with open("graph_structure.png", "wb") as f:
            f.write(img)
        print("graph_structure.png 파일로 저장 완료!")
    except Exception as e:
        print(f"PNG 저장 실패: {e}")
        print("graphviz 설치가 필요할 수 있습니다.")