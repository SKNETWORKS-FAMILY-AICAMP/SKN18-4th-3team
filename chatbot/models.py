from django.db import models
from django.contrib.auth.models import User

# 챗봇 대화 세션 모델
class ChatSession(models.Model):
    """
    대화 세션을 관리하는 모델
    "새 채팅" 버튼을 누를 때마다 새로운 세션이 생성됨
    """
    CONVERSATION_TYPES = [
        ('info', '정보형'),
        ('counseling', '상담형'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    session_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES, default='info', verbose_name='대화 타입')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='시작 시간')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='마지막 업데이트 시간')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')

    class Meta:
        db_table = 'chat_session'
        verbose_name = '대화 세션'
        verbose_name_plural = '대화 세션들'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# 개별 메시지 모델
class Message(models.Model):
    """
    사용자와 챗봇이 주고받은 개별 메시지를 저장하는 모델
    """
    SENDER_TYPES = [
        ('user', '사용자'),
        ('bot', '챗봇'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages', verbose_name='세션')
    sender = models.CharField(max_length=10, choices=SENDER_TYPES, verbose_name='발신자')
    content = models.TextField(verbose_name='메시지 내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 시간')

    class Meta:
        db_table = 'message'
        verbose_name = '메시지'
        verbose_name_plural = '메시지들'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} - {self.content[:50]}"


# 감정 분석 결과 모델
class SentimentAnalysis(models.Model):
    """
    메시지의 감정 분석 결과를 저장하는 모델
    HuggingFace 모델을 통해 자동으로 분석됨
    """
    SENTIMENT_TYPES = [
        ('positive', '긍정'),
        ('negative', '부정'),
        ('neutral', '중립'),
    ]

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='sentiment', verbose_name='메시지')
    sentiment_type = models.CharField(max_length=20, choices=SENTIMENT_TYPES, verbose_name='감정 타입')
    sentiment_score = models.FloatField(verbose_name='감정 점수')  # 0.0 ~ 1.0
    keywords = models.JSONField(default=list, verbose_name='감정 키워드')  # 감정을 나타내는 키워드들
    analyzed_at = models.DateTimeField(auto_now_add=True, verbose_name='분석 시간')

    class Meta:
        db_table = 'sentiment_analysis'
        verbose_name = '감정 분석'
        verbose_name_plural = '감정 분석들'
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"{self.message.id} - {self.sentiment_type} ({self.sentiment_score:.2f})"


# 질환 검색 기록 모델
class DiseaseQuery(models.Model):
    """
    사용자가 검색한 질환 정보를 저장하는 모델
    "우울증", "불안장애" 등의 질환명을 추출하여 저장
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='disease_queries', verbose_name='메시지')
    disease_name = models.CharField(max_length=100, verbose_name='질환명')
    searched_at = models.DateTimeField(auto_now_add=True, verbose_name='검색 시간')

    class Meta:
        db_table = 'disease_query'
        verbose_name = '질환 검색'
        verbose_name_plural = '질환 검색들'
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['disease_name', '-searched_at']),
        ]

    def __str__(self):
        return f"{self.disease_name} - {self.searched_at.strftime('%Y-%m-%d %H:%M')}"
