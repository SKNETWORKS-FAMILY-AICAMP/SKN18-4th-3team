"""
Django 마이그레이션 히스토리 수정 스크립트 (안전한 방법)

마이그레이션 히스토리 불일치 문제를 해결하기 위해
django_migrations 테이블만 수정합니다.
데이터는 유지됩니다.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# 프로젝트 루트 경로 (docs 폴더의 상위 디렉토리)
BASE_DIR = Path(__file__).resolve().parent.parent

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

def fix_migration_history():
    """마이그레이션 히스토리 수정 (데이터 유지)"""
    config = get_db_config()
    
    print("=" * 60)
    print("     Django 마이그레이션 히스토리 수정")
    print("=" * 60)
    print("⚠️  이 방법은 데이터를 유지하면서 마이그레이션 히스토리만 수정합니다.")
    print()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # 현재 마이그레이션 상태 확인
        print("📋 현재 마이그레이션 상태 확인 중...")
        cursor.execute("""
            SELECT app, name 
            FROM django_migrations 
            WHERE app IN ('admin', 'users', 'chatbot')
            ORDER BY app, name;
        """)
        
        existing = cursor.fetchall()
        if existing:
            print("\n현재 적용된 마이그레이션:")
            for app, name in existing:
                print(f"  - {app}.{name}")
        else:
            print("\n적용된 마이그레이션이 없습니다.")
        
        # 문제가 되는 admin.0001_initial 레코드 삭제
        print("\n🔧 마이그레이션 히스토리 수정 중...")
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'admin' AND name = '0001_initial';
        """)
        
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"  ✓ admin.0001_initial 레코드 삭제됨 ({deleted}개)")
        else:
            print("  ℹ️  admin.0001_initial 레코드가 없습니다.")
        
        conn.commit()
        
        print("\n✅ 마이그레이션 히스토리 수정 완료!")
        print("\n이제 다음 명령어를 실행하세요:")
        print("  1. python manage.py migrate --fake-initial")
        print("  2. python manage.py migrate")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ 오류 발생: {e}")
        return False

if __name__ == '__main__':
    confirm = input("\n⚠️  마이그레이션 히스토리를 수정합니다. 계속하시겠습니까? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("취소되었습니다.")
        sys.exit(0)
    
    if fix_migration_history():
        print("\n" + "=" * 60)
        print("✅ 수정 완료!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 수정 실패")
        print("=" * 60)
        sys.exit(1)

