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
        return {
            "user_question": user_question,
            "retrieved_chunks": []
        }

    # -------------------------------
    # TODO: Vector DB 검색 로직 구현
    # -------------------------------
    # 실제 구현 시:
    #   1. user_question → embedding 생성
    #   2. Vector DB에서 similarity search
    #   3. score 포함된 chunk 리스트 반환
    #
    # 현재는 dummy_chunks로 동작하는 형태(테스트용)
    # -------------------------------

    # 예시: 검색된 것처럼 보이는 더미 chunk (테스트용)
    dummy_chunks = [
        {
            "content": "우울증은 지속적인 우울감과 흥미 감소를 특징으로 하는 정신질환입니다.",
            "metadata": {"doc_id": 1, "page": 5},
            "score": 0.82
        },
        {
            "content": "불안장애는 강한 긴장감과 두려움이 지속되는 상태를 의미합니다.",
            "metadata": {"doc_id": 2, "page": 3},
            "score": 0.65
        },
        {
            "content": "ADHD는 주의력 결핍과 과잉행동이 나타나는 신경발달 장애입니다.",
            "metadata": {"doc_id": 3, "page": 8},
            "score": 0.57
        }
    ]

    # 나중에 Vector DB 연동하면 여기서 검색 결과 반환
    retrieved_chunks = dummy_chunks

    return {
        "user_question": user_question,
        "retrieved_chunks": retrieved_chunks
    }
