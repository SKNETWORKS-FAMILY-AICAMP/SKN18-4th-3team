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
"""
classify_node.py
- 사용자 질문(user_question)을 {information, counseling, unknown} 으로 분류
- gpt-5-nano를 사용하여 모든 질문을 분류
"""

from typing import Dict, Any

# ▼ OpenAI SDK 사용 (프로젝트 래퍼가 있으면 교체하세요)
try:
    from openai import OpenAI
    _client = OpenAI()  # 환경변수 OPENAI_API_KEY 필요
except Exception:  # SDK 미설치/키 미설정 시에도 코드 동작
    _client = None


def _classify_with_llm(q: str) -> str:
    """
    gpt-5-nano를 사용하여 질문을 세 가지 레이블로 분류
    - information: 정신질환 지식/치료/진단기준 등의 정보만 물어보는 경우
    - counseling: 개인 상태/감정/증상 이야기와 상담 관련 내용이 조금이라도 포함된 경우
    - unknown: 서비스와 관계없는 질문 (예: "오늘 밥 뭐먹을까?")
    """
    if _client is None:
        return "unknown"
    
    system = (
        "당신은 사용자 질문을 세 가지 레이블 중 하나로 정확하게 분류하는 전문가입니다.\n\n"
        "분류 기준:\n"
        "1. 'information': 정신질환에 대한 지식, 치료 방법, 진단 기준 등 객관적인 정보만을 요청하는 질문\n"
        "   예시: '우울증이란 무엇인가요?', '불안장애의 증상은?', 'ADHD 치료 방법은?'\n\n"
        "2. 'counseling': 개인의 상태, 감정, 증상에 대한 이야기나 상담 관련 내용이 조금이라도 포함된 질문\n"
        "   예시: '요즘 우울한데 어떻게 해야 하나요?', '제가 불안장애인가요?', '잠을 못 자요'\n"
        "   주의: 개인적 경험이나 감정이 조금이라도 언급되면 counseling으로 분류\n\n"
        "3. 'unknown': 정신건강 서비스와 전혀 관계없는 질문\n"
        "   예시: '오늘 밥 뭐먹을까?', '날씨 어때?', '맛집 추천해줘', '파이썬 코드 작성해줘'\n\n"
        "반드시 'information', 'counseling', 'unknown' 중 하나만 정확히 출력하세요. 다른 설명은 하지 마세요."
    )
    
    user = f"질문: {q}"
    
    try:
        resp = _client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0
        )
        label = resp.choices[0].message.content.strip().lower()
        
        # 유효한 레이블인지 확인
        if label in {"information", "counseling", "unknown"}:
            return label
        else:
            return "unknown"
            
    except Exception as e:
        print(f"LLM 분류 중 오류 발생: {e}")
        return "unknown"


def classify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      - state['user_question']: str (필수)
    Output:
      - state['question_type']: 'information' | 'counseling' | 'unknown'
    """
    q = (state.get("user_question") or "").strip()
    
    # 빈 질문은 unknown으로 처리
    if not q:
        state["question_type"] = "unknown"
        return state
    
    # gpt-5-nano로 분류
    label = _classify_with_llm(q)
    state["question_type"] = label
    
    return state
