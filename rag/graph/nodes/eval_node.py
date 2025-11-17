"""
Eval Node
---------

[기능 설명]
- 사용자 질문(user_question)과 검색된 chunk(retrieved_chunks)의 유사도를 LLM으로 검증하는 노드
- 각 chunk에 대해 다음 두 기준으로 0점부터 점수를 부여:
  1) 질문과의 관련성 (question_relevance, 0.0 ~ 0.3)
  2) 답변에 도움이 되는 정도 (answer_helpfulness, 0.0 ~ 0.3)
- 두 점수의 합(total_score = relevance + helpfulness)을 기준으로 필터링
- 필터링된 chunk를 verified_chunks로 반환

[입력 State]
- user_question: str - 사용자 질문
- retrieved_chunks: list[dict] - 검색된 chunk 리스트
    * chunk 예시:
        {
            "content": "우울증은 ...",
            "metadata": {...},
            "score": 0.82
        }

[출력 State]
- user_question: str - 사용자 질문 (전달)
- verified_chunks: list[dict] - 검증된 chunk 리스트
  - content: str - chunk 내용
  - metadata: dict - chunk 메타데이터
  - score: float - 총점 (0.0 ~ 0.6)
  - question_relevance: float - 관련성 점수 (0.0 ~ 0.3)
  - answer_helpfulness: float - 도움됨 점수 (0.0 ~ 0.3)
"""

from typing import Dict, Any, List
import json

# OpenAI SDK 사용 (환경에 따라 폴백 가능)
try:
    from openai import OpenAI
    _client = OpenAI()
except Exception:
    _client = None

# 점수 범위 및 임계값
MAX_RELEVANCE = 0.3
MAX_HELPFULNESS = 0.3
# 임계값: 나중에 실험하면서 조정
THRESHOLD = 0.4

def _build_chunk_preview(
    chunks: List[Dict[str, Any]],
    max_chunks: int = 10,
    max_chars: int = 400,
) -> str:
    """
    LLM 프롬프트에 넣기 좋은 형태로 chunk들을 정리
    - 최대 max_chunks개만 사용
    - 각 chunk는 max_chars 글자까지만 사용
    """
    lines: List[str] = []
    for i, ch in enumerate(chunks[:max_chunks]):
        content = (ch.get("content") or "").replace("\n", " ").strip()
        if len(content) > max_chars:
            content = content[: max_chars - 3] + "..."
        lines.append(f"[{i}] {content}")
    return "\n".join(lines)


