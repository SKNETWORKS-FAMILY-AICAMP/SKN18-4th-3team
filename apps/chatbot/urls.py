from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # 메인 페이지
    path('', views.chat_view, name='chat'),
    path('chat/', views.chat_view, name='chat'),

    # 대화 세션 관리 (로그인 사용자만) - RESTful API
    path('api/conversations/', views.ConversationListCreateView.as_view(), name='conversation_list_create'),
    path('api/conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),

    # 메시지 송수신 - RESTful API
    path('api/conversations/<int:conversation_id>/messages/', views.MessageListCreateView.as_view(), name='message_list_create'),

    # 비로그인 사용자 대화 (저장 안됨)
    path('api/chat/', views.guest_chat_view, name='guest_chat'),
]
