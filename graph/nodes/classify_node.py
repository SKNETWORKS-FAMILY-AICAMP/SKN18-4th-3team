"""
Classify Node
-------------

[기능 설명]
- 사용자의 질문을 분석하여 질문 유형을 분류하는 노드
- LLM을 사용하여 질문의 의도를 파악하고 3가지 유형으로 분류
1. 정신질환 정보형: 정신질환에 대한 지식, 정보를 요청하는 질문
2. 상담형: 개인의 증상이나 상태에 대한 상담을 원하는 질문
3. 서비스 무관: 정신건강과 무관하거나 부적절한 질문

[입력 State]
- user_question: str - 사용자가 입력한 질문

[출력 State]
- user_question: str - 사용자 질문
- question_type: str - 질문 유형
  * "information": 정신질환 정보형 질문
  * "counseling": 상담형 질문
  * "unknown": 서비스와 관련없는 질문

[분류 예시]
1. 정보형 (information):
   - "우울증이란 무엇인가요?"
   - "불안장애의 증상은 어떤 것들이 있나요?"
   
2. 상담형 (counseling):
   - "요즘 기분이 우울한데 어떻게 해야 하나요?"
   - "불안감이 심해서 잠을 못 자요"
   
3. 서비스 무관 (unknown):
   - "오늘 날씨 어때?"
   - "맛집 추천해줘"
   - "파이썬 코드 작성해줘"
"""


def classify_node(state):
   """
   사용자 질문을 분류하는 노드

   Returns:
      dict: question_type을 포함한 상태
            - "information": 정보형 질문
            - "counseling": 상담형 질문
            - "unknown": 서비스 무관 질문
   """
   user_question = state.get("user_question", "")
   # TODO: LLM을 사용하여 질문 유형 분류
   # 반환값: "information", "counseling", "unknown" 중 하나
   question_type = _classify_question(user_question)
   
   return {"user_question": user_question, "question_type": question_type}
