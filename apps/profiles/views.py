from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import User
from apps.chatbot.models import Conversation, Message


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """프로필 조회"""
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'profile_image': user.profile_image.url if user.profile_image else None,
        'created_at': user.created_at
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def profile_update_view(request):
    """프로필 업데이트 (사용자명만 변경 가능)"""
    user = request.user
    username = request.data.get('username')

    if not username:
        return Response({'error': '사용자명을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    user.username = username
    user.save()

    return Response({
        'message': '프로필이 수정되었습니다.',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'profile_image': user.profile_image.url if user.profile_image else None
        }
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """비밀번호 변경"""
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')

    if not all([current_password, new_password, new_password_confirm]):
        return Response({'error': '모든 필드를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 현재 비밀번호 확인
    if not user.check_password(current_password):
        return Response({'error': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    # 새 비밀번호 일치 확인
    if new_password != new_password_confirm:
        return Response({'error': '새 비밀번호가 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    # 비밀번호 유효성 검사
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({'message': '비밀번호가 변경되었습니다.'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """계정 삭제"""
    password = request.data.get('password')

    if not password:
        return Response({'error': '비밀번호를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 비밀번호 확인
    if not request.user.check_password(password):
        return Response({'error': '비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    request.user.delete()
    return Response({'message': '계정이 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_image_view(request):
    """프로필 이미지 업로드"""
    if 'profile_image' not in request.FILES:
        return Response({'error': '이미지 파일을 업로드해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user.profile_image = request.FILES['profile_image']
    user.save()

    return Response({
        'message': '프로필 이미지가 업로드되었습니다.',
        'profile_image': user.profile_image.url
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_statistics_view(request):
    """사용자 통계 조회 (주간/월간 대화 통계)"""
    user = request.user
    now = timezone.now()

    # 주간 통계 (최근 7일)
    week_ago = now - timedelta(days=7)
    weekly_conversations = Conversation.objects.filter(
        user=user,
        created_at__gte=week_ago
    ).count()
    weekly_messages = Message.objects.filter(
        conversation__user=user,
        role='user',
        created_at__gte=week_ago
    ).count()

    # 월간 통계 (최근 30일)
    month_ago = now - timedelta(days=30)
    monthly_conversations = Conversation.objects.filter(
        user=user,
        created_at__gte=month_ago
    ).count()
    monthly_messages = Message.objects.filter(
        conversation__user=user,
        role='user',
        created_at__gte=month_ago
    ).count()

    # 전체 통계
    total_conversations = Conversation.objects.filter(user=user).count()
    total_messages = Message.objects.filter(
        conversation__user=user,
        role='user'
    ).count()

    return Response({
        'weekly': {
            'conversations': weekly_conversations,
            'messages': weekly_messages
        },
        'monthly': {
            'conversations': monthly_conversations,
            'messages': monthly_messages
        },
        'total': {
            'conversations': total_conversations,
            'messages': total_messages
        }
    })