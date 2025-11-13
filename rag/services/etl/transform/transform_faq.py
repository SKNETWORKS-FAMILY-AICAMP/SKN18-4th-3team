"""
FAQ 데이터 Transform: 질문-응답 쌍을 청킹하여 Vector DB 준비

핵심 원칙:
1. 질문-응답 쌍의 의미 유지 (질문과 응답 분리 금지)
2. LangChain RecursiveCharacterTextSplitter 사용
3. 긴 응답은 청킹하되 각 청크에 질문 포함
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ==============================
# 데이터 구조
# ==============================

@dataclass
class FAQChunk:
    """FAQ Vector 청크"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata
        }


# ==============================
# FAQ Splitter (LangChain 기반)
# ==============================

class FAQTextSplitter:
    """
    LangChain RecursiveCharacterTextSplitter를 사용하여 FAQ 청킹

    특징:
    - 질문-응답 쌍의 의미 유지
    - 응답이 긴 경우에만 분할
    - 각 청크에 질문을 포함하여 검색 가능성 향상
    """

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Args:
            chunk_size: 청크당 최대 문자 수
            chunk_overlap: 청크 간 중복 문자 수 (문맥 유지)
            separators: 분할 우선순위 구분자
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # FAQ에 적합한 구분자 우선순위
        if separators is None:
            separators = [
                "\n\n",      # 문단 구분 (최우선)
                "\n",        # 줄바꿈
                ". ",        # 문장 구분
                "! ",
                "? ",
                "• ",        # 불릿 포인트
                "♦ ",        # 특수 불릿
                " ",         # 공백 (최후)
                ""           # 문자 단위 (최후의 최후)
            ]

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )

    def split_faq(
        self,
        question: str,
        answer: str,
        keyword: str,
        faq_index: int
    ) -> List[FAQChunk]:
        """
        단일 FAQ를 청킹

        전략:
        1. 질문 + 응답을 하나의 문서로 생성
        2. 크기가 작으면 단일 청크
        3. 크기가 크면 LangChain Splitter로 분할
        4. 분할된 각 청크에 질문 추가 (검색 시 질문으로 매칭 가능)
        """
        # 전체 컨텐츠 생성
        full_content = f"[질문]\n{question}\n\n[응답]\n{answer}"

        # 단일 청크로 가능한지 확인
        if len(full_content) <= self.chunk_size:
            return [self._create_chunk(
                content=full_content,
                question=question,
                answer=answer,
                keyword=keyword,
                faq_index=faq_index,
                chunk_index=0,
                total_chunks=1,
                is_complete=True
            )]

        # LangChain Splitter로 응답 분할
        answer_chunks = self._split_long_answer(answer)

        # 각 청크에 질문 추가
        faq_chunks = []
        for idx, answer_chunk in enumerate(answer_chunks):
            chunk_content = f"[질문]\n{question}\n\n[응답]\n{answer_chunk}"

            faq_chunk = self._create_chunk(
                content=chunk_content,
                question=question,
                answer=answer_chunk,
                keyword=keyword,
                faq_index=faq_index,
                chunk_index=idx,
                total_chunks=len(answer_chunks),
                is_complete=(len(answer_chunks) == 1)
            )
            faq_chunks.append(faq_chunk)

        return faq_chunks

    def _split_long_answer(self, answer: str) -> List[str]:
        """
        LangChain TextSplitter를 사용하여 긴 응답 분할

        Returns:
            분할된 응답 텍스트 리스트
        """
        # LangChain Document 생성
        doc = Document(page_content=answer)

        # 분할
        split_docs = self.text_splitter.split_documents([doc])

        # 텍스트만 추출
        return [doc.page_content for doc in split_docs]

    def _create_chunk(
        self,
        content: str,
        question: str,
        answer: str,
        keyword: str,
        faq_index: int,
        chunk_index: int,
        total_chunks: int,
        is_complete: bool
    ) -> FAQChunk:
        """FAQ 청크 생성"""
        chunk_id = self._generate_chunk_id(question, faq_index, chunk_index)

        metadata = {
            "chunk_id": chunk_id,
            "keyword": keyword,
            "disease_name": keyword,
            "category": "FAQ",
            "content_type": "faq"
        }

        return FAQChunk(
            chunk_id=chunk_id,
            content=content,
            metadata=metadata
        )

    @staticmethod
    def _generate_chunk_id(question: str, faq_index: int, chunk_index: int) -> str:
        """청크 ID 생성"""
        hash_input = f"{question}_{faq_index}_{chunk_index}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"faq_{hash_digest}"


