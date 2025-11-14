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
    
    - 정보형(information): 사용자 질문 그대로 검색
    - 상담형(counseling): 각 증상 키워드별로 개별 검색 후 결과를 합침
    """
    user_question = state.get("user_question", "").strip()
    question_type = state.get("question_type", "information")
    extracted_symptoms = state.get("extracted_symptoms", [])

    # 질문 비어있으면 바로 빈 리스트 반환
    if not user_question:
        return {"user_question": user_question, "retrieved_chunks": []}

    # Vector DB 검색
    try:
        from rag.services.vector_store import get_vector_store

        vector_store = get_vector_store()
        
        # 상담형이고 증상 키워드가 여러 개 있으면 각각 검색 후 합치기
        if question_type == "counseling" and extracted_symptoms and len(extracted_symptoms) > 1:
            all_chunks = []
            seen_chunk_ids = set()
            
            # 각 키워드별로 검색 (top_k=3으로 줄여서 여러 키워드 검색)
            for symptom in extracted_symptoms:
                chunks = vector_store.search(
                    query=symptom, top_k=3, threshold=0.5
                )
                
                # 중복 제거하면서 추가
                for chunk in chunks:
                    chunk_id = chunk.get("chunk_id")
                    if chunk_id and chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(chunk_id)
                        all_chunks.append(chunk)
            
            # 점수 기준으로 정렬하고 상위 5개만 선택
            all_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
            retrieved_chunks = all_chunks[:5]
        else:
            # 정보형이거나 키워드가 1개이면 기존 방식대로
            retrieved_chunks = vector_store.search(
                query=user_question, top_k=5, threshold=0.5
            )

    except Exception as e:
        print(f"[search_vectordb_node] Vector DB 검색 실패: {e}")
        retrieved_chunks = []

    return {"user_question": user_question, "retrieved_chunks": retrieved_chunks}
