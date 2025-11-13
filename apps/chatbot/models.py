from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


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
            models.Index(fields=['-updated_at']),  # 최신 대화 조회 성능 향상
            models.Index(fields=['user', '-updated_at']),  # 사용자별 대화 조회 성능 향상
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
                # "사용자 질문 - 챗봇 응답" 형식으로 제목 생성
                title = f"{user_message.content[:30]} - {instance.content[:30]}"
                conversation.title = title
                conversation.save(update_fields=['title'])
