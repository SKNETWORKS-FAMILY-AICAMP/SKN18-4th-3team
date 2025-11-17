from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # 인증 관련 (로그인, 회원가입만)
    path('signup/', views.signup_view, name='signup'),
    path('signup/check-email/', views.check_email_view, name='check_email'),  # 이메일 중복 체크(실시간 검증)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
