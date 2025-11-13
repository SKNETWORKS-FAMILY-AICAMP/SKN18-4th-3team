"""
범용 Transform: 테이블 내 이미지를 포함한 데이터를 RAG 친화적으로 변환

하이브리드 구현:
- Vector DB: 텍스트 임베딩 (이미지 alt 텍스트 포함)
- RDB: 이미지 메타데이터 (URL, alt, location 등)

이미지 분석: AI 분석 대신 HTML alt 텍스트 사용
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import hashlib


# ==============================
# 데이터 구조
# ==============================

@dataclass
class ImageMetadata:
    """RDB에 저장될 이미지 메타데이터"""
    image_id: str
    disease_name: str
    category: str  # '개요.정의', '진단.검사' 등

    # 이미지 정보
    image_url: str
    image_type: str  # 'graph', 'table', 'diagram', 'photo'

    # 텍스트 설명 (AI 생성 필요)
    alt_text: str = ""  # AI가 생성한 이미지 설명
    caption: str = ""   # 원본 캡션

    # 관계 정보
    related_chunk_id: str = ""
    table_context: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VectorChunk:
    """Vector DB에 저장될 청크"""
    chunk_id: str
    content: str  # 임베딩할 텍스트 (이미지 설명 포함)
    metadata: Dict[str, Any]  # 모든 메타데이터

    def to_dict(self) -> Dict[str, Any]:
        """
        Vector DB 저장 형식으로 변환

        대부분의 Vector DB는 다음 구조를 사용:
        {
            "id": "chunk_xxx",
            "content": "텍스트...",
            "metadata": {...}
        }
        """
        return {
            "id": self.chunk_id,  # Vector DB의 Primary Key
            "content": self.content,
            "metadata": self.metadata  # chunk_id, disease_name 등 모두 포함
        }


# ==============================
# 이미지 처리 유틸리티
# ==============================

class ImageExtractor:
    """테이블/텍스트에서 이미지 URL 추출"""

    # 이미지 패턴: [이미지: URL]
    IMAGE_PATTERN = re.compile(r'\[이미지:\s*([^\]]+)\]')

    @classmethod
    def extract_images_from_text(cls, text: str) -> List[Tuple[str, str]]:
        """
        텍스트에서 이미지 URL과 전체 매치 추출

        Returns:
            [(전체 매치 문자열, URL), ...]
        """
        matches = cls.IMAGE_PATTERN.findall(text)
        results = []
        for match in matches:
            url = match.strip()
            full_match = f"[이미지: {match}]"
            results.append((full_match, url))
        return results

    @classmethod
    def has_images(cls, obj: Any) -> bool:
        """객체에 이미지 URL이 포함되어 있는지 확인"""
        if isinstance(obj, str):
            return bool(cls.IMAGE_PATTERN.search(obj))
        elif isinstance(obj, list):
            return any(cls.has_images(item) for item in obj)
        elif isinstance(obj, dict):
            return any(cls.has_images(v) for v in obj.values())
        return False

    @classmethod
    def extract_all_image_urls(cls, obj: Any) -> List[str]:
        """객체에서 모든 이미지 URL 추출 (재귀)"""
        urls = []
        if isinstance(obj, str):
            matches = cls.IMAGE_PATTERN.findall(obj)
            urls.extend([m.strip() for m in matches])
        elif isinstance(obj, list):
            for item in obj:
                urls.extend(cls.extract_all_image_urls(item))
        elif isinstance(obj, dict):
            for v in obj.values():
                urls.extend(cls.extract_all_image_urls(v))
        return urls


class TableImageProcessor:
    """테이블 데이터 및 이미지 처리 (alt 텍스트 기반)"""

    def __init__(self):
        """이미지 메타데이터 처리 (alt 텍스트 사용)"""
        pass

    @staticmethod
    def generate_image_id(disease_name: str, category: str, url: str) -> str:
        """이미지 ID 생성 (중복 방지를 위한 해시)"""
        hash_input = f"{disease_name}_{category}_{url}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"img_{hash_digest}"

    def process_table(
        self,
        table_data: List[List[str]],
        disease_name: str,
        category: str
    ) -> Tuple[str, List[ImageMetadata]]:
        """
        테이블 데이터 처리:
        1. 이미지 URL 추출
        2. 이미지 메타데이터 생성
        3. 텍스트 설명 플레이스홀더 생성

        Returns:
            (텍스트 설명, 이미지 메타데이터 리스트)
        """
        if not table_data:
            return "", []

        image_records = []
        text_parts = []

        # 테이블 첫 행이 헤더인지 확인
        headers = table_data[0] if table_data else []

        # 각 행 처리
        for row_idx, row in enumerate(table_data):
            row_text_parts = []

            for col_idx, cell in enumerate(row):
                if not isinstance(cell, str):
                    continue

                # 셀에서 이미지 추출
                images = ImageExtractor.extract_images_from_text(cell)

                if images:
                    # 이미지가 있는 경우
                    for full_match, url in images:
                        # 이미지 메타데이터 생성
                        image_id = self.generate_image_id(disease_name, category, url)

                        # 컬럼 헤더 가져오기
                        column_header = headers[col_idx] if col_idx < len(headers) else f"컬럼_{col_idx}"

                        # 이미지 설명 (AI 분석 없이 기본 플레이스홀더)
                        alt_text = f"[{category}의 {column_header} 시각자료]"

                        image_meta = ImageMetadata(
                            image_id=image_id,
                            disease_name=disease_name,
                            category=category,
                            image_url=url,
                            image_type=self._guess_image_type(category),
                            alt_text=alt_text,
                            caption="",
                            table_context={
                                "row_index": row_idx,
                                "column_index": col_idx,
                                "column_header": column_header
                            }
                        )
                        image_records.append(image_meta)

                        # 텍스트에는 플레이스홀더 삽입
                        cell = cell.replace(full_match, f"[시각자료_{image_id}]")

                # 이미지 제거된 셀 텍스트 추가
                cell_clean = cell.strip()
                if cell_clean and cell_clean not in ["", "-"]:
                    row_text_parts.append(cell_clean)

            if row_text_parts:
                text_parts.append(" | ".join(row_text_parts))

        # 테이블을 텍스트로 변환
        table_text = "\n".join(text_parts)

        return table_text, image_records

    def process_images_array(
        self,
        images_data: List[Dict[str, Any]],
        disease_name: str,
        category: str,
        context_text: str = ""
    ) -> List[ImageMetadata]:
        """
        크롤링 구조의 images 배열 처리

        Args:
            images_data: [{"url": "...", "alt": "...", "location": "table/text"}]
            disease_name: 질병명
            category: 카테고리
            context_text: 섹션 텍스트 (사용 안 함)

        Returns:
            이미지 메타데이터 리스트
        """
        image_records = []

        for img_data in images_data:
            url = img_data.get('url', '')
            alt = img_data.get('alt', '')
            location = img_data.get('location', 'text')

            if not url:
                continue

            # 이미지 ID 생성
            image_id = self.generate_image_id(disease_name, category, url)

            # alt 텍스트 사용
            if alt and len(alt) > 0:
                print(f"   ✓ alt 텍스트 사용: {alt[:50]}...")
                description = alt
            else:
                # alt가 없으면 기본 설명
                description = f"[{category}의 시각자료]"
                print(f"   ⚠️  alt 없음, 기본 설명 사용")

            # caption 필드는 원본 데이터의 caption 사용
            original_caption = img_data.get('caption', '')

            image_meta = ImageMetadata(
                image_id=image_id,
                disease_name=disease_name,
                category=category,
                image_url=url,
                image_type=self._guess_image_type(category),
                alt_text=description,
                caption=original_caption,  # 원본 caption 사용
                table_context={"location": location} if location == "table" else None
            )
            image_records.append(image_meta)

        return image_records

    @staticmethod
    def _guess_image_type(category: str) -> str:
        """카테고리에서 이미지 타입 추론"""
        category_lower = category.lower()
        if "원인" in category_lower or "경과" in category_lower:
            return "graph"
        elif "검사" in category_lower:
            return "table"
        elif "정의" in category_lower:
            return "diagram"
        else:
            return "illustration"


# ==============================
# 필터링: 불필요한 필드 제거
# ==============================

class DataFilter:
    """RAG에 부적절한 데이터 필터링"""

    # 제거할 키 패턴
    EXCLUDE_KEYS = {
        "__intro__",
        "참고문헌",
        "검사",  # 설문지 제거
    }

    @classmethod
    def should_exclude(cls, key: str) -> bool:
        """키가 제외 대상인지 확인"""
        for pattern in cls.EXCLUDE_KEYS:
            if pattern in key:
                return True
        return False

    @classmethod
    def filter_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리에서 불필요한 키 제거"""
        filtered = {}
        for key, value in data.items():
            if cls.should_exclude(key):
                continue

            if isinstance(value, dict):
                filtered[key] = cls.filter_dict(value)
            else:
                filtered[key] = value

        return filtered


