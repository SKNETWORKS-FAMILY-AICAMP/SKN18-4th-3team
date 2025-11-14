from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .encryption import encrypt_content, decrypt_content


class Conversation(models.Model):
    """
    대화 세션 모델 - 사용자와 챗봇 간의 대화 세션
    로그인 사용자만 대화 내용이 저장됨
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name='사용자'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='대화 제목'
    )  # 첫 번째 사용자 메시지 + 챗봇 응답으로 자동 생성
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='시작일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='최종 업데이트')

    class Meta:
        db_table = 'conversations'
        verbose_name = '대화 세션'
        verbose_name_plural = '대화 세션'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['updated_at']),  # 최신 대화 조회 성능 향상
            models.Index(fields=['user', 'updated_at']),  # 사용자별 대화 조회 성능 향상
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Untitled'}"


class Message(models.Model):
    """
    메시지 모델 - 대화 세션 내의 개별 메시지
    """
    ROLE_CHOICES = [
        ('user', '사용자'),
        ('assistant', '챗봇'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='대화 세션'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name='역할'
    )
    content = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    # 랭그래프 관련 필드 - 생각하는 챗봇 표시용
    thinking_process = models.JSONField(
        null=True,
        blank=True,
        verbose_name='사고 과정',
        help_text='랭그래프 노드 진행 과정: [{"node": "classify", "description": "질문 분류 중...", "order": 1}, ...]'
    )

    class Meta:
        db_table = 'messages'
        verbose_name = '메시지'
        verbose_name_plural = '메시지'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),  # 대화별 메시지 조회 성능 향상
        ]

    def __str__(self):
        return f"{self.conversation.id} - {self.role}: {self.content[:30]}"
    
    def get_decrypted_content(self):
        """암호화된 내용을 복호화하여 반환"""
        return decrypt_content(self.content)
    
    def set_encrypted_content(self, plain_text: str):
        """평문을 암호화하여 저장"""
        self.content = encrypt_content(plain_text)


# Signal: 메시지 저장 전 암호화
@receiver(pre_save, sender=Message)
def encrypt_message_content(sender, instance, **kwargs):
    """
    메시지 저장 전 content 필드를 암호화
    이미 암호화된 경우는 그대로 유지 (중복 암호화 방지)
    """
    if not instance.content:
        return
    
    # 새로 생성되는 메시지인지 확인 (pk가 없으면 새 메시지)
    if instance.pk:
        # 기존 메시지 업데이트인 경우, 이미 암호화되어 있을 수 있음
        try:
            # 복호화 시도 - 성공하면 이미 암호화된 것
            decrypted = decrypt_content(instance.content)
            # 복호화 성공 = 이미 암호화됨, 그대로 유지
            return
        except:
            # 복호화 실패 = 평문이거나 다른 형식, 암호화 진행
            pass
    else:
        # 새 메시지인 경우 암호화
        instance.content = encrypt_content(instance.content)


# Signal: 챗봇 응답 시 대화 제목 자동 생성
@receiver(post_save, sender=Message)
def auto_generate_conversation_title(sender, instance, created, **kwargs):
    """
    챗봇의 첫 응답이 생성되면 자동으로 대화 제목 생성
    대화 제목 = "사용자 첫 메시지 + 챗봇 첫 응답"
    """
    if created and instance.role == 'assistant':
        conversation = instance.conversation
        if not conversation.title:  # 제목이 없을 때만
            # 첫 번째 사용자 메시지 가져오기
            user_message = conversation.messages.filter(role='user').first()
            if user_message:
                # "사용자 질문 - 챗봇 응답" 형식으로 제목 생성 (복호화된 내용 사용)
                user_content = user_message.get_decrypted_content()[:30]
                assistant_content = instance.get_decrypted_content()[:30]
                title = f"{user_content} - {assistant_content}"
                conversation.title = title
                conversation.save(update_fields=['title'])


# 챗 검색 기능.



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

    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='sentiment',
        verbose_name='메시지'
    )
    sentiment_type = models.CharField(
        max_length=20,
        choices=SENTIMENT_TYPES,
        verbose_name='감정 타입'
    )
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


class DiseaseQuery(models.Model):
    """
    사용자가 검색한 질환 정보를 저장하는 모델
    "우울증", "불안장애" 등의 질환명을 추출하여 저장
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='disease_queries',
        verbose_name='메시지'
    )
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
