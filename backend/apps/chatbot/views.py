from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message, SentimentAnalysis
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_view(request):
    """채팅 메인 페이지 (로그인 사용자는 대화 저장, 게스트는 저장 안됨)"""
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

        if not content:
            return Response({'error': '메시지 내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

        # 사용자 메시지 저장
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=content
        )

        # TODO: 랭그래프 호출 (랭그래프 개발자가 제공하는 함수 사용)
        # 임시 응답
        assistant_content = "챗봇 응답 (랭그래프 연동 필요)"
        thinking_process = [
            {"node": "classify", "description": "질문 분류 중...", "order": 1},
            {"node": "retrieve", "description": "관련 정보 검색 중...", "order": 2},
            {"node": "generate", "description": "응답 생성 중...", "order": 3}
        ]

        # 챗봇 메시지 저장 (Signal로 대화 제목 자동 생성)
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_content,
            thinking_process=thinking_process
        )

        return Response({
            'user_message': {
                'id': user_message.id,
                'role': user_message.role,
                'content': user_message.get_decrypted_content(),  # 복호화된 내용 반환
                'created_at': user_message.created_at
            },
            'assistant_message': {
                'id': assistant_message.id,
                'role': assistant_message.role,
                'content': assistant_message.get_decrypted_content(),  # 복호화된 내용 반환
                'thinking_process': assistant_message.thinking_process,
                'created_at': assistant_message.created_at
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_chat_view(request):
    """게스트 사용자 대화 (대화 내용 저장 안됨)"""
    content = request.data.get('content')
    conversation_history = request.data.get('conversation_history', [])

    if not content:
        return Response({'error': '메시지 내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # TODO: 랭그래프 호출
    # 임시 응답
    assistant_content = "챗봇 응답 (랭그래프 연동 필요)"
    thinking_process = [
        {"node": "classify", "description": "질문 분류 중...", "order": 1},
        {"node": "retrieve", "description": "관련 정보 검색 중...", "order": 2},
        {"node": "generate", "description": "응답 생성 중...", "order": 3}
    ]

    return Response({'response': assistant_content, 'thinking_process': thinking_process})