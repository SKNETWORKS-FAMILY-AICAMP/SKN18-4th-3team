from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message, SentimentAnalysis
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

# 랭그래프 import (Python 패키지 구조 사용)
try:
    from rag.build_graph import get_app
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: 랭그래프를 import할 수 없습니다: {e}")
    LANGGRAPH_AVAILABLE = False


# 노드 설명 매핑
NODE_DESCRIPTIONS = {
    "classify": "질문 분류 중...",
    "search_vectordb": "관련 정보 검색 중...",
    "eval": "정보 검증 중...",
    "sql_search": "데이터베이스 검색 중...",
    "state_check": "상태 확인 중...",
    "question": "질문 생성 중...",
    "slot_memory": "정보 통합 중...",
    "extract": "증상 추출 중...",
    "chat_llm": "답변 생성 중...",
}

# 핵심 노드만 필터링 (사용자에게 표시할 노드)
KEY_NODES = {
    "classify", "search_vectordb", "eval", "sql_search",
    "state_check", "question", "slot_memory", "extract", "chat_llm"
}


def run_langgraph(user_question, conversation_state=None, user_answer=None):
    """
    랭그래프를 실행하고 노드 실행 이벤트를 수집하여 thinking_process 생성
    
    Args:
        user_question: 사용자 질문 (최초 질문 또는 답변)
        conversation_state: 이전 대화 상태 (slot_data, slot_status 등) - 상담형 대화용
        user_answer: 사용자 답변 (상담형 질문에 대한 답변) - 선택적
    
    Returns:
        tuple: (response_content, thinking_process, bot_question, updated_state)
        - response_content: 최종 답변 또는 None (상담형 질문인 경우)
        - thinking_process: 노드 실행 과정
        - bot_question: 상담형 질문 (question 노드에서 생성된 질문, None일 수 있음)
        - updated_state: 업데이트된 대화 상태 (다음 호출 시 사용)
    """
    if not LANGGRAPH_AVAILABLE:
        return "챗봇 응답 (랭그래프 연동 필요)", [
            {"node": "classify", "description": "질문 분류 중...", "order": 1},
            {"node": "retrieve", "description": "관련 정보 검색 중...", "order": 2},
            {"node": "generate", "description": "응답 생성 중...", "order": 3}
        ], None, None
    
    try:
        app = get_app()
        
        # 초기 상태 설정
        initial_state = {
            "user_question": user_question,
            "initial_question": user_question,
        }
        
        # 이전 대화 상태 복원 (상담형 대화의 경우)
        if conversation_state:
            initial_state.update(conversation_state)
        
        # 사용자 답변이 있으면 state에 추가 (상담형 질문에 대한 답변)
        if user_answer:
            initial_state["user_answer"] = user_answer
        
        # 그래프 실행 및 노드 이벤트 수집
        thinking_process = []
        final_answer = None
        bot_question = None
        updated_state = None
        order = 1

        # invoke를 사용하여 그래프 실행 (stream 대신 사용하여 GeneratorExit 방지)
        # recursion_limit=200: 상담형 대화의 순환 구조 대응 (7개 slot × 3노드 × 반복 + 여유분)
        try:
            # invoke로 전체 실행
            final_result = app.invoke(initial_state, {"recursion_limit": 200})
            
            if isinstance(final_result, dict):
                # thinking_process는 간단하게 구성 (실제 노드 실행 순서는 추적 안 함)
                question_type = final_result.get("question_type", "").lower()
                
                # 질문 타입에 따라 thinking_process 구성
                if question_type == "counseling":
                    thinking_process = [
                        {"node": "classify", "description": "질문 분류 중...", "order": 1},
                        {"node": "state_check", "description": "상태 확인 중...", "order": 2},
                    ]
                    if final_result.get("bot_question"):
                        thinking_process.append({"node": "question", "description": "질문 생성 중...", "order": 3})
                    else:
                        thinking_process.extend([
                            {"node": "slot_memory", "description": "정보 통합 중...", "order": 3},
                            {"node": "extract", "description": "증상 추출 중...", "order": 4},
                            {"node": "search_vectordb", "description": "관련 정보 검색 중...", "order": 5},
                            {"node": "chat_llm", "description": "답변 생성 중...", "order": 6},
                        ])
                else:
                    thinking_process = [
                        {"node": "classify", "description": "질문 분류 중...", "order": 1},
                        {"node": "search_vectordb", "description": "관련 정보 검색 중...", "order": 2},
                        {"node": "eval", "description": "정보 검증 중...", "order": 3},
                    ]
                    if final_result.get("related_images"):
                        thinking_process.append({"node": "sql_search", "description": "데이터베이스 검색 중...", "order": 4})
                        thinking_process.append({"node": "chat_llm", "description": "답변 생성 중...", "order": 5})
                    else:
                        thinking_process.append({"node": "chat_llm", "description": "답변 생성 중...", "order": 4})
                
                # 상담형 질문 추출
                if "bot_question" in final_result:
                    bot_question = final_result.get("bot_question")
                    updated_state = {
                        "slot_data": final_result.get("slot_data", {}),
                        "slot_status": final_result.get("slot_status", {}),
                        "current_slot": final_result.get("current_slot"),
                        "initial_question": final_result.get("initial_question", user_question),
                        "question_type": final_result.get("question_type"),
                    }
                # 최종 답변 추출
                elif "final_answer" in final_result:
                    final_answer = final_result.get("final_answer")
                    # 관련 이미지도 함께 추출
                    if "related_images" in final_result:
                        related_images = final_result.get("related_images", [])
                    updated_state = {
                        "slot_data": final_result.get("slot_data", {}),
                        "slot_status": final_result.get("slot_status", {}),
                        "question_type": final_result.get("question_type"),
                    }
                else:
                    final_answer = "답변을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            else:
                final_answer = "답변을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
                
        except Exception as invoke_error:
            # invoke 실패 시 에러 처리
            print(f"invoke 오류: {invoke_error}")
            import traceback
            traceback.print_exc()
            final_answer = f"답변 생성 중 오류가 발생했습니다. (오류: {str(invoke_error)})"
            thinking_process = [
                {"node": "error", "description": f"오류 발생: {str(invoke_error)}", "order": 1}
            ]
        
        return final_answer, thinking_process, bot_question, updated_state
        
    except Exception as e:
        import traceback
        error_msg = f"랭그래프 실행 오류: {e}"
        error_trace = traceback.format_exc()
        print(error_msg)
        print(error_trace)
        
        # 로깅 (Django 로거 사용)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"랭그래프 실행 오류: {error_msg}")
        logger.error(f"스택 트레이스: {error_trace}")
        
        return f"답변 생성 중 오류가 발생했습니다. (오류: {str(e)})", [
            {"node": "error", "description": f"오류 발생: {str(e)}", "order": 1}
        ], None, None


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_view(request):
    """채팅 메인 페이지"""
    if request.user.is_authenticated:
        return Response({
            'is_authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'profile_image': request.user.profile_image.url if request.user.profile_image else None
            }
        })
    else:
        return Response({'is_authenticated': False, 'user': None})


