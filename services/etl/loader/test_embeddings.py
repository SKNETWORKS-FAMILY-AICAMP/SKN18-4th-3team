"""
임베딩 모델 비교 테스트 스크립트

세 가지 임베딩 모델(KM-BERT, OpenAI Small, OpenAI Large)의
유사도 검색 성능을 비교 테스트합니다.

테스트 방식:
- 사용자 질문을 입력받아 각 모델로 임베딩 생성
- 각 모델별로 가장 유사한 청크 1개 검색 (top-1)
- 결과 비교 및 분석
"""

import os
import psycopg2
from typing import List, Dict, Any, Optional
from init_db import get_db_config, get_project_root
from load_vectordb import EmbeddingGenerator
from dotenv import load_dotenv


class EmbeddingTester:
    """임베딩 모델 테스트 클래스"""

    def __init__(self):
        self.generator = EmbeddingGenerator()
        self.conn = None

        # 환경 변수 로드
        project_root = get_project_root()
        load_dotenv(project_root / '.env')

    def connect_db(self):
        """데이터베이스 연결"""
        config = get_db_config()
        self.conn = psycopg2.connect(**config)
        print("✅ 데이터베이스 연결 성공\n")

    def close_db(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()

    def search_kmbert(self, query: str, top_k: int = 1) -> List[Dict[str, Any]]:
        """KM-BERT 모델로 유사도 검색"""
        if not self.generator.kmbert_model:
            raise RuntimeError("KM-BERT 모델이 로드되지 않았습니다.")

        # 쿼리 임베딩 생성
        query_embedding = self.generator.generate_kmbert_embedding(query)

        # DB 검색
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                chunk_id,
                content,
                disease_name,
                category,
                content_type,
                1 - (embedding <=> %s::vector) as similarity
            FROM embeddings_kmbert
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                'chunk_id': row[0],
                'content': row[1],
                'disease_name': row[2],
                'category': row[3],
                'content_type': row[4],
                'similarity': float(row[5])
            })

        cursor.close()
        return results

    def search_openai_small(self, query: str, top_k: int = 1) -> List[Dict[str, Any]]:
        """OpenAI Small 모델로 유사도 검색"""
        if not self.generator.openai_client:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다.")

        # 쿼리 임베딩 생성
        query_embedding = self.generator.generate_openai_embedding(
            query,
            "text-embedding-3-small"
        )

        # DB 검색
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                chunk_id,
                content,
                disease_name,
                category,
                content_type,
                1 - (embedding <=> %s::vector) as similarity
            FROM embeddings_openai_small
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                'chunk_id': row[0],
                'content': row[1],
                'disease_name': row[2],
                'category': row[3],
                'content_type': row[4],
                'similarity': float(row[5])
            })

        cursor.close()
        return results

    def search_openai_large(self, query: str, top_k: int = 1) -> List[Dict[str, Any]]:
        """OpenAI Large 모델로 유사도 검색"""
        if not self.generator.openai_client:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다.")

        # 쿼리 임베딩 생성
        query_embedding = self.generator.generate_openai_embedding(
            query,
            "text-embedding-3-large"
        )

        # DB 검색
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                chunk_id,
                content,
                disease_name,
                category,
                content_type,
                1 - (embedding <=> %s::vector) as similarity
            FROM embeddings_openai_large
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                'chunk_id': row[0],
                'content': row[1],
                'disease_name': row[2],
                'category': row[3],
                'content_type': row[4],
                'similarity': float(row[5])
            })

        cursor.close()
        return results

    def print_result(self, model_name: str, result: Dict[str, Any]):
        """검색 결과 출력"""
        print(f"\n{'=' * 80}")
        print(f"  🔍 {model_name}")
        print(f"{'=' * 80}")

        if not result:
            print("❌ 검색 결과가 없습니다.")
            return

        print(f"📌 Chunk ID: {result['chunk_id']}")
        print(f"🏥 질병명: {result['disease_name']}")
        print(f"📂 카테고리: {result['category']}")
        print(f"📝 콘텐츠 타입: {result['content_type']}")
        print(f"📊 유사도: {result['similarity']:.4f}")
        print(f"\n💬 내용:")
        print("-" * 80)
        # 내용이 너무 길면 앞부분만 출력
        content = result['content']
        if len(content) > 500:
            print(content[:500] + "...")
        else:
            print(content)
        print("-" * 80)

    def compare_models(self, query: str, top_k: int = 1):
        """세 모델의 검색 결과 비교"""
        print("\n" + "=" * 80)
        print(f"  🔎 질문: {query}")
        print("=" * 80)

        results = {}

        # KM-BERT 검색
        if self.generator.kmbert_model:
            try:
                print("\n⏳ KM-BERT 검색 중...")
                results['kmbert'] = self.search_kmbert(query, top_k)
            except Exception as e:
                print(f"❌ KM-BERT 검색 실패: {e}")
                results['kmbert'] = []
        else:
            print("\n⚠️  KM-BERT 모델을 사용할 수 없습니다.")
            results['kmbert'] = []

        # OpenAI Small 검색
        if self.generator.openai_client:
            try:
                print("\n⏳ OpenAI Small 검색 중...")
                results['openai_small'] = self.search_openai_small(query, top_k)
            except Exception as e:
                print(f"❌ OpenAI Small 검색 실패: {e}")
                results['openai_small'] = []
        else:
            print("\n⚠️  OpenAI Small 모델을 사용할 수 없습니다.")
            results['openai_small'] = []

        # OpenAI Large 검색
        if self.generator.openai_client:
            try:
                print("\n⏳ OpenAI Large 검색 중...")
                results['openai_large'] = self.search_openai_large(query, top_k)
            except Exception as e:
                print(f"❌ OpenAI Large 검색 실패: {e}")
                results['openai_large'] = []
        else:
            print("\n⚠️  OpenAI Large 모델을 사용할 수 없습니다.")
            results['openai_large'] = []

        # 결과 출력
        print("\n" + "=" * 80)
        print("  📊 검색 결과")
        print("=" * 80)

        if results['kmbert']:
            self.print_result("KM-BERT (768차원)", results['kmbert'][0])

        if results['openai_small']:
            self.print_result("OpenAI Small (1536차원)", results['openai_small'][0])

        if results['openai_large']:
            self.print_result("OpenAI Large (3072차원)", results['openai_large'][0])

        # 비교 요약
        print("\n" + "=" * 80)
        print("  📈 비교 요약")
        print("=" * 80)

        if results['kmbert']:
            print(f"KM-BERT:      유사도 {results['kmbert'][0]['similarity']:.4f} | {results['kmbert'][0]['disease_name']}")
        if results['openai_small']:
            print(f"OpenAI Small: 유사도 {results['openai_small'][0]['similarity']:.4f} | {results['openai_small'][0]['disease_name']}")
        if results['openai_large']:
            print(f"OpenAI Large: 유사도 {results['openai_large'][0]['similarity']:.4f} | {results['openai_large'][0]['disease_name']}")

        print("=" * 80)


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("  임베딩 모델 비교 테스트 (Top-1 유사도 검색)")
    print("=" * 80)

    tester = EmbeddingTester()

    # DB 연결
    try:
        tester.connect_db()
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return

    # 모델 로드
    print("📥 모델 로딩 중...\n")

    kmbert_loaded = tester.generator.load_kmbert()
    openai_loaded = tester.generator.load_openai()

    if not kmbert_loaded and not openai_loaded:
        print("\n❌ 사용 가능한 임베딩 모델이 없습니다.")
        tester.close_db()
        return

    # 테스트 질문들
    test_queries = [
        "양극성장애 증상이 뭐야?",
        "우울증 치료 방법은?",
        "조현병의 원인은 무엇인가요?",
        "불안장애는 어떻게 진단하나요?",
        "ADHD 약물 치료가 있나요?"
    ]

    print("\n" + "=" * 80)
    print("  테스트 모드 선택")
    print("=" * 80)
    print("1. 미리 준비된 질문으로 테스트")
    print("2. 직접 질문 입력")
    print("=" * 80)

    mode = input("\n선택 (1-2): ").strip()

    try:
        if mode == '1':
            # 미리 준비된 질문으로 테스트
            for i, query in enumerate(test_queries, 1):
                print(f"\n\n{'#' * 80}")
                print(f"  테스트 {i}/{len(test_queries)}")
                print(f"{'#' * 80}")
                tester.compare_models(query, top_k=1)

                if i < len(test_queries):
                    input("\n계속하려면 Enter를 누르세요...")

        elif mode == '2':
            # 사용자 입력 질문
            while True:
                print("\n" + "=" * 80)
                query = input("질문을 입력하세요 (종료: q): ").strip()

                if query.lower() == 'q':
                    break

                if not query:
                    print("⚠️  질문을 입력해주세요.")
                    continue

                tester.compare_models(query, top_k=1)

        else:
            print("⚠️  잘못된 선택입니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        tester.close_db()
        print("\n✅ 테스트 종료")


if __name__ == '__main__':
    main()
