from rest_framework import serializers
from .models import User


class UserSignupSerializer(serializers.Serializer):
    """회원가입 Serializer"""
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    def validate_email(self, value):
        """이메일 중복 확인"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('이미 사용 중인 이메일입니다.')
        return value

    def validate(self, attrs):
        """비밀번호 일치 확인 및 유효성 검사"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({'password_confirm': '비밀번호가 일치하지 않습니다.'})

        # 최소 길이만 확인 (8자 이상)
        if len(password) < 8:
            raise serializers.ValidationError({'password': '비밀번호는 최소 8자 이상이어야 합니다.'})

        return attrs


class UserLoginSerializer(serializers.Serializer):
    """로그인 Serializer"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class EmailCheckSerializer(serializers.Serializer):
    """이메일 중복 확인 Serializer"""
    email = serializers.EmailField(required=True)

