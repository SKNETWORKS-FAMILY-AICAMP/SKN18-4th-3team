"""
Eval Node
---------

[기능 설명]
- 사용자 질문(user_question)과 검색된 chunk(retrieved_chunks)의 유사도를 LLM으로 검증하는 노드
- gpt-5-mini 모델을 사용해 각 chunk의 관련도를 0~1 사이 점수로 평가
- 임계값(threshold)을 기준으로 관련성이 높은 chunk만 필터링
- 필터링된 chunk를 verified_chunks로 반환

[입력 State]
- user_question: str - 사용자 질문
- retrieved_chunks: list[dict] - 검색된 chunk 리스트

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
- verified_chunks: list[dict] - 검증된 chunk 리스트(score >= threshold 인 것만)
  - content: str - chunk 내용
  - metadata: dict - chunk 메타데이터
  - score: float - LLM이 판단한 유사도 점수 (0~1)
"""

from typing import Dict, Any, List
import json

# OpenAI SDK 사용 (환경에 따라 폴백 가능)
try:
    from openai import OpenAI
    _client = OpenAI()
except Exception:
    _client = None


def _build_chunk_preview(chunks: List[Dict[str, Any]], max_chunks: int = 10, max_chars: int = 400) -> str:
    """
    LLM 프롬프트에 넣기 좋은 형태로 chunk들을 정리
    - 최대 max_chunks개만 사용
    - 각 chunk는 max_chars 글자까지만 사용
    """
    lines = []
    for i, ch in enumerate(chunks[:max_chunks]):
        content = (ch.get("content") or "").replace("\n", " ").strip()
        if len(content) > max_chars:
            content = content[: max_chars - 3] + "..."
        lines.append(f"[{i}] {content}")
    return "\n".join(lines)


def _llm_score_chunks(user_question: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[int, float]:
    """
    gpt-5-mini를 사용해 각 chunk의 관련도 점수를 0~1 사이 float로 받는 함수
    반환값: { index: relevance_score }
    """
    if _client is None or not retrieved_chunks or not user_question.strip():
        return {}

    chunks_text = _build_chunk_preview(retrieved_chunks)

    system_msg = (
        "당신은 의료/정신건강 텍스트 검색 시스템의 '관련도 평가자'입니다.\n"
        "입력으로 사용자 질문과 여러 개의 후보 문단(chunk)이 주어집니다.\n\n"
        "각 chunk가 질문에 얼마나 관련이 있는지 0.0~1.0 사이의 실수 점수로 평가하세요.\n"
        "- 0.0에 가까울수록 거의 관련 없음\n"
        "- 1.0에 가까울수록 매우 관련 있음\n\n"
        "출력 형식은 반드시 JSON만 사용하세요. 예:\n"
        "{\n"
        '  "results": [\n'
        '    {"index": 0, "relevance": 0.92},\n'
        '    {"index": 1, "relevance": 0.10}\n'
        "  ]\n"
        "}\n"
        "추가 설명, 자연어 문장, 코드 블록(````), 주석 등은 절대 넣지 마세요."
    )

    user_msg = (
        f"[사용자 질문]\n{user_question}\n\n"
        "[후보 chunk 목록]\n"
        f"{chunks_text}\n\n"
        "위 chunk들 각각에 대해 관련도 점수를 평가해주세요."
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ]
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)

        results = data.get("results", [])
        index_to_score: Dict[int, float] = {}
        for item in results:
            try:
                idx = int(item.get("index"))
                score = float(item.get("relevance"))
                if 0.0 <= score <= 1.0 and 0 <= idx < len(retrieved_chunks):
                    index_to_score[idx] = score
            except Exception:
                continue

        return index_to_score

    except Exception as e:
        # LLM 오류 시 콘솔 로그 남기고 빈 dict 반환 → 폴백 로직 사용
        print(f"[eval_node] LLM 평가 중 오류 발생: {e}")
        return {}


def eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색된 chunk의 관련성을 LLM으로 검증하는 노드
    """
    user_question = state.get("user_question", "")
    retrieved_chunks = state.get("retrieved_chunks", []) or []

    # 아무 것도 없으면 바로 반환
    if not retrieved_chunks or not user_question.strip():
        return {
            "user_question": user_question,
            "verified_chunks": []
        }

    # TODO: 임계값 기반 chunk 필터링

    # 기본 임계값
    threshold = 0.7

    # 1) LLM으로 관련도 점수 받기
    index_to_score = _llm_score_chunks(user_question, retrieved_chunks)

    verified_chunks: List[Dict[str, Any]] = []

    if index_to_score:
        # LLM 점수가 있으면 그 점수를 기준으로 필터링
        for idx, chunk in enumerate(retrieved_chunks):
            score = index_to_score.get(idx)
            if score is None:
                continue
            if score >= threshold:
                # chunk에 LLM 점수를 덮어써서 downstream에서 활용 가능하도록
                new_chunk = dict(chunk)
                new_chunk["score"] = float(score)
                verified_chunks.append(new_chunk)
    else:
        # 2) LLM 사용이 불가능하거나 실패한 경우, 기존 score 기반 필터링으로 폴백
        verified_chunks = [
            chunk for chunk in retrieved_chunks
            if float(chunk.get("score", 0)) >= threshold
        ]

    return {
        "user_question": user_question,
        "verified_chunks": verified_chunks
    }
