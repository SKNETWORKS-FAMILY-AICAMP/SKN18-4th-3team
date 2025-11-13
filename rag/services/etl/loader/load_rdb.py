"""
RDB 데이터 로더 (image_metadata)

이미지 메타데이터를 PostgreSQL RDB에 적재합니다.
"""

import json
import psycopg2
from pathlib import Path
from typing import List, Dict, Any
from init_db import get_db_config, get_project_root


def load_image_metadata(data_file: Path) -> List[Dict[str, Any]]:
    """이미지 메타데이터 JSON 파일 로드"""
    print(f"\n📂 이미지 메타데이터 로드 중: {data_file}")

    if not data_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {data_file}")
        return []

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✅ {len(data)}개의 이미지 메타데이터를 로드했습니다.")
    return data


def insert_image_metadata(conn, metadata_list: List[Dict[str, Any]]) -> int:
    """이미지 메타데이터를 DB에 삽입"""
    cursor = conn.cursor()

    insert_sql = """
    INSERT INTO image_metadata (
        image_id, disease_name, category, image_url, image_type,
        alt_text, caption, related_chunk_id, table_context
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (image_id) DO UPDATE SET
        disease_name = EXCLUDED.disease_name,
        category = EXCLUDED.category,
        image_url = EXCLUDED.image_url,
        image_type = EXCLUDED.image_type,
        alt_text = EXCLUDED.alt_text,
        caption = EXCLUDED.caption,
        related_chunk_id = EXCLUDED.related_chunk_id,
        table_context = EXCLUDED.table_context;
    """

    inserted_count = 0

    for metadata in metadata_list:
        try:
            # table_context는 JSONB 타입이므로 json.dumps 필요
            table_context_json = json.dumps(metadata.get('table_context')) if metadata.get('table_context') else None

            cursor.execute(insert_sql, (
                metadata['image_id'],
                metadata['disease_name'],
                metadata['category'],
                metadata['image_url'],
                metadata.get('image_type'),
                metadata.get('alt_text'),
                metadata.get('caption'),
                metadata.get('related_chunk_id'),
                table_context_json
            ))
            inserted_count += 1

        except Exception as e:
            print(f"⚠️  이미지 메타데이터 삽입 실패 (image_id: {metadata.get('image_id')}): {e}")
            continue

    conn.commit()
    cursor.close()

    return inserted_count


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("     RDB 데이터 로더 (image_metadata)")
    print("=" * 60)

    # 프로젝트 루트 경로
    project_root = get_project_root()
    data_file = project_root / 'data' / 'rdb' / 'image_metadata.json'

    # 데이터 로드
    metadata_list = load_image_metadata(data_file)

    if not metadata_list:
        print("\n❌ 적재할 데이터가 없습니다.")
        return

    # DB 연결
    print("\n📡 데이터베이스 연결 중...")
    config = get_db_config()

    try:
        conn = psycopg2.connect(**config)
        print("✅ 데이터베이스 연결 성공")

        # 데이터 삽입
        print("\n💾 이미지 메타데이터 삽입 중...")
        inserted_count = insert_image_metadata(conn, metadata_list)

        print(f"\n✅ {inserted_count}개의 이미지 메타데이터 삽입 완료!")

        # 삽입된 데이터 확인
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM image_metadata;")
        total_count = cursor.fetchone()[0]
        cursor.close()

        print(f"📊 총 {total_count}개의 이미지 메타데이터가 DB에 저장되어 있습니다.")

        conn.close()

    except psycopg2.Error as e:
        print(f"\n❌ 데이터베이스 오류: {e}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == '__main__':
    main()
