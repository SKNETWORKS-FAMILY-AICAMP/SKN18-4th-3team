"""
PostgreSQL 데이터베이스 초기화 스크립트

pgvector 확장 및 테이블 스키마를 생성합니다.

데이터 파일 경로:
    - data/rdb/image_metadata.json: 이미지 메타데이터 (RDB용)
    - data/vector_db/faq_chunks.json: FAQ 청크 데이터 (Vector DB용)
    - data/vector_db/info_chunks.json: 질병 정보 청크 데이터 (Vector DB용)

사용 예시:
    python init_db.py
    python init_db.py --reset  # 기존 테이블 삭제 후 재생성
"""

import os
import argparse
from pathlib import Path
from functools import lru_cache
import psycopg2
from dotenv import load_dotenv


def get_project_root():
    """프로젝트 루트 경로 반환 (rag 폴더)"""
    # 현재 파일: rag/services/etl/loader/init_db.py
    # parents[0]: loader/, parents[1]: etl/, parents[2]: services/, parents[3]: rag/
    return Path(__file__).resolve().parents[3]


# 데이터 파일 경로 상수
PROJECT_ROOT = get_project_root()
DATA_RDB_DIR = PROJECT_ROOT / 'data' / 'rdb'
DATA_VECTOR_DB_DIR = PROJECT_ROOT / 'data' / 'vector_db'

IMAGE_METADATA_FILE = DATA_RDB_DIR / 'image_metadata.json'
FAQ_CHUNKS_FILE = DATA_VECTOR_DB_DIR / 'faq_chunks.json'
INFO_CHUNKS_FILE = DATA_VECTOR_DB_DIR / 'info_chunks.json'


@lru_cache(maxsize=1)
def get_db_config():
    """환경 변수에서 DB 설정 가져오기"""
    # 프로젝트 루트 찾기 (.git 기준)
    project_root = get_project_root()

    # .env 파일 로드 (절대 경로로 명시)
    env_path = project_root / '.env'
    load_dotenv()

    return {
        'dbname': os.environ.get('PG_DB'),
        'user': os.environ.get('PG_USER'),
        'password': os.environ.get('PG_PASSWORD'),
        'host': os.environ.get('PG_HOST'),
        'port': os.environ.get('PG_PORT')
    }


def test_connection():
    """데이터베이스 연결 테스트"""
    config = get_db_config()

    print("=" * 60)
    print("     데이터베이스 연결 테스트")
    print("=" * 60)
    print(f"호스트: {config['host']}:{config['port']}")
    print(f"데이터베이스: {config['dbname']}")
    print(f"사용자: {config['user']}")

    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # PostgreSQL 버전 확인
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n✅ 연결 성공!")
        print(f"PostgreSQL 버전: {version.split(',')[0]}")

        # pgvector 확장 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        has_vector = cursor.fetchone()[0]

        if has_vector:
            print("✅ pgvector 확장이 이미 설치되어 있습니다.")
        else:
            print("⚠️  pgvector 확장이 설치되어 있지 않습니다. 스키마 생성 시 자동 설치됩니다.")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\n❌ 연결 실패: {e}")
        return False

# 데이터 중복 적재 방지를 위하여 데이터 적재 전 테이블 삭제
def drop_tables():
    """기존 테이블 삭제"""
    config = get_db_config()

    print("\n" + "=" * 60)
    print("     기존 테이블 삭제")
    print("=" * 60)

    drop_sql = """
    -- 함수 삭제
    DROP FUNCTION IF EXISTS search_openai_large_similarity(vector, float, int) CASCADE;

    -- 테이블 삭제
    DROP TABLE IF EXISTS image_metadata CASCADE;
    DROP TABLE IF EXISTS embeddings_openai_large CASCADE;
    """

    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        cursor.execute(drop_sql)
        conn.commit()

        print("✅ 기존 테이블 삭제 완료")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌ 테이블 삭제 실패: {e}")
        raise


def create_schema():
    """스키마 파일 실행"""
    config = get_db_config()
    schema_file = Path(__file__).parent / 'schemas.sql'

    print("\n" + "=" * 60)
    print("     스키마 생성")
    print("=" * 60)
    print(f"스키마 파일: {schema_file}")

    if not schema_file.exists():
        print(f"❌ 스키마 파일을 찾을 수 없습니다: {schema_file}")
        return False

    # SQL 파일 읽기
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # SQL 실행
        cursor.execute(schema_sql)
        conn.commit()

        print("\n✅ 스키마 생성 완료!")

        # 생성된 테이블 확인
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN (
                'image_metadata',
                'embeddings_openai_large'
            )
            ORDER BY tablename;
        """)

        tables = cursor.fetchall()

        if tables:
            print("\n생성된 테이블:")
            for table in tables:
                print(f"  ✓ {table[0]}")
        else:
            print("⚠️  테이블이 생성되지 않았습니다.")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\n❌ 스키마 생성 실패: {e}")
        return False


def show_table_info():
    """테이블 정보 출력"""
    config = get_db_config()

    print("\n" + "=" * 60)
    print("📊 테이블 정보")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()

        # 각 테이블의 컬럼 정보
        tables = [
            'image_metadata',
            'embeddings_openai_large',
        ]

        for table in tables:
            cursor.execute(f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()

            if columns:
                print(f"\n[{table}]")
                for col_name, col_type, col_length in columns:
                    type_str = f"{col_type}"
                    if col_length:
                        type_str += f"({col_length})"
                    print(f"  - {col_name}: {type_str}")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌ 테이블 정보 조회 실패: {e}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='PostgreSQL 데이터베이스 초기화',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
환경 변수 (.env 파일에 설정):
  PG_DB        데이터베이스 이름
  PG_USER      사용자 이름
  PG_PASSWORD  비밀번호
  PG_HOST      호스트
  PG_PORT      포트

사용 예시:
  # 기본 실행
  python init_db.py

  # 기존 테이블 삭제 후 재생성
  python init_db.py --reset

  # 테이블 정보만 확인
  python init_db.py --info
        """
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='기존 테이블 삭제 후 재생성'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='테이블 정보만 출력 (생성하지 않음)'
    )

    args = parser.parse_args()

    # 연결 테스트
    if not test_connection():
        print("\n❌ 데이터베이스 연결에 실패했습니다. 설정을 확인해주세요.")
        return

    # 정보만 출력
    if args.info:
        show_table_info()
        return

    # 테이블 삭제 (reset 옵션)
    if args.reset:
        confirm = input("\n⚠️  기존 데이터가 모두 삭제됩니다. 계속하시겠습니까? (Yes/no): ")
        if confirm.lower() not in ['y', 'yes']:
            print("취소되었습니다.")
            return
        drop_tables()

    # 스키마 생성
    if create_schema():
        show_table_info()

        print("\n" + "=" * 60)
        print("✅ 데이터베이스 초기화 완료!")
        print("=" * 60)
    else:
        print("\n❌ 데이터베이스 초기화 실패")


if __name__ == '__main__':
    main()