# ==============================
# Transform 메인 로직
# ==============================

class DiseaseDataTransformer:
    """질병 데이터를 Vector DB + RDB 형식으로 변환"""

    def __init__(self):
        """Transform 초기화 (AI 분석 없음, alt 텍스트 사용)"""
        self.image_processor = TableImageProcessor()
        self.image_extractor = ImageExtractor()
        self.data_filter = DataFilter()

    def transform_disease_entry(
        self,
        disease_data: Dict[str, Any]
    ) -> Tuple[List[VectorChunk], List[ImageMetadata]]:
        """
        단일 질병 데이터 변환

        Returns:
            (Vector 청크 리스트, 이미지 메타데이터 리스트)
        """
        disease_name = disease_data.get("질환명", "Unknown")

        # 불필요한 필드 제거
        disease_data = self.data_filter.filter_dict(disease_data)

        vector_chunks = []
        all_image_metadata = []

        # 각 카테고리 처리 (개요, 진단, 치료, 스스로 돕는 법)
        for category_name, category_data in disease_data.items():
            if category_name == "질환명" or category_name == "이미지":
                continue

            if not isinstance(category_data, dict):
                continue

            # 카테고리 내 하위 섹션 처리
            chunks, images = self._process_category(
                disease_name,
                category_name,
                category_data
            )
            vector_chunks.extend(chunks)
            all_image_metadata.extend(images)

        return vector_chunks, all_image_metadata

    def _process_category(
        self,
        disease_name: str,
        category_name: str,
        category_data: Dict[str, Any]
    ) -> Tuple[List[VectorChunk], List[ImageMetadata]]:
        """카테고리 데이터 처리 (재귀적)"""
        chunks = []
        images = []

        for section_key, section_value in category_data.items():
            category_path = f"{category_name}.{section_key}"

            # tables, text, images 배열이 있는 경우 (크롤링 v2 구조)
            if isinstance(section_value, dict):
                if "tables" in section_value or "text" in section_value or "images" in section_value:
                    chunk, imgs = self._process_section_with_tables(
                        disease_name,
                        category_path,
                        section_value
                    )
                    if chunk:
                        chunks.append(chunk)
                    images.extend(imgs)
                else:
                    # 중첩된 딕셔너리 재귀 처리
                    sub_chunks, sub_imgs = self._process_category(
                        disease_name,
                        category_path,
                        section_value
                    )
                    chunks.extend(sub_chunks)
                    images.extend(sub_imgs)

            # 단순 텍스트
            elif isinstance(section_value, str):
                chunk = self._create_text_chunk(
                    disease_name,
                    category_path,
                    section_value
                )
                if chunk:
                    chunks.append(chunk)

            # 리스트 (테이블일 가능성)
            elif isinstance(section_value, list):
                # 2D 리스트인지 확인 (테이블)
                if section_value and isinstance(section_value[0], list):
                    chunk, imgs = self._process_table_list(
                        disease_name,
                        category_path,
                        section_value
                    )
                    if chunk:
                        chunks.append(chunk)
                    images.extend(imgs)

        return chunks, images

    def _process_section_with_tables(
        self,
        disease_name: str,
        category: str,
        section_data: Dict[str, Any]
    ) -> Tuple[Optional[VectorChunk], List[ImageMetadata]]:
        """tables, text, images가 있는 섹션 처리 (크롤링 v2 구조)"""
        content_parts = []
        all_images = []

        # 1. text 처리
        text_content = section_data.get("text", "")
        if text_content:
            content_parts.append(f"[텍스트 설명]\n{text_content}")

        # 2. tables 처리
        tables = section_data.get("tables", [])
        if tables:
            for table_idx, table in enumerate(tables):
                if not isinstance(table, list):
                    continue

                table_text, table_images = self.image_processor.process_table(
                    table,
                    disease_name,
                    category
                )

                if table_text:
                    content_parts.append(f"[표 {table_idx + 1}]\n{table_text}")
                all_images.extend(table_images)

        # 3. images 배열 처리
        images_data = section_data.get("images", [])
        if images_data:
            section_images = self.image_processor.process_images_array(
                images_data,
                disease_name,
                category,
                context_text=text_content
            )

            # 중복 제거 및 병합: 테이블에서 추출한 이미지와 images 배열의 이미지 병합
            all_images = self._merge_duplicate_images(all_images, section_images)

        if not content_parts:
            return None, []

        # 청크 생성
        chunk_id = self._generate_chunk_id(disease_name, category)
        content = "\n\n".join(content_parts)

        # 이미지 메타데이터에 청크 ID 연결
        for img in all_images:
            img.related_chunk_id = chunk_id

        # 메타데이터 구성
        metadata = {
            # 식별 정보
            "chunk_id": chunk_id,
            "disease_name": disease_name,
            "category": category,

            # 시각 자료 정보
            "has_visual": len(all_images) > 0,

            # 검색 최적화
            "content_type": self._infer_content_type(category),
        }

        chunk = VectorChunk(
            chunk_id=chunk_id,
            content=content,
            metadata=metadata
        )

        return chunk, all_images

    def _process_table_list(
        self,
        disease_name: str,
        category: str,
        table_data: List[List[str]]
    ) -> Tuple[Optional[VectorChunk], List[ImageMetadata]]:
        """테이블 리스트 처리"""
        table_text, images = self.image_processor.process_table(
            table_data,
            disease_name,
            category
        )

        if not table_text:
            return None, []

        chunk_id = self._generate_chunk_id(disease_name, category)

        for img in images:
            img.related_chunk_id = chunk_id

        metadata = {
            "chunk_id": chunk_id,
            "disease_name": disease_name,
            "category": category,
            "has_visual": len(images) > 0,
            "content_type": self._infer_content_type(category),
        }

        chunk = VectorChunk(
            chunk_id=chunk_id,
            content=table_text,
            metadata=metadata
        )

        return chunk, images

    def _create_text_chunk(
        self,
        disease_name: str,
        category: str,
        text: str
    ) -> Optional[VectorChunk]:
        """순수 텍스트 청크 생성"""
        text = text.strip()
        if not text or len(text) < 10:
            return None

        chunk_id = self._generate_chunk_id(disease_name, category)

        metadata = {
            "chunk_id": chunk_id,
            "disease_name": disease_name,
            "category": category,
            "has_visual": False,
            "content_type": self._infer_content_type(category),
        }

        return VectorChunk(
            chunk_id=chunk_id,
            content=text,
            metadata=metadata
        )

    @staticmethod
    def _generate_chunk_id(disease_name: str, category: str) -> str:
        """청크 ID 생성"""
        hash_input = f"{disease_name}_{category}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"chunk_{hash_digest}"

    def _merge_duplicate_images(
        self,
        table_images: List[ImageMetadata],
        section_images: List[ImageMetadata]
    ) -> List[ImageMetadata]:
        """
        테이블에서 추출한 이미지와 images 배열의 이미지를 병합

        전략:
        1. image_id로 중복 확인
        2. 중복된 경우:
           - images 배열의 실제 alt_text 사용
           - 테이블의 table_context 정보 병합
        3. 중복되지 않은 경우 모두 포함
        """
        # image_id -> ImageMetadata 매핑
        merged_dict = {}

        # 1. 테이블 이미지를 먼저 추가 (table_context 정보 보존)
        for img in table_images:
            merged_dict[img.image_id] = img

        # 2. section_images를 순회하며 병합
        for section_img in section_images:
            if section_img.image_id in merged_dict:
                # 중복된 경우: 테이블 정보 + 실제 alt 텍스트 병합
                table_img = merged_dict[section_img.image_id]

                # 실제 alt 텍스트가 있으면 업데이트
                if section_img.alt_text and not section_img.alt_text.startswith("["):
                    table_img.alt_text = section_img.alt_text

                # caption 업데이트
                if section_img.caption:
                    table_img.caption = section_img.caption

                # table_context 병합: 테이블 위치 정보 추가
                if table_img.table_context and section_img.table_context:
                    # 테이블 셀 정보가 있으면 유지하고 location만 추가
                    if "row_index" in table_img.table_context:
                        table_img.table_context["location"] = "table"
                elif section_img.table_context:
                    table_img.table_context = section_img.table_context

            else:
                # 중복되지 않은 경우 추가
                merged_dict[section_img.image_id] = section_img

        return list(merged_dict.values())

    @staticmethod
    def _infer_content_type(category: str) -> str:
        """카테고리에서 content_type 추론"""
        category_lower = category.lower()

        if "정의" in category_lower:
            return "정의"
        elif "원인" in category_lower:
            return "원인"
        elif "증상" in category_lower:
            return "증상"
        elif "진단" in category_lower:
            return "진단"
        elif "치료" in category_lower:
            return "치료"
        elif "약물" in category_lower:
            return "약물치료"
        elif "예방" in category_lower or "돕는" in category_lower:
            return "예방/관리"
        elif "역학" in category_lower or "통계" in category_lower:
            return "통계"
        else:
            return "기타"


