"""
Vector Store Service
--------------------
pgvector를 사용한 Vector DB 검색 서비스
"""

import os
from typing import List, Dict, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from openai import OpenAI
except ImportError:
    psycopg2 = None
    OpenAI = None


class VectorStore:
    """pgvector 기반 Vector DB 검색 클래스"""
    
    def __init__(self):
        self.client = OpenAI() if OpenAI else None
        self.conn = None
        
    def _get_connection(self):
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
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """텍스트를 임베딩 벡터로 변환"""
        if not self.client:
            return None
            
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 실패: {e}")
            return None
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Vector DB에서 유사한 chunk 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            threshold: 최소 유사도 임계값
            
        Returns:
            검색된 chunk 리스트
        """
        # 임베딩 생성
        embedding = self._get_embedding(query)
        if not embedding:
            return []
        
        # DB 연결
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # pgvector 코사인 유사도 검색
                query_sql = """
                    SELECT 
                        chunk_id,
                        content,
                        disease_name,
                        category,
                        content_type,
                        1 - (embedding <=> %s::vector) as score
                    FROM embeddings_openai_large
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                
                cur.execute(
                    query_sql,
                    (embedding, embedding, threshold, embedding, top_k)
                )
                
                rows = cur.fetchall()
                
                # 결과 포맷팅
                results = []
                for row in rows:
                    results.append({
                        "chunk_id": row.get("chunk_id"),
                        "content": row.get("content"),
                        "metadata": {
                            "disease_name": row.get("disease_name"),
                            "category": row.get("category"),
                            "content_type": row.get("content_type")
                        },
                        "score": float(row.get("score", 0))
                    })
                
                return results
                
        except Exception as e:
            print(f"Vector DB 검색 실패: {e}")
            return []
        finally:
            conn.close()


# 싱글톤 인스턴스
_vector_store = None

def get_vector_store() -> VectorStore:
    """VectorStore 싱글톤 인스턴스 반환"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
