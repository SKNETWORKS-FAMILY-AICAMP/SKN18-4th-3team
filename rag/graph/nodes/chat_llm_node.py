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
    node_type = (state.get("node_type") or "").strip().lower()
    
    # 검증된 청크에 연결된 이미지 정보 가져오기
    verified_chunk_images = state.get("verified_chunk_images") or []
    chunk_sources = state.get("chunk_sources") or []

    # 근거 텍스트 정리(정보형)
    evidence = verified + sql_res
    evidence_text = _shorten_chunks(evidence)

    # node_type에 따라 시스템 프롬프트 분기
    if node_type == "counseling":
        system = (
            "당신은 따뜻하고 자상하며 배려심 깊은 전문 심리상담가이자 정신과 의사입니다. "
            "사용자의 감정과 상황을 깊이 공감하며, 부드럽고 이해심 있는 어조로 대화합니다.\n\n"
            "답변 시 다음을 준수하세요:\n"
            "1. 사용자의 감정을 먼저 인정하고 공감을 표현하세요\n"
            "2. 전문적이면서도 따뜻한 톤으로 조언을 제공하세요\n"
            "3. 의학적 조언이나 증상에 대한 설명을 제공할 수 있지만, 반드시 답변 마지막에 다음 문구를 포함하세요:\n"
            "   '※ 본 답변은 참고 사항일 뿐이며, 정식 의학적 진단이나 처방이 아닙니다. "
            "정확한 진단과 치료를 위해서는 반드시 전문의와 상담하시기 바랍니다.'\n"
            "4. 안전하고 현실적인 다음 행동을 제안하세요\n"
            "5. 사용자가 더 편안하게 이야기할 수 있도록 부드러운 후속 질문 1개를 제시하세요\n"
            "6. 절대 판단하거나 비난하지 말고, 항상 지지적인 태도를 유지하세요"
        )
    else:
        system = (
            "너는 한국어 전문상담가이다. 공감적이고 명료하게 답하되, "
            "정보형 질문에는 근거를 간략히 요약하고, 상담형(콘텍스트 있을 때)에는 "
            "안전하고 현실적인 다음 행동을 제안한다. 의학적 진단/처방은 하지 않는다. "
            "마지막에 후속 질문 1개를 제시한다."
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
    
    # 이미지 정보를 state에 저장 (웹 인터페이스에서 사용하기 위해)
    state["verified_chunk_images"] = verified_chunk_images
    state["chunk_sources"] = chunk_sources
    
    return state
