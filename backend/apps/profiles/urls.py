from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # 마이페이지 - 프로필 조회 및 수정
    path('', views.profile_view, name='profile'),
    path('update/', views.profile_update_view, name='profile_update'),
    path('password/', views.change_password_view, name='change_password'),
    path('delete/', views.delete_account_view, name='delete_account'),
    path('upload-image/', views.upload_profile_image_view, name='upload_profile_image'),

    # 대시보드 차트 API 엔드포인트 (6개)
    path('api/kpi/', views.dashboard_api_kpi, name='api_kpi'),
    path('api/conversation-frequency/', views.dashboard_api_conversation_frequency, name='api_conversation_frequency'),
    path('api/hourly-pattern/', views.dashboard_api_hourly_pattern, name='api_hourly_pattern'),
    path('api/sentiment-distribution/', views.dashboard_api_sentiment_distribution, name='api_sentiment_distribution'),
    path('api/emotion-keywords/', views.dashboard_api_emotion_keywords, name='api_emotion_keywords'),
    path('api/top-diseases/', views.dashboard_api_top_diseases, name='api_top_diseases'),
]
