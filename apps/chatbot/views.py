from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def chat_view(request):
    """채팅 메인 뷰 (로그인 필수)"""
    return render(request, 'chatbot/chatbot.html')
