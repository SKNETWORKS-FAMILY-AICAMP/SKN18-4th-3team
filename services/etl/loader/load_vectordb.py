"""
Vector DB 데이터 로더 (임베딩 생성 + 적재)

FAQ/INFO 청크 데이터를 임베딩 후 PostgreSQL Vector DB에 적재합니다.
- KM-BERT (768차원)
- OpenAI text-embedding-3-small (1536차원)
- OpenAI text-embedding-3-large (3072차원)
"""

import json
import os
import psycopg2
from pathlib import Path
from typing import List, Dict, Any, Literal
from init_db import get_db_config, get_project_root
from dotenv import load_dotenv

# 임베딩 모델 임포트
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    KMBERT_AVAILABLE = True
except ImportError:
    KMBERT_AVAILABLE = False
    print("⚠️  transformers 라이브러리가 설치되지 않았습니다. KM-BERT 임베딩을 사용할 수 없습니다.")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai 라이브러리가 설치되지 않았습니다. OpenAI 임베딩을 사용할 수 없습니다.")


class EmbeddingGenerator:
    """임베딩 생성기"""

    def __init__(self):
        self.kmbert_model = None
        self.kmbert_tokenizer = None
        self.openai_client = None

        # 환경 변수 로드
        project_root = get_project_root()
        load_dotenv(project_root / '.env')

    def load_kmbert(self):
        """KM-BERT 모델 로드"""
        if not KMBERT_AVAILABLE:
            print("❌ KM-BERT를 사용할 수 없습니다.")
            return False

        try:
            print("📥 KM-BERT 모델 로드 중...")
            model_name = "BM-K/KoSimCSE-bert-multitask"
            self.kmbert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.kmbert_model = AutoModel.from_pretrained(model_name)
            self.kmbert_model.eval()
            print("✅ KM-BERT 모델 로드 완료")
            return True
        except Exception as e:
            print(f"❌ KM-BERT 모델 로드 실패: {e}")
            return False

    def load_openai(self):
        """OpenAI 클라이언트 초기화"""
        if not OPENAI_AVAILABLE:
            print("❌ OpenAI를 사용할 수 없습니다.")
            return False

        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                return False

            self.openai_client = OpenAI(api_key=api_key)
            print("✅ OpenAI 클라이언트 초기화 완료")
            return True
        except Exception as e:
            print(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
            return False

    def generate_kmbert_embedding(self, text: str) -> List[float]:
        """KM-BERT 임베딩 생성 (768차원)"""
        if not self.kmbert_model or not self.kmbert_tokenizer:
            raise RuntimeError("KM-BERT 모델이 로드되지 않았습니다.")

        with torch.no_grad():
            inputs = self.kmbert_tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            outputs = self.kmbert_model(**inputs)
            # [CLS] 토큰의 임베딩 사용
            embedding = outputs.last_hidden_state[:, 0, :].squeeze().tolist()

        return embedding

    def generate_openai_embedding(
        self,
        text: str,
        model: Literal["text-embedding-3-small", "text-embedding-3-large"]
    ) -> List[float]:
        """OpenAI 임베딩 생성"""
        if not self.openai_client:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다.")

        response = self.openai_client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding


def load_chunk_data(data_files: List[Path]) -> List[Dict[str, Any]]:
    """청크 데이터 JSON 파일들 로드"""
    all_chunks = []

    for data_file in data_files:
        print(f"\n📂 청크 데이터 로드 중: {data_file}")

        if not data_file.exists():
            print(f"⚠️  파일을 찾을 수 없습니다: {data_file}")
            continue

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ {len(data)}개의 청크를 로드했습니다.")
        all_chunks.extend(data)

    print(f"\n📊 총 {len(all_chunks)}개의 청크를 로드했습니다.")
    return all_chunks


def extract_metadata(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """청크에서 메타데이터 추출"""
    metadata = chunk.get('metadata', {})

    return {
        'chunk_id': chunk.get('id') or metadata.get('chunk_id'),
        'content': chunk.get('content', ''),
        'disease_name': metadata.get('disease_name', 'Unknown'),
        'category': metadata.get('category', 'Unknown'),
        'has_visual': metadata.get('has_visual', False),
        'content_type': metadata.get('content_type', 'text')
    }


def insert_embeddings(
    conn,
    table_name: str,
    chunks_with_embeddings: List[Dict[str, Any]]
) -> int:
    """임베딩 데이터를 DB에 삽입"""
    cursor = conn.cursor()

    insert_sql = f"""
    INSERT INTO {table_name} (
        chunk_id, content, embedding,
        disease_name, category, has_visual, content_type
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (chunk_id) DO UPDATE SET
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding,
        disease_name = EXCLUDED.disease_name,
        category = EXCLUDED.category,
        has_visual = EXCLUDED.has_visual,
        content_type = EXCLUDED.content_type;
    """

    inserted_count = 0

    for chunk in chunks_with_embeddings:
        try:
            cursor.execute(insert_sql, (
                chunk['chunk_id'],
                chunk['content'],
                chunk['embedding'],
                chunk['disease_name'],
                chunk['category'],
                chunk['has_visual'],
                chunk['content_type']
            ))
            inserted_count += 1

        except Exception as e:
            print(f"⚠️  임베딩 삽입 실패 (chunk_id: {chunk.get('chunk_id')}): {e}")
            continue

    conn.commit()
    cursor.close()

    return inserted_count


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("     Vector DB 데이터 로더")
    print("=" * 60)

    # 프로젝트 루트 경로
    project_root = get_project_root()
    data_files = [
        project_root / 'data' / 'vector_db' / 'faq_chunks.json',
        project_root / 'data' / 'vector_db' / 'info_chunks.json'
    ]

    # 청크 데이터 로드
    chunks = load_chunk_data(data_files)

    if not chunks:
        print("\n❌ 적재할 데이터가 없습니다.")
        return

    # 사용자에게 임베딩 모델 선택
    print("\n" + "=" * 60)
    print("임베딩 모델을 선택하세요:")
    print("  1. KM-BERT (768차원)")
    print("  2. OpenAI text-embedding-3-small (1536차원)")
    print("  3. OpenAI text-embedding-3-large (3072차원)")
    print("  4. 모두 생성")
    print("=" * 60)

    choice = input("선택 (1-4): ").strip()

    # 임베딩 생성기 초기화
    generator = EmbeddingGenerator()

    # DB 연결
    print("\n📡 데이터베이스 연결 중...")
    config = get_db_config()

    try:
        conn = psycopg2.connect(**config)
        print("✅ 데이터베이스 연결 성공")

        # 선택에 따라 임베딩 생성 및 적재
        if choice in ['1', '4']:
            # KM-BERT
            if generator.load_kmbert():
                print("\n" + "=" * 60)
                print("🔄 KM-BERT 임베딩 생성 및 적재 중...")
                print("=" * 60)

                chunks_with_embeddings = []
                for i, chunk in enumerate(chunks, 1):
                    metadata = extract_metadata(chunk)
                    try:
                        embedding = generator.generate_kmbert_embedding(metadata['content'])
                        metadata['embedding'] = embedding
                        chunks_with_embeddings.append(metadata)

                        if i % 100 == 0:
                            print(f"  진행 중: {i}/{len(chunks)} 청크 처리됨")

                    except Exception as e:
                        print(f"⚠️  임베딩 생성 실패 (chunk_id: {metadata['chunk_id']}): {e}")
                        continue

                inserted = insert_embeddings(conn, 'embeddings_kmbert', chunks_with_embeddings)
                print(f"✅ KM-BERT: {inserted}개의 임베딩 삽입 완료")

        if choice in ['2', '4']:
            # OpenAI Small
            if generator.load_openai():
                print("\n" + "=" * 60)
                print("🔄 OpenAI Small 임베딩 생성 및 적재 중...")
                print("=" * 60)

                chunks_with_embeddings = []
                for i, chunk in enumerate(chunks, 1):
                    metadata = extract_metadata(chunk)
                    try:
                        embedding = generator.generate_openai_embedding(
                            metadata['content'],
                            "text-embedding-3-small"
                        )
                        metadata['embedding'] = embedding
                        chunks_with_embeddings.append(metadata)

                        if i % 100 == 0:
                            print(f"  진행 중: {i}/{len(chunks)} 청크 처리됨")

                    except Exception as e:
                        print(f"⚠️  임베딩 생성 실패 (chunk_id: {metadata['chunk_id']}): {e}")
                        continue

                inserted = insert_embeddings(conn, 'embeddings_openai_small', chunks_with_embeddings)
                print(f"✅ OpenAI Small: {inserted}개의 임베딩 삽입 완료")

        if choice in ['3', '4']:
            # OpenAI Large
            if generator.load_openai():
                print("\n" + "=" * 60)
                print("🔄 OpenAI Large 임베딩 생성 및 적재 중...")
                print("=" * 60)

                chunks_with_embeddings = []
                for i, chunk in enumerate(chunks, 1):
                    metadata = extract_metadata(chunk)
                    try:
                        embedding = generator.generate_openai_embedding(
                            metadata['content'],
                            "text-embedding-3-large"
                        )
                        metadata['embedding'] = embedding
                        chunks_with_embeddings.append(metadata)

                        if i % 100 == 0:
                            print(f"  진행 중: {i}/{len(chunks)} 청크 처리됨")

                    except Exception as e:
                        print(f"⚠️  임베딩 생성 실패 (chunk_id: {metadata['chunk_id']}): {e}")
                        continue

                inserted = insert_embeddings(conn, 'embeddings_openai_large', chunks_with_embeddings)
                print(f"✅ OpenAI Large: {inserted}개의 임베딩 삽입 완료")

        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print("=" * 60)

        conn.close()

    except psycopg2.Error as e:
        print(f"\n❌ 데이터베이스 오류: {e}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == '__main__':
    main()
