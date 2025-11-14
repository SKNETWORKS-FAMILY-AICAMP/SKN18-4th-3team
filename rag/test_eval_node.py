"""
eval_node.py 단위 테스트 파일

- eval_node + search_vectordb_node 연동 단위 테스트

목적:
- search_vectordb_node를 통해 실제 VectorDB에서 retrieved_chunks를 가져오고
- 해당 청크들을 eval_node에 넣어 LLM 기반 점수/필터링이 정상 동작하는지 확인
"""

from dotenv import load_dotenv
load_dotenv()  # .env에서 OPENAI_API_KEY 읽기

from rag.graph.nodes.search_vectordb_node import search_vectordb_node
from rag.graph.nodes.eval_node import eval_node


def main():
    # 테스트용 사용자 질문 (필요하면 이 문장은 바꿔가며 여러 번 실험)
    user_question = "불안장애가 있으면 어떤 증상들이 나타나나요?"

    # 1) 초기 state: 질문 + question_type만 넣고 시작
    state = {
        "user_question": user_question,
        "question_type": "information",
    }

    print("\n===== search_vectordb_node TEST START =====")
    after_search = search_vectordb_node(state)

    retrieved_chunks = after_search.get("retrieved_chunks") or []
    print(f"[search_vectordb_node] retrieved_chunks count = {len(retrieved_chunks)}")

    # 필요하면 어떤 청크가 왔는지 간단히 내용 확인
    for i, ch in enumerate(retrieved_chunks[:3]):  # 상위 3개만 preview
        preview = (ch.get("content") or "").replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:117] + "..."
        print(f"  - chunk[{i}] preview: {preview}")

    print("===== search_vectordb_node TEST END =====\n")

    print("===== eval_node TEST START =====")
    after_eval = eval_node(after_search)

    verified_chunks = after_eval.get("verified_chunks") or []
    print(f"[eval_node] verified_chunks count = {len(verified_chunks)}")

    # 점수와 함께 상위 몇 개만 출력
    for i, ch in enumerate(verified_chunks[:5]):
        q_rel = ch.get("question_relevance")
        a_help = ch.get("answer_helpfulness")
        score = ch.get("score")
        preview = (ch.get("content") or "").replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:117] + "..."
        print(
            f"  - verified[{i}] score={score:.3f} "
            f"(rel={q_rel:.3f}, help={a_help:.3f}) :: {preview}"
        )

    print("===== eval_node TEST END =====\n")


if __name__ == "__main__":
    main()
