"""
대화 내용 암호화/복호화 유틸리티
Fernet (symmetric encryption) 사용
"""
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os


def get_encryption_key():
    """
    환경변수에서 암호화 키를 가져오거나 생성
    SECRET_KEY를 기반으로 Fernet 키 생성
    """
    # 환경변수에서 암호화 키 가져오기
    encryption_key = os.getenv('ENCRYPTION_KEY')
    
    if not encryption_key:
        # SECRET_KEY를 기반으로 Fernet 키 생성
        # Fernet은 32바이트 URL-safe base64 인코딩된 키를 요구
        secret_key = settings.SECRET_KEY
        # SECRET_KEY를 해시하여 32바이트 생성
        import hashlib
        key_bytes = hashlib.sha256(secret_key.encode()).digest()
        encryption_key = base64.urlsafe_b64encode(key_bytes).decode()
    else:
        encryption_key = encryption_key
    
    return encryption_key.encode()


def encrypt_content(content: str) -> str:
    """
    대화 내용 암호화
    """
    if not content:
        return content
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(content.encode())
        return encrypted.decode()
    except Exception as e:
        # 암호화 실패 시 원본 반환 (로깅 필요)
        print(f"암호화 실패: {e}")
        return content


def decrypt_content(encrypted_content: str) -> str:
    """
    대화 내용 복호화
    """
    if not encrypted_content:
        return encrypted_content
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_content.encode())
        return decrypted.decode()
    except Exception as e:
        # 복호화 실패 시 원본 반환 (로깅 필요)
        print(f"복호화 실패: {e}")
        return encrypted_content

