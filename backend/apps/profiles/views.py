from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractWeekDay, ExtractHour
from datetime import datetime, timedelta
from collections import Counter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.chatbot.models import Conversation, Message, SentimentAnalysis, DiseaseQuery
from .serializers import ProfileUpdateSerializer, ChangePasswordSerializer


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
    serializer = ProfileUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user.username = serializer.validated_data['username']
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
    serializer = ChangePasswordSerializer(data=request.data, context={'user': request.user})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']

    # 현재 비밀번호 확인
    if not user.check_password(current_password):
        return Response({'current_password': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

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
def dashboard_api_kpi(request):
    """
    KPI 데이터를 반환하는 API
    - 총 대화 횟수
    - 총 메시지 수
    """
    user = request.user

    # 총 대화 횟수
    total_conversations = Conversation.objects.filter(user=user).count()

    # 총 메시지 수 (사용자가 보낸 메시지만)
    total_messages = Message.objects.filter(
        conversation__user=user,
        role='user'
    ).count()

    return Response({
        'total_conversations': total_conversations,
        'total_messages': total_messages,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api_conversation_frequency(request):
    """
    최근 7일 대화 빈도 데이터를 반환하는 API
    """
    user = request.user
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    # 최근 7일간의 날짜별 대화 횟수
    conversations = Conversation.objects.filter(
        user=user,
        created_at__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # 날짜별로 데이터 정리
    date_counts = {conv['date']: conv['count'] for conv in conversations}

    # 7일치 데이터 생성 (데이터가 없는 날은 0으로)
    labels = []
    values = []
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        labels.append(date.strftime('%m/%d'))
        values.append(date_counts.get(date, 0))

    return Response({
        'labels': labels,
        'values': values,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api_hourly_pattern(request):
    """
    시간대별 대화 패턴 데이터를 반환하는 API (히트맵용)
    메시지 생성 시간을 기준으로 계산 (대화 세션이 아닌 실제 메시지 활동 시간)
    """
    user = request.user

    # 사용자가 보낸 메시지의 생성 시간을 가져옴 (실제 대화 활동 시간)
    messages = Message.objects.filter(
        conversation__user=user,
        role='user'  # 사용자 메시지만 (실제 대화 활동)
    ).annotate(
        weekday=ExtractWeekDay('created_at'),  # 1=일요일, 2=월요일, ..., 7=토요일
        hour=ExtractHour('created_at')
    ).values('weekday', 'hour').annotate(
        count=Count('id')
    )

    # 요일별, 시간대별 데이터 구조화
    # weekday: 1(일) ~ 7(토) -> 0(월) ~ 6(일)로 변환
    heatmap_data = [[0 for _ in range(24)] for _ in range(7)]

    for msg in messages:
        weekday = msg['weekday']
        # Django의 ExtractWeekDay: 1=일요일, 2=월요일, ..., 7=토요일
        # 배열 인덱스: 0=월요일, 1=화요일, ..., 6=일요일로 변환
        if weekday == 1:  # 일요일
            day_index = 6
        else:  # 월요일~토요일
            day_index = weekday - 2

        hour = msg['hour']
        count = msg['count']

        heatmap_data[day_index][hour] = count

    return Response({
        'heatmap_data': heatmap_data,
        'weekdays': ['월', '화', '수', '목', '금', '토', '일'],
        'hours': list(range(24)),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api_sentiment_distribution(request):
    """
    감정 분포 데이터를 반환하는 API (파이차트용)
    """
    user = request.user

    # 감정별 카운트
    sentiment_counts = SentimentAnalysis.objects.filter(
        message__conversation__user=user
    ).values('sentiment_type').annotate(
        count=Count('id')
    )

    # 데이터 정리
    data_dict = {item['sentiment_type']: item['count'] for item in sentiment_counts}

    positive_count = data_dict.get('positive', 0)
    negative_count = data_dict.get('negative', 0)
    neutral_count = data_dict.get('neutral', 0)

    return Response({
        'labels': ['긍정', '부정', '중립'],
        'values': [positive_count, negative_count, neutral_count],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api_emotion_keywords(request):
    """
    감정 키워드 데이터를 반환하는 API (워드 클라우드용)
    """
    user = request.user

    # 모든 감정 분석 결과에서 키워드 추출
    sentiments = SentimentAnalysis.objects.filter(
        message__conversation__user=user
    ).values('keywords', 'sentiment_type')

    # 키워드 빈도 계산
    keyword_counts = Counter()
    keyword_sentiments = {}  # 키워드별 감정 타입

    for sentiment in sentiments:
        keywords = sentiment['keywords']
        sentiment_type = sentiment['sentiment_type']

        for keyword in keywords:
            keyword_counts[keyword] += 1
            # 키워드가 처음 나타났을 때의 감정 타입 저장
            if keyword not in keyword_sentiments:
                keyword_sentiments[keyword] = sentiment_type

    # 상위 30개 키워드 추출
    top_keywords = keyword_counts.most_common(30)

    # 데이터 정리
    keywords_data = [
        {
            'text': keyword,
            'count': count,
            'sentiment': keyword_sentiments[keyword]
        }
        for keyword, count in top_keywords
    ]

    return Response({
        'keywords': keywords_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api_top_diseases(request):
    """
    자주 검색한 질환 TOP 10 데이터를 반환하는 API
    """
    user = request.user

    # 질환별 검색 횟수
    disease_counts = DiseaseQuery.objects.filter(
        message__conversation__user=user
    ).values('disease_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # 데이터 정리
    labels = [item['disease_name'] for item in disease_counts]
    values = [item['count'] for item in disease_counts]

    return Response({
        'labels': labels,
        'values': values,
    })