# ==============================
# 메인 실행
# ==============================

def main():
    """
    Transform 실행 (alt 텍스트 기반)

    사용 예시:
        python transform_info.py
    """
    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / 'data' / 'raw' / 'diseases_info.json'

    output_chunks = project_root / 'data' / 'vector_db' / 'info_chunks.json'
    output_images = project_root / 'data' / 'rdb' / 'image_metadata.json'

    # 출력 디렉토리 생성
    output_chunks.parent.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        diseases_data = json.load(f)

    print(f"📝 Transform 설정:")
    print(f"   - 이미지 처리: HTML alt 텍스트 사용")
    print(f"   - 입력 파일: {input_file}")
    print(f"   - 질병 데이터: {len(diseases_data)}개\n")

    transformer = DiseaseDataTransformer()

    all_chunks = []
    all_images = []

    for disease_entry in diseases_data:
        chunks, images = transformer.transform_disease_entry(disease_entry)
        all_chunks.extend(chunks)
        all_images.extend(images)

    # 저장
    with open(output_chunks, 'w', encoding='utf-8') as f:
        json.dump([chunk.to_dict() for chunk in all_chunks], f, ensure_ascii=False, indent=2)

    with open(output_images, 'w', encoding='utf-8') as f:
        json.dump([img.to_dict() for img in all_images], f, ensure_ascii=False, indent=2)

    print(f"✅ Transform 완료!")
    print(f"   - Vector 청크: {len(all_chunks)}개")
    print(f"   - 이미지 메타데이터: {len(all_images)}개")
    print(f"   - 출력 위치:")
    print(f"     • {output_chunks}")
    print(f"     • {output_images}")

    # 통계 출력
    images_with_alt = sum(1 for img in all_images if not img.alt_text.startswith("[이미지 설명 필요"))
    print(f"\n📊 통계:")
    print(f"   - 이미지 설명 필요: {len(all_images) - images_with_alt}개")
    print(f"   - 시각 자료 포함 청크: {sum(1 for c in all_chunks if c.metadata.get('has_visual'))}개")


if __name__ == '__main__':
    main()
