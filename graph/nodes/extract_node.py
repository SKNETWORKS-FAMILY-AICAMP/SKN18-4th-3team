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


import json
from typing import Any, Dict, List

# 1) OpenAI LLM을 불러옵니다. (설치/키가 없다면 자동으로 None 처리)
try:
    from openai import OpenAI  # type: ignore

    _client = OpenAI()
except Exception:
    _client = None

# 2) LLM이 따라야 할 간단한 안내 문구(시스템 프롬프트)를 준비합니다.
_SYSTEM_PROMPT = (
    "너는 정신건강 상담 내용을 읽고, 관련된 증상/질환 키워드만 뽑아서 "
    'JSON 배열 형식으로 알려주는 도우미야. 예: ["우울증", "불안장애"]'
)


def _parse_keywords(raw_text: str) -> List[str]:
    """LLM이 준 문자열에서 JSON 배열만 뽑아 안전하게 리스트로 변환한다."""
    content = raw_text.strip()

    # 3) 코드 블록(```json ... ```) 형태로 답이 올 수도 있으니 미리 제거합니다.
    if content.startswith("```"):
        parts = content.split("```")
        # parts 예시: ["", "json", '\n["우울증"]\n', ""]
        if len(parts) >= 3:
            content = parts[2].strip() or parts[1].strip()
        else:
            content = parts[-1].strip()

    # 4) JSON 파싱을 시도하고, 실패하면 빈 리스트를 돌려줍니다.
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [item.strip() for item in parsed if isinstance(item, str) and item.strip()]
    except json.JSONDecodeError:
        pass

    return []


def _call_llm_for_keywords(counseling_text: str) -> List[str]:
    """LLM에게 상담 내용을 보내고, 키워드만 받아온다."""
    # 5) 상담 내용이 없거나, LLM 클라이언트가 준비되지 않았다면 빈 리스트 반환
    if not counseling_text.strip() or _client is None:
        return []

    # 6) user 메시지를 준비합니다. (LLM에 실제 상담 내용을 그대로 전달)
    user_prompt = (
        "[상담 내용]\n"
        f"{counseling_text.strip()}\n\n"
        "위 내용을 보고 관련 증상/질환 키워드를 JSON 배열로만 작성해 주세요."
    )

    try:
        response = _client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
        raw_text = response.choices[0].message.content or ""
        return _parse_keywords(raw_text)
    except Exception:
        # 7) LLM 호출이 실패하면 빈 리스트로 넘어가고, 아래에서 기본값을 채웁니다.
        return []


def extract_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    상담 내용을 LLM에 보내 증상 키워드를 추출하고,
    Vector DB에서 검색하기 좋은 문장을 만들어 돌려줍니다.
    """
    # 8) slot_memory_node가 만들어 둔 상담 요약 텍스트를 가져옵니다.
    counseling_context = state.get("counseling_context", "") or ""

    # 9) LLM을 호출해서 증상/질환 키워드를 받아옵니다.
    symptom_keywords = _call_llm_for_keywords(counseling_context)

    # 10) 아무 키워드도 없으면 기본 문구로 채워 후속 단계가 멈추지 않게 합니다.
    if not symptom_keywords:
        symptom_keywords = ["증상 정보 없음"]

    # 11) 키워드를 공백으로 묶어 Vector DB 검색에 쓰일 문장을 만듭니다.
    search_query = " ".join(symptom_keywords)

    # 12) 다음 노드가 그대로 사용할 수 있도록 딕셔너리 형태로 결과를 반환합니다.
    return {
        "user_question": search_query,
        "extracted_symptoms": symptom_keywords,
    }
