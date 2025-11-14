from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class ProfileUpdateSerializer(serializers.Serializer):
    """프로필 업데이트 Serializer"""
    username = serializers.CharField(max_length=150, required=True)


class ChangePasswordSerializer(serializers.Serializer):
    """비밀번호 변경 Serializer"""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """비밀번호 일치 확인 및 유효성 검사"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError({'new_password_confirm': '새 비밀번호가 일치하지 않습니다.'})

        # Django 비밀번호 유효성 검사
        try:
            validate_password(new_password, self.context['user'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})

        return attrs

