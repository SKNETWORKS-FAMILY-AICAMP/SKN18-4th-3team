from pathlib import Path
import yaml
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# .env 파일 로드 (독립 실행 시 필요)
load_dotenv()

# ─────────────────────────────────────────────────────────────
# 경로
ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "specs" / "counseling_rag.graph.yaml"

# ─────────────────────────────────────────────────────────────
# 노드 함수 바인딩 (nodes/*.py 파일에 함수가 있어야 함)
# 각 파일은 해당 이름의 함수 하나를 export한다고 가정:
#   classify.py      -> classify_node(state)
#   search_vectordb.py -> search_vectordb_node(state)
#   eval.py          -> eval_node(state)
#   sql_search.py    -> sql_search_node(state)
#   state_check.py   -> state_check_node(state)
#   question.py      -> question_node(state)
#   answer.py        -> answer_node(state)
#   slot_memory.py   -> slot_memory_node(state)
#   extract.py       -> extract_node(state)
#   chat_llm.py      -> chat_llm_node(state)

from graph.nodes.classify_node import classify_node
from graph.nodes.search_vectordb_node import search_vectordb_node
from graph.nodes.eval_node import eval_node
from graph.nodes.sql_search_node import sql_search_node
from graph.nodes.state_check_node import state_check_node
from graph.nodes.question_node import question_node
from graph.nodes.answer_node import answer_node
from graph.nodes.slot_memory_node import slot_memory_node
from graph.nodes.extract_node import extract_node
from graph.nodes.chat_llm_node import chat_llm_node

NODE_IMPL = {
    "classify": classify_node,
    "search_vectordb": search_vectordb_node,
    "eval": eval_node,
    "sql_search": sql_search_node,
    "state_check": state_check_node,
    "question": question_node,
    "answer": answer_node,
    "slot_memory": slot_memory_node,
    "extract": extract_node,
    "chat_llm": chat_llm_node,
}

# ─────────────────────────────────────────────────────────────
def load_spec(path: Path = SPEC) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_from_spec(spec: dict):
    """
    최소 스캐폴드:
    - spec["graph"]["entry"] 를 엔트리로 설정
    - spec["nodes"] 의 id 들을 노드로 등록
    - spec["edges"] 의 "A -> B" 문자열로 엣지 구성
    """
    sg = StateGraph(dict)

    # 노드 등록
    for node in spec["nodes"]:
        node_id = node["id"]
        fn = NODE_IMPL.get(node_id)
        if fn is None:
            raise KeyError(f"[Taeho_build_graph] NODE_IMPL에 매핑 없는 노드 id: {node_id}")
        sg.add_node(node_id, fn)

    # 엔트리 설정
    entry = spec["graph"]["entry"]
    sg.set_entry_point(entry)

    # 엣지 등록
    for edge in spec["edges"]:
        # "A -> B" 형식
        src, dst = [s.strip() for s in edge.split("->")]
        if dst == "END":
            sg.add_edge(src, END)
        else:
            sg.add_edge(src, dst)

    return sg.compile()

def get_app():
    spec = load_spec()
    return build_from_spec(spec)

if __name__ == "__main__":
    app = get_app()
    print(f"✓ Graph compiled from: {SPEC}")
    try:
        print("Mermaid:")
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
    except Exception as e:
        print(f"(Mermaid 출력 실패 무시) {e}")
