"""
챗봇 앱 URL 설정
"""

from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # 대시보드 메인 페이지
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # 대시보드 API 엔드포인트
    path('api/kpi/', views.dashboard_api_kpi, name='api_kpi'),
    path('api/conversation-frequency/', views.dashboard_api_conversation_frequency, name='api_conversation_frequency'),
    path('api/hourly-pattern/', views.dashboard_api_hourly_pattern, name='api_hourly_pattern'),
    path('api/sentiment-distribution/', views.dashboard_api_sentiment_distribution, name='api_sentiment_distribution'),
    path('api/emotion-keywords/', views.dashboard_api_emotion_keywords, name='api_emotion_keywords'),
    path('api/top-diseases/', views.dashboard_api_top_diseases, name='api_top_diseases'),
    path('api/disease-trends/', views.dashboard_api_disease_trends, name='api_disease_trends'),
]