def _llm_score_chunks(
    user_question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> Dict[int, Dict[str, float]]:
    """
    gpt-5-mini를 사용하여 각 chunk별로 두 가지 점수를 계산:
      - question_relevance: 0.0 ~ 0.3
      - answer_helpfulness: 0.0 ~ 0.3

    반환값 예시:
      {
        0: {"question_relevance": 0.25, "answer_helpfulness": 0.3},
        1: {"question_relevance": 0.0,  "answer_helpfulness": 0.05},
        ...
      }
    """
    if _client is None or not retrieved_chunks or not user_question.strip():
        return {}

    chunks_text = _build_chunk_preview(retrieved_chunks)

    system_msg = (
        "당신은 의료/정신건강 RAG 시스템에서 검색된 문단(chunk)의 품질을 평가하는 전문가입니다.\n"
        "각 chunk에 대해 아래 두 기준을 독립적으로 평가하세요.\n\n"
        "1) 질문과의 관련성(question_relevance):\n"
        "   - 이 chunk의 내용이 사용자 질문의 주제/맥락과 얼마나 관련이 있는지 평가합니다.\n"
        "   - 0.0 ~ 0.3 범위에서 점수를 부여하세요.\n"
        "   - 전혀 관련 없으면 0.0, 매우 관련 있으면 0.3에 가깝게.\n\n"
        "2) 답변에 도움이 되는 정도(answer_helpfulness):\n"
        "   - 이 chunk가 실제로 사용자에게 제공할 답변 내용을 채우는 데 얼마나 도움이 되는지 평가합니다.\n"
        "   - 0.0 ~ 0.3 범위에서 점수를 부여하세요.\n"
        "   - 내용이 구체적이고 설명/정의/지침을 잘 포함할수록 높은 점수.\n\n"
        "각 chunk에 대해 두 점수를 모두 제공하고, JSON 형식으로만 출력하세요.\n"
        "점수는 반드시 숫자(float)이며, 범위를 벗어나지 않도록 하세요.\n\n"
        "출력 형식(예시):\n"
        "{\n"
        '  \"results\": [\n'
        '    {\"index\": 0, \"question_relevance\": 0.25, \"answer_helpfulness\": 0.30},\n'
        '    {\"index\": 1, \"question_relevance\": 0.10, \"answer_helpfulness\": 0.05}\n'
        "  ]\n"
        "}\n\n"
        "중요:\n"
        "- JSON 이외의 텍스트, 설명, 코드블록(````), 주석 등을 절대 출력하지 마세요."
    )

    user_msg = (
        f"[사용자 질문]\n{user_question}\n\n"
        "[후보 chunk 목록]\n"
        f"{chunks_text}\n\n"
        "각 chunk에 대해 두 점수를 평가하고 위에서 지정한 JSON 형식으로만 응답하세요."
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            # gpt-5-mini는 temperature=0.0 지원 안 함 → 기본값 사용
        )
        raw = resp.choices[0].message.content.strip()
        print("\n[DEBUG] Raw LLM Output =======================")
        print(raw)
        print("==============================================\n")

        data = json.loads(raw)

        results = data.get("results", [])
        index_to_scores: Dict[int, Dict[str, float]] = {}

        for item in results:
            try:
                idx = int(item.get("index"))
                q_rel = float(item.get("question_relevance", 0.0))
                a_help = float(item.get("answer_helpfulness", 0.0))

                # 범위 클램핑
                q_rel = max(0.0, min(MAX_RELEVANCE, q_rel))
                a_help = max(0.0, min(MAX_HELPFULNESS, a_help))

                if 0 <= idx < len(retrieved_chunks):
                    index_to_scores[idx] = {
                        "question_relevance": q_rel,
                        "answer_helpfulness": a_help,
                    }
            except Exception:
                # 잘못된 형식은 스킵
                continue

        return index_to_scores

    except Exception as e:
        # LLM 오류 시 콘솔 로그 남기고 빈 dict 반환 → 폴백 로직 사용
        print(f"[eval_node] LLM 평가 중 오류 발생: {e}")
        return {}


def eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색된 chunk들의 관련성과 유용성을 LLM으로 평가하여 유효한 chunk만 필터링.
    """
    user_question = state.get("user_question", "")
    retrieved_chunks: List[Dict[str, Any]] = state.get("retrieved_chunks", []) or []

    # 아무 것도 없으면 바로 반환
    if not user_question.strip() or not retrieved_chunks:
        return {
            "user_question": user_question,
            "verified_chunks": []
        }

    # 1) LLM으로 세부 점수 계산
    scored = _llm_score_chunks(user_question, retrieved_chunks)

    verified_chunks: List[Dict[str, Any]] = []

    if scored:
        # LLM 점수를 사용하여 total_score 계산 후 필터링
        for idx, chunk in enumerate(retrieved_chunks):
            scores = scored.get(idx)
            if not scores:
                continue

            q_rel = float(scores.get("question_relevance", 0.0))
            a_help = float(scores.get("answer_helpfulness", 0.0))
            total = q_rel + a_help  # 0.0 ~ 0.6

            if total >= THRESHOLD:
                new_chunk = dict(chunk)
                new_chunk["question_relevance"] = q_rel
                new_chunk["answer_helpfulness"] = a_help
                new_chunk["score"] = total  # downstream에서 사용할 총점
                verified_chunks.append(new_chunk)
    else:
        # 2) LLM 사용 불가/실패 시: 기존 score 값이 있다면 동일 threshold로 폴백
        verified_chunks = [
            chunk for chunk in retrieved_chunks
            if float(chunk.get("score", 0.0)) >= THRESHOLD
        ]

    return {
        "user_question": user_question,
        "verified_chunks": verified_chunks
    }
