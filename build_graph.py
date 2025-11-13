"""
build_graph.py
--------------
통합된 LangGraph 구조 정의 및 컴파일
- YAML 스펙 기반 그래프 구성
- 조건부 엣지 라우팅 구현
- eval=gpt-5-mini, 나머지=gpt-5-nano (노드 내부에서 모델 선택)
"""

from pathlib import Path
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ===== Nodes import =====
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

# ===== Agents import (라우팅 함수) =====
from graph.agents.classify_agent import route_after_classify
from graph.agents.state_check_agent import route_after_state_check
from graph.agents.eval_agent import route_after_eval


# ===== State 정의 =====
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
    - 조건부 엣지를 포함한 완전한 그래프 구조
    """
    # StateGraph 초기화 (recursion_limit 증가)
    workflow = StateGraph(GraphState)
    
    # ===== 노드 추가 =====
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
    
    # ===== 엣지 추가 =====
    # 시작점
    workflow.set_entry_point("classify")
    
    # 1. classify 후 조건부 라우팅
    workflow.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "search_vectordb": "search_vectordb",
            "state_check": "state_check",
            "__end__": END
        }
    )
    
    # 2. 정보형 플로우
    workflow.add_edge("search_vectordb", "eval")
    
    # eval 후 조건부 라우팅
    workflow.add_conditional_edges(
        "eval",
        route_after_eval,
        {
            "sql_search": "sql_search",
            "chat_llm": "chat_llm",
            "__end__": END
        }
    )
    workflow.add_edge("sql_search", "chat_llm")
    
    # 3. 상담형 플로우 (순환 구조)
    workflow.add_conditional_edges(
        "state_check",
        route_after_state_check,
        {
            "question": "question",
            "slot_memory": "slot_memory"
        }
    )
    workflow.add_edge("question", "answer")
    workflow.add_edge("answer", "state_check")
    
    # 모든 slot 충족 시 팬아웃
    workflow.add_edge("slot_memory", "extract")
    workflow.add_edge("slot_memory", "chat_llm")
    workflow.add_edge("extract", "search_vectordb")
    
    # 4. 최종 답변 후 종료
    workflow.add_edge("chat_llm", END)
    
    # 그래프 컴파일
    # checkpointer를 사용하면 상담형 대화에서 중단/재개 가능
    app = workflow.compile()
    
    return app


def get_app():
    """
    외부에서 그래프 인스턴스를 가져올 때 사용
    """
    return build_graph()


if __name__ == "__main__":
    """
    그래프 시각화 및 테스트
    """
    print("=" * 60)
    print("정신건강 상담 챗봇 그래프 빌드")
    print("=" * 60)
    
    try:
        app = build_graph()
        print("✓ 그래프 빌드 완료!")
        
        # 그래프 구조 출력
        print("\n=== 그래프 구조 (Mermaid) ===")
        mermaid_output = app.get_graph().draw_mermaid()
        
        # 중복 라인 제거
        lines = mermaid_output.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            if line not in seen:
                unique_lines.append(line)
                seen.add(line)
        
        print('\n'.join(unique_lines))
        
        # PNG로 저장 시도
        try:
            print("\n그래프를 PNG로 저장 중...")
            img = app.get_graph().draw_mermaid_png()
            with open("graph_structure.png", "wb") as f:
                f.write(img)
            print("✓ graph_structure.png 파일로 저장 완료!")
        except Exception as e:
            print(f"PNG 저장 실패 (무시): {e}")
            
    except Exception as e:
        print(f"✗ 그래프 빌드 실패: {e}")
        raise