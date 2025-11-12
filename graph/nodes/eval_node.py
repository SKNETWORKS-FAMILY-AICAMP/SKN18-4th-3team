"""
Eval Node
---------

[기능 설명]
- 사용자 질문과 검색된 chunk의 유사도를 검증하는 노드
- 임계값(threshold)을 기준으로 관련성이 높은 chunk만 필터링
- 검증된 chunk를 다음 노드로 전달

[입력 State]
- user_question: str - 사용자 질문
- retrieved_chunks: list[dict] - 검색된 chunk 리스트

[출력 State]
- user_question: str - 사용자 질문 (전달)
- verified_chunks: list[dict] - 검증된 chunk 리스트
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
