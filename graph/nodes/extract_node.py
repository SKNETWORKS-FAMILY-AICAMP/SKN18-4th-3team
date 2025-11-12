"""
Extract Node
------------

[역할]
사용자 답변에서 증상 키워드를 추출하여 Vector DB 조회용 쿼리 생성

[처리 로직]
1. slot_data에서 모든 답변 통합
2. LLM으로 증상 관련 키워드 추출
3. 추출된 키워드를 검색 쿼리로 변환

[입력]
- slot_data: 모든 slot에 수집된 답변
- counseling_context: 통합된 상담 텍스트

[출력]
- user_question: 추출된 증상 키워드 (Vector DB 검색용)
- extracted_symptoms: 추출된 증상 키워드 리스트

[다음 노드]
→ search_vectordb_node (증상 키워드로 관련 정보 검색)

[예시]
입력: "2주 동안 우울하고 불안해요. 잠도 못 자고 집중이 안 돼요"
추출: ["우울", "불안", "불면", "집중력 저하"]
쿼리: "우울 불안 불면 집중력 저하"
→ Vector DB에서 관련 정신질환 정보 검색
"""


def extract_node(state):
    """
    증상 키워드를 추출하여 Vector DB 검색 쿼리 생성
    """
    slot_data = state.get("slot_data", {})
    counseling_context = state.get("counseling_context", "")

    # TODO: LLM을 사용하여 증상 키워드 추출
    # 예: "우울하고 불안해요" → ["우울", "불안"]
    # 예: "잠을 못 자요" → ["불면", "수면장애"]
    
    symptom_keywords = []  # LLM으로 추출된 키워드 리스트
    search_query = counseling_context  # 기본값: 전체 텍스트

    return {
        "user_question": search_query,  # Vector DB 검색용
        "extracted_symptoms": symptom_keywords,  # 추출된 증상 리스트
    }
