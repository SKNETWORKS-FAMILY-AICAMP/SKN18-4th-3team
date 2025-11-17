"""
상담형 대화 흐름 추적 테스트
- 프론트엔드 상태 저장 시뮬레이션
- 백엔드 상태 복원 시뮬레이션
- 각 노드 실행 시 state 변화 추적
- 실제 views.py 로직 재현
"""

from rag.build_graph import get_app
import json


class Colors:
    """터미널 색상"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_separator(char="=", length=80):
    print(char * length)


def print_header(text, color=Colors.HEADER):
    print(f"\n{color}{Colors.BOLD}")
    print_separator()
    print(f"  {text}")
    print_separator()
    print(Colors.END)


def print_state(title, state, color=Colors.CYAN):
    """State 내용을 보기 좋게 출력"""
    print(f"\n{color}{Colors.BOLD}[{title}]{Colors.END}")
    print_separator("-", 80)
    
    # 주요 필드만 출력
    important_fields = [
        "user_question",
        "initial_question",
        "question_type",
        "user_answer",
        "current_slot",
        "slot_data",
        "slot_status",
        "bot_question",
        "final_answer",
    ]
    
    for field in important_fields:
        if field in state and state[field] is not None:
            value = state[field]
            
            # 긴 텍스트는 줄여서 표시
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            
            # dict는 JSON 형식으로
            if isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            
            print(f"  {field}: {value}")
    
    print_separator("-", 80)


def simulate_frontend_backend_flow():
    """프론트-백 상태 흐름 시뮬레이션"""
    print_header("상담형 대화 프론트-백 흐름 시뮬레이션", Colors.HEADER)
    
    print(f"\n{Colors.YELLOW}이 테스트는 실제 프론트엔드-백엔드 상태 교환을 시뮬레이션합니다.{Colors.END}")
    print(f"{Colors.YELLOW}각 단계에서 어떤 데이터가 저장되고 전달되는지 확인하세요.{Colors.END}\n")
    
    # 그래프 로드
    app = get_app()
    
    # 프론트엔드 상태 (메모리)
    frontend_state = {
        "conversation_state": None,
        "requires_answer": False,
    }
    
    # 초기 질문 입력
    print_separator("=", 80)
    initial_question = input(f"{Colors.GREEN}[사용자 입력] 첫 질문을 입력하세요: {Colors.END}").strip()
    
    if not initial_question:
        print(f"{Colors.RED}질문을 입력해주세요.{Colors.END}")
        return
    
    turn = 0
    max_turns = 10
    
    while turn < max_turns:
        turn += 1
        
        print_header(f"Turn {turn}: 그래프 실행", Colors.BLUE)
        
        # ===== 백엔드: initial_state 구성 =====
        print(f"\n{Colors.CYAN}{Colors.BOLD}[백엔드] initial_state 구성{Colors.END}")
        
        if turn == 1:
            # 첫 번째 턴
            initial_state = {
                "user_question": initial_question,
                "initial_question": initial_question,
            }
            print(f"  - 첫 질문: {initial_question}")
            print(f"  - conversation_state: None")
            print(f"  - user_answer: None")
        else:
            # 사용자 답변 입력
            print_separator("=", 80)
            user_answer = input(f"{Colors.GREEN}[사용자 입력] 답변을 입력하세요 (quit=종료): {Colors.END}").strip()
            
            if user_answer.lower() == 'quit' or not user_answer:
                print(f"\n{Colors.YELLOW}테스트를 종료합니다.{Colors.END}")
                break
            
            # 백엔드: state 복원
            initial_state = {
                "user_question": frontend_state["conversation_state"]["initial_question"],
                "initial_question": frontend_state["conversation_state"]["initial_question"],
            }
            
            # conversation_state 복원
            initial_state.update(frontend_state["conversation_state"])
            
            # user_answer 추가
            initial_state["user_answer"] = user_answer
            
            print(f"  - initial_question 유지: {initial_state['initial_question']}")
            print(f"  - conversation_state 복원: ✓")
            print(f"  - user_answer 추가: {user_answer}")
        
        print_state("백엔드 initial_state", initial_state, Colors.CYAN)
        
        # ===== 그래프 실행 =====
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[그래프 실행 중...]{Colors.END}")
        
        try:
            # 스트리밍으로 각 노드 실행 추적
            node_count = 0
            current_state = initial_state.copy()
            final_result = None
            
            for event in app.stream(initial_state, {"recursion_limit": 200}):
                # event는 {node_name: output_state} 형태
                for node_name, output_state in event.items():
                    node_count += 1
                    
                    print(f"\n{Colors.BLUE}{'━' * 80}{Colors.END}")
                    print(f"{Colors.BLUE}{Colors.BOLD}[노드 #{node_count}] {node_name}{Colors.END}")
                    print(f"{Colors.BLUE}{'━' * 80}{Colors.END}")
                    
                    # 노드 INPUT 표시 (현재 누적 state)
                    print(f"\n{Colors.CYAN}📥 INPUT (이 노드가 받은 state):{Colors.END}")
                    important_input_fields = [
                        "user_question", "initial_question", "question_type",
                        "user_answer", "current_slot", "slot_data", "slot_status",
                        "bot_question", "retrieved_chunks", "verified_chunks"
                    ]
                    
                    has_input = False
                    for key in important_input_fields:
                        if key in current_state and current_state[key] is not None:
                            has_input = True
                            value = current_state[key]
                            
                            # 값 포맷팅
                            if isinstance(value, str) and len(value) > 60:
                                display_value = value[:60] + "..."
                            elif isinstance(value, dict):
                                if key in ["slot_data", "slot_status"]:
                                    display_value = json.dumps(value, ensure_ascii=False)
                                else:
                                    display_value = f"{{...}} ({len(value)} keys)"
                            elif isinstance(value, list):
                                display_value = f"[{len(value)}개]"
                            else:
                                display_value = value
                            
                            print(f"  • {key}: {display_value}")
                    
                    if not has_input:
                        print(f"  (주요 필드 없음)")
                    
                    # 노드 OUTPUT 표시 (이 노드가 반환한 값)
                    print(f"\n{Colors.YELLOW}📤 OUTPUT (이 노드가 반환한 값):{Colors.END}")
                    if output_state:
                        has_output = False
                        for key, value in output_state.items():
                            if value is not None:
                                has_output = True
                                
                                # 값 포맷팅
                                if isinstance(value, str) and len(value) > 60:
                                    display_value = value[:60] + "..."
                                elif isinstance(value, dict):
                                    if key in ["slot_data", "slot_status"]:
                                        display_value = json.dumps(value, ensure_ascii=False)
                                    else:
                                        display_value = f"{{...}} ({len(value)} keys)"
                                elif isinstance(value, list):
                                    display_value = f"[{len(value)}개]"
                                else:
                                    display_value = value
                                
                                print(f"  • {key}: {display_value}")
                        
                        if not has_output:
                            print(f"  (반환값 없음)")
                        
                        # 현재 state 업데이트 (누적)
                        current_state.update(output_state)
                        final_result = current_state.copy()
                    else:
                        print(f"  (반환값 없음)")
            
            print(f"\n{Colors.GREEN}{'━' * 80}{Colors.END}")
            print(f"{Colors.GREEN}{Colors.BOLD}✓ 그래프 실행 완료 (총 {node_count}개 노드 실행){Colors.END}")
            print(f"{Colors.GREEN}{'━' * 80}{Colors.END}")
            
            # 최종 누적 state 표시
            print_state("그래프 최종 누적 state", final_result, Colors.YELLOW)
            
        except Exception as e:
            print(f"\n{Colors.RED}❌ 그래프 실행 오류: {e}{Colors.END}")
            import traceback
            traceback.print_exc()
            break
        
        # ===== 백엔드: 응답 구성 =====
        print(f"\n{Colors.CYAN}{Colors.BOLD}[백엔드] 응답 구성 (views.py 로직){Colors.END}")
        print(f"{Colors.CYAN}{'─' * 80}{Colors.END}")
        
        print(f"\n{Colors.YELLOW}📋 views.py 코드 실행:{Colors.END}")
        print(f"   if 'bot_question' in final_result:")
        print(f"       # 상담형 질문 → conversation_state 생성")
        print(f"   elif 'final_answer' in final_result:")
        print(f"       # 최종 답변 → requires_answer=False")
        
        if "bot_question" in final_result and final_result.get("bot_question"):
            # 상담형 질문 (views.py line 125-134)
            bot_question = final_result["bot_question"]
            
            print(f"\n{Colors.GREEN}✓ bot_question 발견!{Colors.END}")
            print(f"   → question 노드가 질문을 생성했음")
            
            # conversation_state 생성 (views.py와 동일)
            conversation_state = {
                "slot_data": final_result.get("slot_data", {}),
                "slot_status": final_result.get("slot_status", {}),
                "current_slot": final_result.get("current_slot"),
                "initial_question": final_result.get("initial_question"),
                "question_type": final_result.get("question_type"),
            }
            
            print(f"\n{Colors.CYAN}conversation_state 생성 과정:{Colors.END}")
            print(f"   conversation_state = {{")
            print(f"       'slot_data': final_result.get('slot_data', {{}})  # {len(conversation_state['slot_data'])}개")
            print(f"       'slot_status': final_result.get('slot_status', {{}})  # {len(conversation_state['slot_status'])}개")
            print(f"       'current_slot': final_result.get('current_slot')  # {conversation_state['current_slot']}")
            print(f"       'initial_question': final_result.get('initial_question')  # {conversation_state['initial_question']}")
            print(f"       'question_type': final_result.get('question_type')  # {conversation_state['question_type']}")
            print(f"   }}")
            
            requires_answer = True
            
            print(f"\n{Colors.CYAN}requires_answer 설정:{Colors.END}")
            print(f"   requires_answer = True  # bot_question이 있으니까")
            
            print(f"\n{Colors.GREEN}✓ 응답 구성 완료{Colors.END}")
            print(f"   - bot_question: {bot_question[:60]}...")
            print(f"   - requires_answer: True")
            print(f"   - conversation_state: 생성됨 (5개 필드)")
            
            response = {
                "bot_question": bot_question,
                "conversation_state": conversation_state,
                "requires_answer": requires_answer,
            }
            
        elif "final_answer" in final_result and final_result.get("final_answer"):
            # 최종 답변 (views.py line 136-143)
            final_answer = final_result["final_answer"]
            
            print(f"\n{Colors.GREEN}✓ final_answer 발견!{Colors.END}")
            print(f"   → chat_llm 노드가 최종 답변을 생성했음")
            
            requires_answer = False
            
            print(f"\n{Colors.CYAN}requires_answer 설정:{Colors.END}")
            print(f"   requires_answer = False  # final_answer가 있으니까")
            
            print(f"\n{Colors.GREEN}✓ 응답 구성 완료{Colors.END}")
            print(f"   - final_answer: 생성됨 (길이: {len(final_answer)}자)")
            print(f"   - requires_answer: False")
            
            response = {
                "final_answer": final_answer,
                "requires_answer": requires_answer,
                "related_images": final_result.get("related_images", []),
            }
            
        else:
            print(f"\n{Colors.RED}❌ 오류: bot_question도 final_answer도 없음{Colors.END}")
            print(f"   → 그래프가 예상치 못한 결과를 반환했습니다")
            break
        
        print(f"{Colors.CYAN}{'─' * 80}{Colors.END}")
        
        print_state("백엔드 응답 (프론트로 전송)", response, Colors.CYAN)
        
        # ===== 프론트엔드: 응답 처리 =====
        print(f"\n{Colors.GREEN}{Colors.BOLD}[프론트엔드] 응답 처리{Colors.END}")
        
        if response.get("bot_question"):
            # 상담형 질문
            print(f"\n{Colors.BOLD}[봇] {response['bot_question']}{Colors.END}")
            
            # 프론트엔드 상태 업데이트
            frontend_state["conversation_state"] = response["conversation_state"]
            frontend_state["requires_answer"] = response["requires_answer"]
            
            print(f"\n{Colors.GREEN}프론트엔드가 메모리에 저장하는 내용:{Colors.END}")
            print_separator("-", 80)
            
            # conversation_state 상세 출력
            print(f"\n{Colors.CYAN}1. conversation_state (다음 요청 시 백엔드로 전달):{Colors.END}")
            conv_state = response["conversation_state"]
            print(f"   • initial_question: {conv_state.get('initial_question')}")
            print(f"   • question_type: {conv_state.get('question_type')}")
            print(f"   • current_slot: {conv_state.get('current_slot')}")
            
            print(f"\n   • slot_data (수집된 답변):")
            slot_data = conv_state.get('slot_data', {})
            for slot, value in slot_data.items():
                if value:
                    print(f"     - {slot}: {value}")
            
            print(f"\n   • slot_status (완료 여부):")
            slot_status = conv_state.get('slot_status', {})
            filled = [k for k, v in slot_status.items() if v]
            unfilled = [k for k, v in slot_status.items() if not v]
            print(f"     - 완료: {', '.join(filled) if filled else '없음'}")
            print(f"     - 미완료: {', '.join(unfilled) if unfilled else '없음'}")
            
            print(f"\n{Colors.CYAN}2. requires_answer (답변 필요 플래그):{Colors.END}")
            print(f"   • {response['requires_answer']}")
            
            print(f"\n{Colors.YELLOW}💡 다음 사용자 입력 시:{Colors.END}")
            print(f"   • is_answer = {response['requires_answer']} (requiresAnswer 값 사용)")
            print(f"   • conversation_state = 위 내용 전체 전달")
            print_separator("-", 80)
            
        elif response.get("final_answer"):
            # 최종 답변
            print(f"\n{Colors.BOLD}[봇 최종 답변]{Colors.END}")
            print_separator("-", 80)
            print(response["final_answer"])
            print_separator("-", 80)
            
            # 관련 이미지
            if response.get("related_images"):
                print(f"\n{Colors.CYAN}관련 이미지: {len(response['related_images'])}개{Colors.END}")
            
            # 프론트엔드 상태 초기화
            frontend_state["conversation_state"] = None
            frontend_state["requires_answer"] = False
            
            print(f"\n{Colors.GREEN}프론트엔드 상태 초기화:{Colors.END}")
            print(f"  • conversation_state: None (상담 종료)")
            print(f"  • requires_answer: False (새 질문 모드)")
            
            print(f"\n{Colors.YELLOW}💡 다음 사용자 입력 시:{Colors.END}")
            print(f"  • is_answer = False (새로운 질문)")
            print(f"  • conversation_state = None")
            
            print(f"\n{Colors.GREEN}{'━' * 80}{Colors.END}")
            print(f"{Colors.GREEN}{Colors.BOLD}✓ 상담 완료!{Colors.END}")
            print(f"{Colors.GREEN}{'━' * 80}{Colors.END}")
            break
    
    if turn >= max_turns:
        print(f"\n{Colors.YELLOW}⚠️  최대 턴 수({max_turns})에 도달했습니다.{Colors.END}")


def main():
    """메인 실행"""
    try:
        simulate_frontend_backend_flow()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}테스트를 중단합니다.{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ 오류 발생: {e}{Colors.END}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
