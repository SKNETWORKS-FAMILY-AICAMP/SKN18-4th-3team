from django.db import models
from django.conf import settings


class UserActivityLog(models.Model):
    """
    사용자 활동 로그 - 로그인, 대화 시작/종료 등의 활동 기록 (추후 통계 분석용)
    """
    ACTION_CHOICES = [
        ('login', '로그인'),
        ('logout', '로그아웃'),
        ('conversation_start', '대화 시작'),
        ('conversation_end', '대화 종료'),
        ('profile_update', '프로필 수정'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name='사용자'
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='활동'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP 주소'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='발생일시')

    class Meta:
        db_table = 'user_activity_logs'
        verbose_name = '사용자 활동 로그'
        verbose_name_plural = '사용자 활동 로그'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.created_at}"
