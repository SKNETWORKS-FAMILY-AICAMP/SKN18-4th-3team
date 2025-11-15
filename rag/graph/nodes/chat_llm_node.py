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
"""
chat_llm_node.py
- 최종 답변 생성 노드
- 입력: verified_chunks(정보형 근거), counseling_context(상담 요약) 등
- 출력: final_answer (전문상담가 톤, 근거요약 + 후속질문 1개)
"""

from typing import Dict, Any, List

# ▼ OpenAI SDK 사용(필요시 프로젝트 래퍼로 교체)
try:
    from openai import OpenAI
    _client = OpenAI()
except Exception:
    _client = None

def _shorten_chunks(chunks: List[Dict[str, Any]], max_chars=700) -> str:
    if not chunks:
        return ""
    acc = []
    remain = max_chars
    for i, ch in enumerate(chunks, 1):
        txt = (ch.get("content") or "").strip().replace("\n", " ")
        if not txt:
            continue
        piece = f"[{i}] {txt}"
        if len(piece) > remain:
            piece = piece[: max(0, remain - 3)] + "..."
        acc.append(piece)
        remain -= len(piece)
        if remain <= 0:
            break
    return "\n".join(acc)

def chat_llm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs (옵션):
      - state['verified_chunks']: List[Dict]
      - state['sql_results']: List[Dict]
      - state['counseling_context']: str
      - state['user_question']: str
      - state['node_type']: str (classify 결과: "counseling" 또는 "information")
    Output:
      - state['final_answer']: str
    """
    user_q = (state.get("user_question") or "").strip()
    ctx = (state.get("counseling_context") or "").strip()
    verified = state.get("verified_chunks") or []
    sql_res = state.get("sql_results") or []
    question_type = (state.get("question_type") or "").strip().lower()

    # 근거 텍스트 정리(정보형)
    evidence = verified + sql_res
    evidence_text = _shorten_chunks(evidence)

    # question_type에 따라 시스템 프롬프트 분기
    if question_type == "counseling":
        # 상담형: 사용자의 개인적 고민, 감정, 증상에 대한 공감과 조언
        system = (
            "당신은 따뜻하고 자상하며 배려심 깊은 전문 심리상담가입니다. "
            "사용자의 감정과 상황을 깊이 공감하며, 부드럽고 이해심 있는 어조로 대화합니다.\n\n"
            "답변 시 다음을 준수하세요:\n"
            "1. 사용자의 감정을 먼저 인정하고 공감을 표현하세요\n"
            "2. 전문적이면서도 따뜻한 톤으로 조언을 제공하세요\n"
            "3. 수집된 정보(증상, 상황 등)를 바탕으로 맞춤형 조언을 제공하세요\n"
            "4. 안전하고 현실적인 다음 행동을 제안하세요 (예: 전문가 상담, 자가 관리법 등)\n"
            "5. 사용자가 더 편안하게 이야기할 수 있도록 부드러운 후속 질문 1개를 제시하세요\n"
            "6. 절대 판단하거나 비난하지 말고, 항상 지지적인 태도를 유지하세요\n"
            "7. 답변 마지막에 반드시 다음 문구를 포함하세요:\n"
            "   '※ 본 답변은 참고 사항일 뿐이며, 정식 의학적 진단이나 처방이 아닙니다. "
            "정확한 진단과 치료를 위해서는 반드시 전문의와 상담하시기 바랍니다.'"
        )
    else:
        # 정보형: 정신건강 관련 지식, 질환 정보, 치료법 등에 대한 객관적 정보 제공
        system = (
            "당신은 정신건강 분야의 전문 지식을 제공하는 AI 어시스턴트입니다.\n\n"
            "답변 시 다음을 준수하세요:\n"
            "1. 제공된 근거 자료를 바탕으로 정확하고 객관적인 정보를 제공하세요\n"
            "2. 전문 용어는 쉽게 풀어서 설명하되, 정확성을 유지하세요\n"
            "3. 근거 자료의 핵심 내용을 간략히 요약하여 제시하세요\n"
            "4. 관련 이미지가 있다면 함께 참고하도록 안내하세요\n"
            "5. 추가로 궁금할 만한 관련 질문 1개를 제시하세요\n"
            "6. 개인의 증상이나 치료에 대한 직접적인 조언은 피하고, 일반적인 정보만 제공하세요\n"
            "7. 답변 마지막에 반드시 다음 문구를 포함하세요:\n"
            "   '※ 본 정보는 일반적인 참고 자료이며, 개인의 상황에 따라 다를 수 있습니다. "
            "구체적인 진단이나 치료가 필요한 경우 반드시 전문의와 상담하시기 바랍니다.'"
        )

    # 프롬프트 구성
    parts = []
    if user_q:
        parts.append(f"[사용자 질문]\n{user_q}")
    if ctx:
        parts.append(f"[상담 콘텍스트]\n{ctx}")
    if evidence_text:
        parts.append(f"[참고 근거]\n{evidence_text}")
    prompt = "\n\n".join(parts).strip() or "사용자 질문이 비어 있습니다."

    # LLM 존재하지 않으면 안전한 폴백
    if _client is None:
        fallback = (
            "요청을 이해했어요. 현재 모델 연결이 없어 일반 가이드를 드립니다.\n\n"
            f"{('- 상담 콘텍스트 요약 존재\n' if ctx else '')}"
            f"{('- 정보 근거가 일부 확보되었습니다.\n' if evidence_text else '')}"
            "다음으로 어떤 점이 가장 궁금하신가요?"
        )
        state["final_answer"] = fallback
        return state

    try:
        resp = _client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = (
            "답변을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.\n"
            f"(internal: {e})"
        )

    state["final_answer"] = answer
    return state
