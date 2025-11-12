"""
Search VectorDB Node
--------------------

[기능 설명]
- 사용자 질문과 유사한 chunk를 Vector DB에서 검색
- 임베딩 유사도 기반으로 관련 문서 추출
- 메타데이터와 함께 chunk를 반환

[입력 State]
- user_question: str - 사용자 질문
- question_type: str - 질문 유형 ("information")

[출력 State]
- user_question: str - 사용자 질문 (전달)
- retrieved_chunks: list[dict] - 검색된 chunk 리스트
  - content: str - chunk 내용
  - metadata: dict - chunk 메타데이터 (문서 ID, 페이지 등)
"""

def search_vectordb_node(state):
    """
    Vector DB에서 유사한 chunk를 검색하는 노드
    """
    user_question = state.get("user_question", "")
    
    # TODO: Vector DB 검색 로직 구현
    retrieved_chunks = []
    
    return {
        "user_question": user_question,
        "retrieved_chunks": retrieved_chunks
    }
