from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractWeekDay, ExtractHour
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from .models import ChatSession, Message, SentimentAnalysis, DiseaseQuery


def get_user_for_request(request):
    """
    요청에서 사용자를 가져오는 헬퍼 함수
    로그인 기능이 완성되면 request.user를 그대로 사용
    개발 중에는 첫 번째 사용자를 사용 (테스트용)
    """
    if request.user.is_authenticated:
        return request.user

    # 개발 중: 첫 번째 사용자 사용 (로그인 구현 후 이 부분은 제거)
    # TODO: 로그인 기능 완성 후 이 부분을 제거하고 @login_required 데코레이터 추가
    user = User.objects.first()
    if not user:
        # 사용자가 없으면 자동으로 테스트 사용자 생성
        user = User.objects.create_user(username='testuser', password='testpass123')
    return user


def dashboard_view(request):
    """
    대시보드 메인 페이지 뷰
    사용자별 대화 통계 및 감정 분석 결과를 보여줌

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)
    context = {
        'user': user,
    }
    return render(request, 'chatbot/dashboard.html', context)


def dashboard_api_kpi(request):
    """
    KPI 데이터를 반환하는 API
    - 총 대화 횟수
    - 총 메시지 수

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)

    # 총 대화 횟수
    total_sessions = ChatSession.objects.filter(user=user).count()

    # 총 메시지 수 (사용자가 보낸 메시지만)
    total_messages = Message.objects.filter(
        session__user=user,
        sender='user'
    ).count()

    data = {
        'total_sessions': total_sessions,
        'total_messages': total_messages,
    }

    return JsonResponse(data)


def dashboard_api_conversation_frequency(request):
    """
    최근 7일 대화 빈도 데이터를 반환하는 API

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    # 최근 7일간의 날짜별 대화 횟수
    sessions = ChatSession.objects.filter(
        user=user,
        created_at__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # 날짜별로 데이터 정리
    date_counts = {session['date']: session['count'] for session in sessions}

    # 7일치 데이터 생성 (데이터가 없는 날은 0으로)
    labels = []
    values = []
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        labels.append(date.strftime('%m/%d'))
        values.append(date_counts.get(date, 0))

    data = {
        'labels': labels,
        'values': values,
    }

    return JsonResponse(data)


def dashboard_api_hourly_pattern(request):
    """
    시간대별 대화 패턴 데이터를 반환하는 API (히트맵용)

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)

    # 모든 세션의 생성 시간을 가져옴
    sessions = ChatSession.objects.filter(user=user).annotate(
        weekday=ExtractWeekDay('created_at'),  # 1=일요일, 2=월요일, ..., 7=토요일
        hour=ExtractHour('created_at')
    ).values('weekday', 'hour').annotate(
        count=Count('id')
    )

    # 요일별, 시간대별 데이터 구조화
    # weekday: 1(일) ~ 7(토) -> 0(월) ~ 6(일)로 변환
    heatmap_data = [[0 for _ in range(24)] for _ in range(7)]

    for session in sessions:
        weekday = session['weekday']
        # Django의 ExtractWeekDay: 1=일요일, 2=월요일, ..., 7=토요일
        # 배열 인덱스: 0=월요일, 1=화요일, ..., 6=일요일로 변환
        if weekday == 1:  # 일요일
            day_index = 6
        else:  # 월요일~토요일
            day_index = weekday - 2

        hour = session['hour']
        count = session['count']

        heatmap_data[day_index][hour] = count

    data = {
        'heatmap_data': heatmap_data,
        'weekdays': ['월', '화', '수', '목', '금', '토', '일'],
        'hours': list(range(24)),
    }

    return JsonResponse(data)


def dashboard_api_sentiment_distribution(request):
    """
    감정 분포 데이터를 반환하는 API (파이차트용)

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)

    # 감정별 카운트
    sentiment_counts = SentimentAnalysis.objects.filter(
        message__session__user=user
    ).values('sentiment_type').annotate(
        count=Count('id')
    )

    # 데이터 정리
    data_dict = {item['sentiment_type']: item['count'] for item in sentiment_counts}

    positive_count = data_dict.get('positive', 0)
    negative_count = data_dict.get('negative', 0)
    neutral_count = data_dict.get('neutral', 0)

    data = {
        'labels': ['긍정', '부정', '중립'],
        'values': [positive_count, negative_count, neutral_count],
    }

    return JsonResponse(data)


def dashboard_api_emotion_keywords(request):
    """
    감정 키워드 데이터를 반환하는 API (워드 클라우드용)

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)

    # 모든 감정 분석 결과에서 키워드 추출
    sentiments = SentimentAnalysis.objects.filter(
        message__session__user=user
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

    data = {
        'keywords': keywords_data,
    }

    return JsonResponse(data)


def dashboard_api_top_diseases(request):
    """
    자주 검색한 질환 TOP 10 데이터를 반환하는 API

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)

    # 질환별 검색 횟수
    disease_counts = DiseaseQuery.objects.filter(
        message__session__user=user
    ).values('disease_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # 데이터 정리
    labels = [item['disease_name'] for item in disease_counts]
    values = [item['count'] for item in disease_counts]

    data = {
        'labels': labels,
        'values': values,
    }

    return JsonResponse(data)


def dashboard_api_disease_trends(request):
    """
    주차별 질환 검색 추이 데이터를 반환하는 API

    TODO: 로그인 기능 완성 후 @login_required 데코레이터 추가
    """
    user = get_user_for_request(request)
    today = datetime.now()
    four_weeks_ago = today - timedelta(weeks=4)

    # 최근 4주간의 질환 검색 데이터
    disease_queries = DiseaseQuery.objects.filter(
        message__session__user=user,
        searched_at__gte=four_weeks_ago
    )

    # 주차별 질환 검색 카운트
    weekly_data = defaultdict(lambda: Counter())

    for query in disease_queries:
        # 주차 계산
        week_diff = (today.date() - query.searched_at.date()).days // 7
        week_label = f"{4 - week_diff}주차"

        weekly_data[week_label][query.disease_name] += 1

    # 상위 5개 질환 추출
    all_diseases = Counter()
    for week_data in weekly_data.values():
        all_diseases.update(week_data)

    top_diseases = [disease for disease, _ in all_diseases.most_common(5)]

    # 데이터 정리
    labels = [f"{i}주차" for i in range(1, 5)]
    datasets = []

    for disease in top_diseases:
        values = [weekly_data[label][disease] for label in labels]
        datasets.append({
            'label': disease,
            'data': values,
        })

    data = {
        'labels': labels,
        'datasets': datasets,
    }

    return JsonResponse(data)
