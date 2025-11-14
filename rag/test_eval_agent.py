from dotenv import load_dotenv
load_dotenv()

from rag.graph.agents.eval_agent import eval_agent, route_after_eval

state = {
    "user_question": "불안장애가 있으면 어떤 증상들이 나타나나요?",
    "retrieved_chunks": [
        {"content": "불안장애는 지속적인 불안과 긴장감을 특징으로 합니다.", "metadata": {"doc_id": 1}},
    ]
}

after_eval = eval_agent(state)
print("[after_eval]", after_eval)

route = route_after_eval(after_eval)
print("[route]", route)
