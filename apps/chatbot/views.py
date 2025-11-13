from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def chat_view(request):
    """채팅 메인 뷰 (로그인 필수)"""
    return render(request, 'chatbot/chatbot.html')



# 챗 스트림
# generate_answer
    # 랭그래프 노드 가져오기
    # 노드별 실행 과정을 "생각"처럼 보여주기
    # stream_mode="updates"
    # 대화 작성 시가 표시
    # 응답 중단 버튼 생성


# 챗 히스토리
    # 챗 요약
    # 마지막 대화 시간 표시
    # 


# 종료된 대화 감정분류 (대화 리스트에 감정 그래프 표시)
    # 구현예정. 감정분류 모델을 붙여넣어서, 종료된 대화의 감정을 분류하고 상위 3개의 감정을 바안에 색깔로 표시