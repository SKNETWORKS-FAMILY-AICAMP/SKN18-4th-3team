# rag/test_eval_node.py

"""
eval_node.py 단위 테스트 파일

목적:
- LLM이 chunk별로 question_relevance / answer_helpfulness 점수를 잘 생성하는지 확인
- total_score = relevance + helpfulness 계산 및 THRESHOLD 필터링 검증
- verified_chunks에 필터링된 chunk가 잘 들어오는지 체크
"""

from dotenv import load_dotenv
load_dotenv()  # 루트의 .env에서 OPENAI_API_KEY 읽기

from rag.graph.nodes.eval_node import eval_node


def main():
    test_state = {
        "user_question": "불안장애가 있으면 어떤 증상들이 나타나나요?",
        "retrieved_chunks": [
            {
                "content": "불안장애는 지속적인 불안과 긴장감을 특징으로 합니다.",
                "metadata": {"doc_id": 1},
            },
            {
                "content": "ADHD는 주의력 결핍과 과잉 행동을 보이는 신경발달장애입니다.",
                "metadata": {"doc_id": 2},
            },
            {
                "content": "불안장애 치료는 약물치료와 인지행동치료가 있습니다.",
                "metadata": {"doc_id": 3},
            },
        ],
    }

    print("\n===== eval_node TEST START =====")
    result = eval_node(test_state)

    print("\n----- 최종 결과 (verified_chunks) -----")
    print(result)

    print("\n===== eval_node TEST END =====\n")


if __name__ == "__main__":
    main()
