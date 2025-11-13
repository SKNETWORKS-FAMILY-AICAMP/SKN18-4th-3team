"""
Eval Node
---------

[기능 설명]
- 사용자 질문(user_question)과 검색된 chunk(retrieved_chunks)의 유사도를 검증하는 노드
- 임계값(threshold)을 기준으로 관련성이 높은 chunk만 필터링
- 필터링된 chunk를 verified_chunks로 반환

[입력 State]
- user_question: str - 사용자 질문
- retrieved_chunks: list[dict] - 검색된 chunk 리스트

- user_question: str - 사용자 질문
- retrieved_chunks: list[dict] - 검색된 chunk 리스트
    * chunk 예시:
        {
            "content": "우울증은 ...",
            "metadata": {...},
            "score": 0.82
        }

[출력 State]
- user_question: str - 사용자 질문 (전달)
- verified_chunks: list[dict] - 검증된 chunk 리스트(score >= threshold 인 것만)
  - content: str - chunk 내용
  - metadata: dict - chunk 메타데이터
  - score: float - 유사도 점수
"""



def eval_node(state):
    """
    검색된 chunk의 관련성을 검증하는 노드
    """
    user_question = state.get("user_question", "")
    retrieved_chunks = state.get("retrieved_chunks", [])
    
    # TODO: 임계값 기반 chunk 필터링
    threshold = 0.7
    verified_chunks = [
        chunk for chunk in retrieved_chunks 
        if chunk.get("score", 0) >= threshold
    ]
    
    return {
        "user_question": user_question,
        "verified_chunks": verified_chunks
    }

def eval_node(state):
    """
    검색된 chunk의 관련성을 검증하는 노드
    """
    user_question = state.get("user_question", "")
    retrieved_chunks = state.get("retrieved_chunks", [])

    # TODO: 임계값 기반 chunk 필터링
    # 임계값
    threshold = 0.7

    # score 기준 필터링
    verified_chunks = [
        chunk for chunk in retrieved_chunks
        if chunk.get("score", 0) >= threshold
    ]

    return {
        "user_question": user_question,
        "verified_chunks": verified_chunks
    }
