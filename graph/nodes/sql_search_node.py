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
- eval에서 검증된 키워드/엔티티를 기반으로 RDB(PostgreSQL) 추가 검색
- 결과는 state['verified_chunks']에 보강(merge) 또는 state['sql_results']에 별도 저장
- DB 환경변수:
  - DATABASE_URL (예: postgresql+psycopg://user:pass@host:port/db)
  또는
  - PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
"""

import os
from typing import Dict, Any, List

# psycopg (3.x)
try:
    import psycopg
except Exception:
    psycopg = None  # 설치 안 되어도 소프트 실패

TABLE = os.getenv("SQL_CHUNK_TABLE", "kb_chunks")  # 예: 텍스트 테이블명
TEXT_COL = os.getenv("SQL_TEXT_COL", "content")
META_COL = os.getenv("SQL_META_COL", "metadata")

def _connect():
    # DATABASE_URL 우선
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg.connect(dsn) if psycopg else None
    # 개별 변수
    if psycopg:
        return psycopg.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            dbname=os.getenv("PGDATABASE"),
        )
    return None

def _extract_keywords(state: Dict[str, Any]) -> List[str]:
    """
    verified_chunks에서 핵심 키워드 후보 추출.
    프로젝트 상황에 맞게 개선하세요.
    """
    kws = []
    for ch in (state.get("verified_chunks") or []):
        # 예: chunk에 'keywords' 리스트나 'title'/'summary' 존재한다고 가정
        if isinstance(ch, dict):
            if "keywords" in ch and isinstance(ch["keywords"], list):
                kws.extend([str(k) for k in ch["keywords"] if k])
            if "title" in ch:
                kws.append(str(ch["title"]))
    # 중복 제거/정리
    seen, uniq = set(), []
    for k in kws:
        kk = k.strip()
        if kk and kk.lower() not in seen:
            seen.add(kk.lower())
            uniq.append(kk)
    return uniq[:10]  # 안전하게 제한

def _search_sql(cur, keywords: List[str], limit: int = 8) -> List[Dict[str, Any]]:
    """
    단순 ILIKE OR 매칭(예시).
    실제로는 tsvector/GIN, re-rank, 점수 컬럼 등을 쓰는 게 좋음.
    """
    if not keywords:
        return []
    conditions = " OR ".join([f"{TEXT_COL} ILIKE %s" for _ in keywords])
    sql = f"""
        SELECT {TEXT_COL} AS content, {META_COL} AS metadata
        FROM {TABLE}
        WHERE {conditions}
        LIMIT {limit}
    """
    params = [f"%{k}%" for k in keywords]
    cur.execute(sql, params)
    rows = cur.fetchall()
    results = []
    for r in rows:
        content = r[0]
        meta = r[1] if len(r) > 1 else None
        results.append({"content": content, "metadata": meta})
    return results

def sql_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      - state['verified_chunks']: List[Dict] (eval에서 검증된 근거)
    Output:
      - state['sql_results']: List[Dict] (SQL 보강 결과)
      - (선택) state['verified_chunks']에 append 병합
    """
    keywords = _extract_keywords(state)
    if not psycopg:
        # DB 드라이버 없으면 소프트 실패
        state["sql_results"] = []
        state["sql_error"] = "psycopg not installed"
        return state

    try:
        conn = _connect()
        if conn is None:
            state["sql_results"] = []
            state["sql_error"] = "DB connection failed"
            return state
        with conn, conn.cursor() as cur:
            results = _search_sql(cur, keywords)
    except Exception as e:
        state["sql_results"] = []
        state["sql_error"] = f"sql_search error: {e}"
        return state

    # 보강: verified_chunks 뒤에 붙이거나 별도 키로 전달
    state["sql_results"] = results
    # 선택적으로 병합하려면 아래 주석 해제
    # state["verified_chunks"] = (state.get("verified_chunks") or []) + results
    return state
