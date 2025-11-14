from django.contrib.auth import login, logout, authenticate
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSignupSerializer, UserLoginSerializer, EmailCheckSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """
    회원가입 API (3단계 프로세스)
    1단계: username, profile_image (선택)
    2단계: email, password, password_confirm
    3단계: 회원가입 완료

    요청 데이터:
    {
        "username": "사용자명",  # 중복 가능
        "email": "user@example.com",  # 필수, 중복 불가
        "password": "비밀번호",
        "password_confirm": "비밀번호 확인",
        "profile_image": 파일 (선택)
    }
    """
    if request.user.is_authenticated:
        return Response(
            {'error': '이미 로그인된 사용자입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Serializer를 통한 검증
    serializer = UserSignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 회원가입 처리
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            # 프로필 이미지가 있으면 저장
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
                user.save()

            # 자동 로그인
            login(request, user)

            return Response(
                {
                    'message': '회원가입이 완료되었습니다.',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'profile_image': user.profile_image.url if user.profile_image else None
                    }
                },
                status=status.HTTP_201_CREATED
            )
    except Exception as e:
        return Response(
            {'error': f'회원가입 처리 중 오류가 발생했습니다: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_view(request):
    """
    이메일 중복 확인 API (실시간 검증)
    회원가입 시 이메일 입력 중 실시간으로 중복을 체크

    요청 데이터:
    {
        "email": "user@example.com"
    }

    응답:
    {
        "available": true/false,
        "message": "사용 가능한 이메일입니다." / "이미 사용 중인 이메일입니다."
    }
    """
    serializer = EmailCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']

    # 이메일 중복 확인
    if User.objects.filter(email=email).exists():
        return Response(
            {
                'available': False,
                'message': '이미 사용 중인 이메일입니다.'
            },
            status=status.HTTP_200_OK
        )

    return Response(
        {
            'available': True,
            'message': '사용 가능한 이메일입니다.'
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    로그인 API (이메일 기반 인증)

    요청 데이터:
    {
        "email": "user@example.com",
        "password": "비밀번호"
    }

    응답:
    {
        "message": "로그인 성공",
        "user": {
            "id": 1,
            "username": "사용자명",
            "email": "user@example.com",
            "profile_image": "url"
        }
    }
    """
    if request.user.is_authenticated:
        return Response(
            {'error': '이미 로그인된 사용자입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    # 이메일로 사용자 인증 (USERNAME_FIELD='email')
    user = authenticate(request, username=email, password=password)

    if user is not None:
        login(request, user)
        return Response(
            {
                'message': '로그인 성공',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'profile_image': user.profile_image.url if user.profile_image else None
                }
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {'error': '이메일 또는 비밀번호가 올바르지 않습니다.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # CSRF 문제 해결을 위해 AllowAny로 변경
def logout_view(request):
    """
    로그아웃 API

    응답:
    {
        "message": "로그아웃되었습니다."
    }
    """
    logout(request)
    return Response(
        {'message': '로그아웃되었습니다.'},
        status=status.HTTP_200_OK
    )
