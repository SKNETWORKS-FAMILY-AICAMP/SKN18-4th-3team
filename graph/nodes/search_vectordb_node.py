"""
Search VectorDB Node
--------------------

[기능 설명]
- 사용자 질문(user_question)을 임베딩으로 변환하여 Vector DB에서 유사 chunk 검색
- 유사도 기반으로 관련 문서를 검색하고 결과를 retrieved_chunks 형태로 반환
- 메타데이터와 함께 chunk를 반환

[입력 State]
- user_question: str - 사용자 질문
- question_type: str - 질문 유형 ("information")

[출력 State]
- user_question: str - 사용자 질문 (전달)
- retrieved_chunks: list[dict] - 검색된 chunk 리스트
  - content: str - chunk 내용
  - metadata: dict - chunk 메타데이터 (문서 ID, 페이지 등)
  [
        {
            "content": "우울증은 ...",
            "metadata": {"doc_id": 3, "page": 12},
            "score": 0.83
        }
    ]
"""

def search_vectordb_node(state):
    """
    Vector DB에서 유사한 chunk를 검색하는 노드
    """
    user_question = state.get("user_question", "").strip()

    # 질문 비어있으면 바로 빈 리스트 반환
    if not user_question:
        return {"user_question": user_question, "retrieved_chunks": []}

    # Vector DB 검색
    try:
        from services.vector_store import get_vector_store

        vector_store = get_vector_store()
        retrieved_chunks = vector_store.search(
            query=user_question, top_k=5, threshold=0.5
        )

    except Exception as e:
        print(f"[search_vectordb_node] Vector DB 검색 실패: {e}")
        retrieved_chunks = []

    return {"user_question": user_question, "retrieved_chunks": retrieved_chunks}
