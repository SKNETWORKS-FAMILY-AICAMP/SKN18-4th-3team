from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    사용자 모델 - Django의 기본 User 모델을 확장
    """
    email = models.EmailField(unique=True, verbose_name='이메일')
    username = models.CharField(max_length=150, verbose_name='사용자명')
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        verbose_name='프로필 이미지'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='가입일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')

    # 로그인 필드를 email로 변경
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자'

    def __str__(self):
        return self.email


# UserEmotionTag 모델 추후 개발(로그인시 사용자 설정 추가 기능)
