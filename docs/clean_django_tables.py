"""
Django 관련 테이블 정리 스크립트

모든 Django 관련 테이블을 CASCADE로 삭제합니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent

# .env 파일 로드
load_dotenv(BASE_DIR / '.env')

def get_db_config():
    """데이터베이스 설정 가져오기"""
    return {
        'dbname': os.environ['PG_DB'],
        'user': os.environ['PG_USER'],
        'password': os.environ['PG_PASSWORD'],
        'host': 'localhost',
        'port': os.environ.get('PG_PORT', '5432')
    }

def clean_django_tables():
    """모든 Django 관련 테이블 삭제"""
    config = get_db_config()
    
    print("=" * 60)
    print("     Django 테이블 정리")
    print("=" * 60)
    
    # Django 기본 테이블 목록
    django_tables = [
        'django_migrations',
        'django_admin_log',
        'django_content_type',
        'django_session',
        'auth_permission',
        'auth_group_permissions',
        'auth_user_user_permissions',
        'auth_user_groups',
        'auth_group',
        'auth_user',
        'users',  # 커스텀 User 모델
        'conversations',  # chatbot 앱
        'messages',  # chatbot 앱
    ]
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        print("\n📋 Django 테이블 삭제 중...")
        
        for table in django_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"  ✓ {table}")
            except psycopg2.Error as e:
                print(f"  ⚠️  {table}: {e}")
        
        conn.commit()
        
        print("\n✅ Django 테이블 정리 완료!")
        print("\n이제 다음 명령어를 실행하세요:")
        print("  python manage.py migrate")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ 오류 발생: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    confirm = input("\n⚠️  모든 Django 테이블이 삭제됩니다. 계속하시겠습니까? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("취소되었습니다.")
        sys.exit(0)
    
    if clean_django_tables():
        print("\n" + "=" * 60)
        print("✅ 정리 완료!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 정리 실패")
        print("=" * 60)
        sys.exit(1)

