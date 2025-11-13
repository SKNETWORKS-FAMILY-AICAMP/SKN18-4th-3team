"""
Vector DB 데이터 로더 (임베딩 생성 + 적재)

FAQ/INFO 청크 데이터를 임베딩 후 PostgreSQL Vector DB에 적재합니다.
- OpenAI text-embedding-3-large (3072차원)
"""

import json
import os
import psycopg2
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from init_db import get_db_config, get_project_root

# OpenAI 임포트
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai 라이브러리가 설치되지 않았습니다. OpenAI 임베딩을 사용할 수 없습니다.")


class EmbeddingGenerator:
    """임베딩 생성기 (OpenAI Large 전용)"""

    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                print("⚠️  OPENAI_API_KEY가 설정되지 않았습니다.")

    def generate_embedding(self, text: str) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환 (OpenAI Large)
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            3072차원 임베딩 벡터
        """
        if not self.openai_client:
            raise ValueError("OpenAI 클라이언트가 초기화되지 않았습니다.")
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ 임베딩 생성 실패: {e}")
            raise


def load_chunks_from_json(file_path: Path) -> List[Dict[str, Any]]:
    """JSON 파일에서 청크 데이터 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def insert_embeddings_to_db(chunks: List[Dict[str, Any]], embedding_generator: EmbeddingGenerator):
    """
    청크 데이터를 임베딩하여 Vector DB에 적재
    
    Args:
        chunks: 청크 데이터 리스트
        embedding_generator: 임베딩 생성기
    """
    config = get_db_config()
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    
    try:
        total = len(chunks)
        print(f"\n📊 총 {total}개 청크 처리 시작...")
        
        for idx, chunk in enumerate(chunks, 1):
            chunk_id = chunk['chunk_id']
            content = chunk['content']
            disease_name = chunk.get('disease_name', '')
            category = chunk.get('category', '')
            has_visual = chunk.get('has_visual', False)
            content_type = chunk.get('content_type', '')
            
            # 임베딩 생성
            try:
                embedding = embedding_generator.generate_embedding(content)
            except Exception as e:
                print(f"⚠️  [{idx}/{total}] chunk_id={chunk_id} 임베딩 실패: {e}")
                continue
            
            # DB 삽입
            try:
                cur.execute("""
                    INSERT INTO embeddings_openai_large 
                    (chunk_id, content, embedding, disease_name, category, has_visual, content_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        disease_name = EXCLUDED.disease_name,
                        category = EXCLUDED.category,
                        has_visual = EXCLUDED.has_visual,
                        content_type = EXCLUDED.content_type,
                        created_at = CURRENT_TIMESTAMP
                """, (chunk_id, content, embedding, disease_name, category, has_visual, content_type))
                
                if idx % 10 == 0:
                    print(f"✓ [{idx}/{total}] 처리 완료")
                    conn.commit()
                    
            except Exception as e:
                print(f"❌ [{idx}/{total}] chunk_id={chunk_id} DB 삽입 실패: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        print(f"\n✅ 총 {total}개 청크 처리 완료!")
        
    finally:
        cur.close()
        conn.close()


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Vector DB 데이터 로더 (OpenAI Large)")
    print("=" * 60)
    
    # 프로젝트 루트 확인
    project_root = get_project_root()
    vector_db_dir = project_root / "data" / "vector_db"
    
    if not vector_db_dir.exists():
        print(f"❌ Vector DB 디렉토리가 없습니다: {vector_db_dir}")
        return
    
    # 임베딩 생성기 초기화
    embedding_generator = EmbeddingGenerator()
    if not embedding_generator.openai_client:
        print("❌ OpenAI 클라이언트 초기화 실패")
        return
    
    # FAQ 청크 처리
    faq_file = vector_db_dir / "faq_chunks.json"
    if faq_file.exists():
        print(f"\n📁 FAQ 청크 로드 중: {faq_file}")
        faq_chunks = load_chunks_from_json(faq_file)
        insert_embeddings_to_db(faq_chunks, embedding_generator)
    else:
        print(f"⚠️  FAQ 청크 파일 없음: {faq_file}")
    
    # INFO 청크 처리
    info_file = vector_db_dir / "info_chunks.json"
    if info_file.exists():
        print(f"\n📁 INFO 청크 로드 중: {info_file}")
        info_chunks = load_chunks_from_json(info_file)
        insert_embeddings_to_db(info_chunks, embedding_generator)
    else:
        print(f"⚠️  INFO 청크 파일 없음: {info_file}")
    
    print("\n" + "=" * 60)
    print("Vector DB 적재 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
