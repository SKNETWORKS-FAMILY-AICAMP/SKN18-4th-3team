"""
SQL Search Node
---------------

[기능 설명]
- 검증된 chunk의 메타데이터를 사용하여 RDB에서 관련 이미지 추출
- 문서 ID, 페이지 번호 등의 메타데이터로 이미지 조회
- 이미지 URL 반환

[입력 State]
- verified_chunks: list[dict] - 검증된 chunk 리스트
  - metadata: dict - chunk 메타데이터

[출력 State]
- verified_chunks: list[dict] - 검증된 chunk (전달)
- related_images: list[str] - 관련 이미지 경로/URL 리스트
"""
"""
sql_search_node.py
- verified_chunks의 related_chunk_id를 사용하여 PostgreSQL에서 관련 이미지 검색
- image_metadata 테이블에서 이미지 메타데이터 조회
"""

import os
from typing import Dict, Any, List

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None


def _get_db_connection():
    """PostgreSQL 연결"""
    if not psycopg2:
        return None
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            dbname=os.getenv("PG_DB")
        )
        return conn
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return None


def _extract_chunk_ids(state: Dict[str, Any]) -> List[str]:
    """verified_chunks에서 chunk_id 추출"""
    chunk_ids = []
    for chunk in (state.get("verified_chunks") or []):
        if isinstance(chunk, dict):
            chunk_id = chunk.get("chunk_id") or chunk.get("id")
            if chunk_id:
                chunk_ids.append(str(chunk_id))
    return chunk_ids


def _search_images_from_db(conn, chunk_ids: List[str]) -> List[Dict[str, Any]]:
    """PostgreSQL에서 chunk_id와 매칭되는 이미지 검색"""
    if not chunk_ids:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # IN 절을 사용한 쿼리
            placeholders = ','.join(['%s'] * len(chunk_ids))
            query = f"""
                SELECT 
                    image_id,
                    image_url,
                    disease_name,
                    category,
                    image_type,
                    alt_text,
                    caption,
                    table_context,
                    related_chunk_id
                FROM image_metadata
                WHERE related_chunk_id IN ({placeholders})
            """
            cur.execute(query, chunk_ids)
            rows = cur.fetchall()
            
            # RealDictCursor는 dict 형태로 반환
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"이미지 검색 실패: {e}")
        return []


def sql_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      - state['verified_chunks']: List[Dict] (eval에서 검증된 chunk)
    Output:
      - state['related_images']: List[Dict] (관련 이미지 메타데이터)
    """
    if not psycopg2:
        state["related_images"] = []
        state["sql_error"] = "psycopg2 not installed"
        return state
    
    # chunk_id 추출
    chunk_ids = _extract_chunk_ids(state)
    
    if not chunk_ids:
        state["related_images"] = []
        return state
    
    # DB 연결
    conn = _get_db_connection()
    if not conn:
        state["related_images"] = []
        state["sql_error"] = "DB connection failed"
        return state
    
    try:
        # 이미지 검색
        related_images = _search_images_from_db(conn, chunk_ids)
        state["related_images"] = related_images
    finally:
        conn.close()
    
    return state