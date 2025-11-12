"""
Extract Node
------------

[역할]
사용자 답변에서 증상 키워드를 추출하여 Vector DB 조회용 쿼리 생성

[처리 로직]
1. counseling_context에서 통합된 상담 내용 받기
2. LLM으로 증상 관련 키워드 추출
3. 추출된 키워드를 검색 쿼리로 변환

[입력]
- counseling_context: 통합된 상담 텍스트 (slot_memory_node에서 생성)

[출력]
- user_question: 추출된 증상 키워드 (Vector DB 검색용)
- extracted_symptoms: 추출된 증상 키워드 리스트

[다음 노드]
→ search_vectordb_node (증상 키워드로 관련 정보 검색)

[예시]
입력: "slot_1: 우울하고 불안해요\nslot_2: 2주\nslot_3: 잠을 못 자요"
추출: ["우울", "불안", "불면", "집중력 저하"]
쿼리: "우울 불안 불면 집중력 저하"
→ Vector DB에서 관련 정신질환 정보 검색
"""


def extract_node(state):
    """
    증상 키워드를 추출하여 Vector DB 검색 쿼리 생성
    """
    # slot_memory_node에서 만들어 준 상담 내용 전체를 받아옵니다.
    # 값이 없으면 빈 문자열("")을 사용합니다.
    counseling_context = state.get("counseling_context", "")

    # 실제 서비스에서는 LLM이 아래 과정을 대신합니다.
    # 지금은 간단한 규칙으로 증상 단어를 찾아봅니다.
    # 1) 우리가 관심 있는 증상 단어 목록을 준비합니다.
    # 2) 상담 내용에 해당 단어가 포함되어 있으면 추출합니다.
    symptom_dictionary = [ 
        "우울",
        "불안",
        "불면",
        "식욕 저하",
        "두통",
        "어지러움",
        "집중력 저하",
        "스트레스",
        "피로",
        "무기력",
    ] # 일단 컨펌 받고 추가해보는 걸로 해보자 

    # 상담 내용을 비교하기 쉽게 모두 소문자/한글 그대로 사용합니다.
    normalized_text = counseling_context.lower()

    # 증상 단어가 포함되어 있는지 하나씩 확인합니다.
    symptom_keywords = []
    for symptom in symptom_dictionary:
        # 한글은 대소문자 개념이 약하지만, 일관된 비교를 위해 동일한 방식으로 처리합니다.
        if symptom in normalized_text:
            symptom_keywords.append(symptom)

    # 증상 단어가 하나도 없을 수 있으니 기본값을 정해줍니다.
    if not symptom_keywords:
        symptom_keywords = ["증상 정보 없음"]

    # 검색 엔진(Vector DB)에 보낼 텍스트를 만듭니다.
    # 여러 단어를 공백으로 연결하면 Vector DB가 각각을 참고할 수 있습니다.
    search_query = " ".join(symptom_keywords)

    return {
        "user_question": search_query,  # Vector DB 검색용
        "extracted_symptoms": symptom_keywords,  # 추출된 증상 리스트
    }
