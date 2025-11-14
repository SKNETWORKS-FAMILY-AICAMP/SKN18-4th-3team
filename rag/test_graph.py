"""
그래프 통합 테스트
- 정보형: 자동 테스트
- 상담형: 대화형 테스트 (터미널 입력)
- 각 노드 실행 상태 출력
"""

from rag.graph.nodes.classify_node import classify_node
from rag.graph.nodes.state_check_node import state_check_node
from rag.graph.nodes.question_node import question_node
from rag.graph.nodes.answer_node import answer_node
from rag.graph.nodes.slot_memory_node import slot_memory_node
from rag.graph.nodes.extract_node import extract_node
from rag.graph.nodes.search_vectordb_node import search_vectordb_node
from rag.graph.nodes.eval_node import eval_node
from rag.graph.nodes.sql_search_node import sql_search_node
from rag.graph.nodes.chat_llm_node import chat_llm_node
from rag.graph.agents.classify_agent import route_after_classify
from rag.graph.agents.state_check_agent import route_after_state_check
from rag.graph.agents.eval_agent import route_after_eval


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_node(node_name, state):
    print(f"\n{'-' * 70}")
    print(f"[노드] {node_name}")
    print(f"{'-' * 70}")
    
    # 주요 상태 출력
    if state.get("question_type"):
        print(f"  질문 유형: {state['question_type']}")
    
    if state.get("retrieved_chunks"):
        print(f"  검색된 청크: {len(state['retrieved_chunks'])}개")
    
    if state.get("verified_chunks"):
        print(f"  검증된 청크: {len(state['verified_chunks'])}개")
    
    if state.get("related_images"):
        print(f"  관련 이미지: {len(state['related_images'])}개")
    
    if state.get("bot_question"):
        print(f"  [봇 질문] {state['bot_question']}")
    
    if state.get("current_slot"):
        print(f"  현재 슬롯: {state['current_slot']}")
    
    if state.get("slot_status"):
        filled = sum(1 for v in state['slot_status'].values() if v)
        total = len(state['slot_status'])
        print(f"  슬롯 진행: {filled}/{total} 완료")
    
    if state.get("extracted_symptoms"):
        print(f"  추출된 증상: {state['extracted_symptoms']}")
    
    if state.get("final_answer"):
        print(f"  [완료] 최종 답변 생성됨 (길이: {len(state['final_answer'])}자)")


