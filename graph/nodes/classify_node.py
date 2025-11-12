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
- 1차: 규칙 기반 키워드/패턴
- 2차(애매할 때만): LLM(gpt-5-nano)로 보정
"""

import re
from typing import Dict, Any, Optional

# ▼ OpenAI SDK 사용 (프로젝트 래퍼가 있으면 교체하세요)
try:
    from openai import OpenAI
    _client = OpenAI()  # 환경변수 OPENAI_API_KEY 필요
except Exception:  # SDK 미설치/키 미설정 시에도 코드 동작(LLM 미사용 분류만)
    _client = None


INFO_HINTS = [
    r"정신질환[이|에]\s*대해", r"증상\s*종류", r"치료\s*방법", r"진단\s*기준",
    r"우울증|불안장애|조현병|ADHD|PTSD|공황장애|강박장애|양극성", r"약물|부작용|심리 교육|인지행동"
]
COUNSEL_HINTS = [
    r"저는|제가|내가|나", r"최근\s*\d+일|요즘|최근에", r"잠이\s*안|수면\s*문제|밥맛|식사\s*문제",
    r"불안해|우울해|죽고|자해|극단|무기력|멘탈|감정", r"상담|도움|조언|어떻게\s*해야"
]

def _regex_any(patterns, text) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)

def _rule_based_classify(q: str) -> Optional[str]:
    q = q.strip()
    if not q:
        return "unknown"
    if _regex_any(COUNSEL_HINTS, q):
        return "counseling"
    if _regex_any(INFO_HINTS, q):
        return "information"
    return None  # 애매 → LLM 보정 시도

def _llm_refine(q: str) -> str:
    """gpt-5-nano로 보정. 실패 시 'unknown'."""
    if _client is None:
        return "unknown"
    system = (
        "너는 질문을 세 가지 레이블 중 하나로만 분류한다: "
        "'information', 'counseling', 'unknown'. "
        "정신질환 지식/치료/진단 기준 등은 information, "
        "개인 상태/감정/증상 이야기와 상담은 counseling, "
        "그 외는 unknown. 정답만 한 단어로 출력."
    )
    user = f"질문: {q}"
    try:
        resp = _client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0
        )
        label = resp.choices[0].message.content.strip().lower()
        return label if label in {"information","counseling","unknown"} else "unknown"
    except Exception:
        return "unknown"

def classify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      - state['user_question']: str (필수)
    Output:
      - state['question_type']: 'information' | 'counseling' | 'unknown'
    """
    q = (state.get("user_question") or "").strip()
    label = _rule_based_classify(q)
    if label is None:
        label = _llm_refine(q)
    state["question_type"] = label or "unknown"
    return state