# ==============================
# Transform 메인
# ==============================

class FAQTransformer:
    """FAQ 데이터를 Vector DB 형식으로 변환"""

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200
    ):
        """
        Args:
            chunk_size: 청크당 최대 문자 수
            chunk_overlap: 청크 간 중복 문자 수
        """
        self.splitter = FAQTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def transform(self, faq_data: List[Dict[str, Any]]) -> List[FAQChunk]:
        """FAQ 데이터 전체 변환"""
        all_chunks = []

        for faq_index, faq_item in enumerate(faq_data):
            question = faq_item.get("question", "")
            answer = faq_item.get("answer", "")
            keyword = faq_item.get("keyword", "기타")

            if not question or not answer:
                print(f"⚠️  FAQ {faq_index}: 질문 또는 응답이 비어있습니다. 건너뜁니다.")
                continue

            # FAQ 청킹
            chunks = self.splitter.split_faq(
                question=question,
                answer=answer,
                keyword=keyword,
                faq_index=faq_index
            )

            all_chunks.extend(chunks)

        return all_chunks

    def get_statistics(self, chunks: List[FAQChunk]) -> Dict[str, Any]:
        """청킹 통계"""
        keyword_dist = {}
        size_dist = {"< 500": 0, "500-1000": 0, "1000-1500": 0, "> 1500": 0}

        for chunk in chunks:
            keyword = chunk.metadata.get("keyword", "기타")
            keyword_dist[keyword] = keyword_dist.get(keyword, 0) + 1

            size = len(chunk.content)
            if size < 500:
                size_dist["< 500"] += 1
            elif size < 1000:
                size_dist["500-1000"] += 1
            elif size < 1500:
                size_dist["1000-1500"] += 1
            else:
                size_dist["> 1500"] += 1

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0,
            "keyword_distribution": keyword_dist,
            "chunk_size_distribution": size_dist
        }


# ==============================
# 메인 실행
# ==============================

def main(chunk_size: int = 1500, chunk_overlap: int = 200):
    """FAQ Transform 실행"""
    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / 'rag' / 'data' / 'raw' / 'diseases_faq.json'
    output_file = project_root / 'rag' / 'data' / 'vector_db' / 'faq_chunks.json'

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    print(f"📂 입력 파일: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        faq_data = json.load(f)

    print(f"📝 FAQ 데이터: {len(faq_data)}개")
    print(f"⚙️  청킹 설정:")
    print(f"   - Chunk Size: {chunk_size}자")
    print(f"   - Chunk Overlap: {chunk_overlap}자")
    print(f"   - Splitter: LangChain RecursiveCharacterTextSplitter\n")

    # Transform
    transformer = FAQTransformer(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = transformer.transform(faq_data)

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([chunk.to_dict() for chunk in chunks], f, ensure_ascii=False, indent=2)

    print(f"✅ Transform 완료!")
    print(f"   출력: {output_file}\n")

    # 통계
    stats = transformer.get_statistics(chunks)
    print(f"📊 통계:")
    print(f"   - 생성된 청크: {stats['total_chunks']}개")
    print(f"   - 평균 청크 크기: {stats['avg_chunk_size']:.0f}자")

    print(f"\n   [키워드별 청크 분포]")
    for keyword, count in sorted(stats['keyword_distribution'].items()):
        print(f"   - {keyword}: {count}개")

    print(f"\n   [청크 크기 분포]")
    for size_range, count in stats['chunk_size_distribution'].items():
        print(f"   - {size_range}자: {count}개")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='FAQ 데이터 Transform (LangChain Splitter 사용)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1500,
        help='청크당 최대 문자 수 (기본값: 1500)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='청크 간 중복 문자 수 (기본값: 200)'
    )

    args = parser.parse_args()

    main(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