class ConversationListCreateView(generics.ListCreateAPIView):
    """대화 세션 목록 조회 및 생성 (로그인 사용자만)"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by('-updated_at')

    def list(self, request, *args, **kwargs):
        """대화 세션 목록 전체 반환 (무한 스크롤용)"""
        queryset = self.get_queryset()
        conversations = []

        for conv in queryset:
            # 마지막 사용자 메시지 가져오기
            last_user_message = conv.messages.filter(role='user').order_by('-created_at').first()
            last_message_preview = ''

            if last_user_message:
                decrypted_content = last_user_message.get_decrypted_content()
                last_message_preview = decrypted_content[:50] + ('...' if len(decrypted_content) > 50 else '')

            # 이 대화의 사용자 메시지들의 감정 통계 계산
            user_message_ids = conv.messages.filter(role='user').values_list('id', flat=True)
            sentiment_stats = SentimentAnalysis.objects.filter(
                message_id__in=user_message_ids
            ).aggregate(
                positive=Count('id', filter=Q(sentiment_type='positive')),
                negative=Count('id', filter=Q(sentiment_type='negative')),
                neutral=Count('id', filter=Q(sentiment_type='neutral'))
            )

            total_sentiments = sentiment_stats['positive'] + sentiment_stats['negative'] + sentiment_stats['neutral']

            # 퍼센테이지 계산
            if total_sentiments > 0:
                sentiment_percentages = {
                    'positive': round((sentiment_stats['positive'] / total_sentiments * 100), 1),
                    'negative': round((sentiment_stats['negative'] / total_sentiments * 100), 1),
                    'neutral': round((sentiment_stats['neutral'] / total_sentiments * 100), 1)
                }
            else:
                # TODO: 추후 삭제 - 임시 하드코딩 (감정 분석 연동 전까지)
                # 대화별로 다른 비율을 보여주기 위해 대화 ID 기반으로 생성
                import random
                random.seed(conv.id)  # 대화 ID를 시드로 사용하여 일관된 값 생성
                negative = round(random.uniform(10, 40), 1)
                neutral = round(random.uniform(20, 50), 1)
                positive = round(100 - negative - neutral, 1)
                sentiment_percentages = {
                    'positive': positive,
                    'negative': negative,
                    'neutral': neutral
                }

            conversations.append({
                'id': conv.id,
                'title': conv.title or 'Untitled',
                'created_at': conv.created_at,
                'updated_at': conv.updated_at,
                'message_count': conv.messages.count(),
                'last_message_preview': last_message_preview,
                'sentiment_percentages': sentiment_percentages
            })

        return Response(conversations)

    def create(self, request, *args, **kwargs):
        """새 대화 세션 생성 (챗봇 첫 응답 시 자동 생성)"""
        title = request.data.get('title', '')
        conversation = Conversation.objects.create(user=request.user, title=title)
        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
            'message_count': 0
        }, status=status.HTTP_201_CREATED)


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    """대화 세션 상세 조회 및 삭제 (로그인 사용자만)"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        conversation = get_object_or_404(Conversation, id=kwargs['pk'], user=request.user)
        messages = [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.get_decrypted_content(),  # 복호화된 내용 반환
            'thinking_process': msg.thinking_process,
            'created_at': msg.created_at
        } for msg in conversation.messages.all().order_by('created_at')]

        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
            'messages': messages
        })

    def destroy(self, request, *args, **kwargs):
        conversation = get_object_or_404(Conversation, id=kwargs['pk'], user=request.user)
        conversation.delete()
        return Response({'message': '대화 세션이 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)


class MessageListCreateView(generics.ListCreateAPIView):
    """메시지 목록 조회 및 전송 (로그인 사용자만)"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(
            conversation_id=conversation_id,
            conversation__user=self.request.user
        ).order_by('created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        messages = [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.get_decrypted_content(),  # 복호화된 내용 반환
            'thinking_process': msg.thinking_process,
            'created_at': msg.created_at
        } for msg in queryset]
        return Response({'count': len(messages), 'results': messages})

    def create(self, request, *args, **kwargs):
        """사용자 메시지 전송 및 챗봇 응답 생성"""
        conversation_id = self.kwargs['conversation_id']
        content = request.data.get('content')
        conversation_state = request.data.get('conversation_state')  # 상담형 대화 상태
        is_answer = request.data.get('is_answer', False)  # 상담형 질문에 대한 답변인지

        if not content:
            return Response({'error': '메시지 내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

        # 사용자 메시지 저장
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=content
        )

        # 랭그래프 호출 및 thinking_process 생성
        # 상담형 질문에 대한 답변인 경우 user_answer로 전달
        user_answer = content if is_answer else None
        final_answer, thinking_process, bot_question, updated_state = run_langgraph(
            content if not is_answer else conversation_state.get('initial_question', content),
            conversation_state=conversation_state,
            user_answer=user_answer
        )

        # 상담형 질문인 경우 (bot_question이 있으면)
        if bot_question:
            # 질문만 저장하고 사용자 응답 대기
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=bot_question,  # 상담형 질문을 content로 저장
                thinking_process=thinking_process
            )
            
            return Response({
                'user_message': {
                    'id': user_message.id,
                    'role': user_message.role,
                    'content': user_message.get_decrypted_content(),
                    'created_at': user_message.created_at
                },
                'assistant_message': {
                    'id': assistant_message.id,
                    'role': assistant_message.role,
                    'content': assistant_message.get_decrypted_content(),
                    'thinking_process': assistant_message.thinking_process,
                    'created_at': assistant_message.created_at
                },
                'bot_question': bot_question,  # 상담형 질문
                'conversation_state': updated_state,  # 다음 호출 시 사용할 상태
                'requires_answer': True  # 사용자 답변 필요
            }, status=status.HTTP_201_CREATED)
        else:
            # 일반 답변인 경우
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=final_answer or "답변을 생성하는 중 문제가 발생했습니다.",
                thinking_process=thinking_process
            )

            return Response({
                'user_message': {
                    'id': user_message.id,
                    'role': user_message.role,
                    'content': user_message.get_decrypted_content(),
                    'created_at': user_message.created_at
                },
                'assistant_message': {
                    'id': assistant_message.id,
                    'role': assistant_message.role,
                    'content': assistant_message.get_decrypted_content(),
                    'thinking_process': assistant_message.thinking_process,
                    'created_at': assistant_message.created_at
                },
                'requires_answer': False  # 사용자 답변 불필요
            }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_chat_view(request):
    """게스트 사용자 대화 (대화 내용 저장 안됨)"""
    content = request.data.get('content')
    conversation_state = request.data.get('conversation_state')  # 상담형 대화 상태
    is_answer = request.data.get('is_answer', False)  # 상담형 질문에 대한 답변인지

    if not content:
        return Response({'error': '메시지 내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 랭그래프 호출 및 thinking_process 생성
    # 상담형 질문에 대한 답변인 경우 user_answer로 전달
    user_answer = content if is_answer else None
    final_answer, thinking_process, bot_question, updated_state = run_langgraph(
        content if not is_answer else conversation_state.get('initial_question', content) if conversation_state else content,
        conversation_state=conversation_state,
        user_answer=user_answer
    )

    # 상담형 질문인 경우 (bot_question이 있으면)
    if bot_question:
        return Response({
            'response': bot_question,  # 상담형 질문
            'thinking_process': thinking_process,
            'bot_question': bot_question,
            'conversation_state': updated_state,  # 다음 호출 시 사용할 상태
            'requires_answer': True  # 사용자 답변 필요
        })
    else:
        # 일반 답변인 경우
        return Response({
            'response': final_answer or "답변을 생성하는 중 문제가 발생했습니다.",
            'thinking_process': thinking_process,
            'requires_answer': False  # 사용자 답변 불필요
        })
