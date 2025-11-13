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

    # 사용자 통계
    path('statistics/', views.user_statistics_view, name='statistics'),
]