def test_information():
    """정보형 질문 테스트"""
    print_header("테스트 1: 정보형 질문")
    
    question = "우울증이란 무엇인가요?"
    print(f"\n[질문] {question}\n")
    
    state = {"user_question": question}
    
    try:
        # 1. classify
        state = classify_node(state)
        print_node("classify", state)
        
        next_route = route_after_classify(state)
        print(f"  → 다음 노드: {next_route}")
        
        if next_route != "search_vectordb":
            print(f"\n⚠️  예상과 다른 라우팅: {next_route}")
            return
        
        # 2. search_vectordb
        state = search_vectordb_node(state)
        print_node("search_vectordb", state)
        
        # 3. eval
        state = eval_node(state)
        print_node("eval", state)
        
        next_route = route_after_eval(state)
        print(f"  → 다음 노드: {next_route}")
        
        # 4. sql_search (조건부)
        if next_route == "sql_search":
            state = sql_search_node(state)
            print_node("sql_search", state)
        
        # 5. chat_llm
        state["node_type"] = "information"
        state = chat_llm_node(state)
        print_node("chat_llm", state)
        
        # 최종 답변 출력
        print(f"\n{'=' * 70}")
        print("[최종 답변]")
        print(f"{'=' * 70}")
        print(state.get("final_answer", "답변 없음"))
        print(f"{'=' * 70}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_counseling():
    """상담형 질문 테스트 (대화형)"""
    print_header("테스트 2: 상담형 질문 (대화형)")
    
    print("\n이 챗봇은 7가지 질문을 통해 당신의 상태를 파악합니다.")
    print("각 질문에 솔직하게 답변해주세요.")
    print("(테스트를 중단하려면 'quit' 입력)\n")
    
    # 초기 질문 받기
    print("-" * 70)
    initial_question = input("[당신] ").strip()
    
    if not initial_question or initial_question.lower() == 'quit':
        print("\n테스트를 종료합니다.")
        return False
    
    state = {"user_question": initial_question}
    
    try:
        # 1. classify
        state = classify_node(state)
        print_node("classify", state)
        
        next_route = route_after_classify(state)
        print(f"  → 다음 노드: {next_route}")
        
        if next_route != "state_check":
            print(f"\n⚠️  상담형이 아닙니다: {state.get('question_type')}")
            return False
        
        # 2. 상담 루프
        turn = 0
        max_turns = 10
        
        while turn < max_turns:
            turn += 1
            print(f"\n{'=' * 70}")
            print(f"  Turn {turn}")
            print(f"{'=' * 70}")
            
            # state_check
            result = state_check_node(state)
            state = {**state, **result}  # 상태 병합
            print_node("state_check", state)
            
            next_route = route_after_state_check(state)
            print(f"  → 다음 노드: {next_route}")
            
            if next_route == "slot_memory":
                # 모든 slot 완료
                print("\n[완료] 모든 질문이 완료되었습니다!")
                
                # slot_memory
                state = slot_memory_node(state)
                print_node("slot_memory", state)
                
                # extract
                state = extract_node(state)
                print_node("extract", state)
                
                # search_vectordb
                state = search_vectordb_node(state)
                print_node("search_vectordb", state)
                
                # eval (선택적)
                if state.get('retrieved_chunks'):
                    state = eval_node(state)
                    print_node("eval", state)
                    
                    next_route = route_after_eval(state)
                    print(f"  → 다음 노드: {next_route}")
                    
                    # sql_search (조건부)
                    if next_route == "sql_search":
                        state = sql_search_node(state)
                        print_node("sql_search", state)
                
                # chat_llm
                state["node_type"] = "counseling"
                state = chat_llm_node(state)
                print_node("chat_llm", state)
                
                # 최종 답변 출력
                print(f"\n{'=' * 70}")
                print("[최종 답변]")
                print(f"{'=' * 70}")
                print(state.get("final_answer", "답변 없음"))
                print(f"{'=' * 70}")
                
                break
            
            elif next_route == "question":
                # question
                result = question_node(state)
                state = {**state, **result}  # 상태 병합
                print_node("question", state)
                
                # 사용자 답변 받기
                print()
                user_answer = input("[당신] ").strip()
                
                if user_answer.lower() == 'quit':
                    print("\n상담을 중단합니다.")
                    return False
                
                if not user_answer:
                    print("⚠️  답변을 입력해주세요.")
                    continue
                
                # answer
                state["user_answer"] = user_answer
                result = answer_node(state)
                state = {**state, **result}  # 상태 병합
                print_node("answer", state)
            
            else:
                print(f"\n⚠️  예상치 못한 라우팅: {next_route}")
                break
        
        if turn >= max_turns:
            print(f"\n⚠️  최대 턴 수({max_turns})에 도달했습니다.")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n상담을 중단합니다.")
        return False
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print_header("정신건강 상담 챗봇 그래프 테스트")
    
    print("\n테스트 옵션:")
    print("  1. 정보형 질문 테스트 (자동)")
    print("  2. 상담형 질문 테스트 (대화형)")
    print("  3. 둘 다 테스트")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    results = []
    
    if choice in ['1', '3']:
        result = test_information()
        results.append(("정보형", result))
    
    if choice in ['2', '3']:
        result = test_counseling()
        results.append(("상담형", result))
    
    # 결과 요약
    if results:
        print_header("테스트 결과 요약")
        for name, result in results:
            status = "[성공]" if result else "[실패]"
            print(f"  {status} {name} 테스트")
        
        total = len(results)
        passed = sum(1 for _, r in results if r)
        print(f"\n  총 {total}개 테스트 중 {passed}개 통과")


if __name__ == "__main__":
    main()
