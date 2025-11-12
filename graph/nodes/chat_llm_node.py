"""
Chat LLM Node
-------------

[기능 설명]
- 검증된 모든 정보를 종합하여 최종 답변을 생성하는 노드
- 사용자 질문, 검증된 chunk, 관련 이미지를 컨텍스트로 사용
- LLM을 통해 자연스러운 답변 생성

[입력 State - 정보형]
- user_question: str - 사용자 질문
- verified_chunks: list[dict] - 검증된 chunk
- related_images: list[str] - 관련 이미지

[입력 State - 상담형]
- user_question: str - 사용자 질문
- extracted_symptoms: dict - 추출된 증상 정보
- slot_data: dict - 수집된 slot 데이터

[출력 State]
- final_answer: str - 최종 생성된 답변
- answer_type: str - 답변 유형 ("information" 또는 "counseling")

[다음 노드]
- 종료 (최종 노드)
"""

def chat_llm_node(state):
    """
    최종 답변을 생성하는 노드
    """
    user_question = state.get("user_question", "")
    verified_chunks = state.get("verified_chunks", [])
    related_images = state.get("related_images", [])
    extracted_symptoms = state.get("extracted_symptoms", {})
    
    # TODO: LLM을 사용하여 최종 답변 생성
    final_answer = ""
    
    return {
        "final_answer": final_answer
    }
