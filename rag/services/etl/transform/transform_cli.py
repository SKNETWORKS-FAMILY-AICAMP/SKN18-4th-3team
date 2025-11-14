"""
Transform CLI: FAQ 및 질병 정보 데이터를 병렬로 변환

이 스크립트는 다음 작업을 병렬로 수행합니다:
1. FAQ 데이터 Transform (diseases_faq.json → faq_chunks.json)
2. 질병 정보 Transform (diseases_info.json → info_chunks.json + image_metadata.json)

사용 예시:
    # 기본 실행 (병렬)
    python transform_cli.py

    # FAQ 청크 크기 조정
    python transform_cli.py --chunk-size 2000 --chunk-overlap 300

    # 순차 실행 (디버깅 시)
    python transform_cli.py --sequential
"""

import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed

# Transform 함수 임포트
from rag.services.etl.transform.transform_faq import FAQTransformer
from rag.services.etl.transform.transform_info import DiseaseDataTransformer


# ==============================
# FAQ Transform Worker
# ==============================

def run_faq_transform(chunk_size: int = 1500, chunk_overlap: int = 200) -> Dict[str, Any]:
    """
    FAQ Transform 실행 (병렬 처리용)

    Args:
        chunk_size: 청크당 최대 문자 수
        chunk_overlap: 청크 간 중복 문자 수

    Returns:
        Transform 결과 통계
    """
    print("🔄 [FAQ] Transform 시작...")
    start_time = time.time()

    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / 'data' / 'raw' / 'diseases_faq.json'
    output_file = project_root / 'data' / 'vector_db' / 'faq_chunks.json'

    # 출력 디렉토리 생성
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        faq_data = json.load(f)

    print(f"📂 [FAQ] 입력: {len(faq_data)}개 FAQ")

    # Transform
    transformer = FAQTransformer(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = transformer.transform(faq_data)

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([chunk.to_dict() for chunk in chunks], f, ensure_ascii=False, indent=2)

    # 통계
    stats = transformer.get_statistics(chunks)
    elapsed = time.time() - start_time

    return {
        "task": "FAQ",
        "input_file": str(input_file),
        "output_file": str(output_file),
        "input_count": len(faq_data),
        "output_count": len(chunks),
        "elapsed_time": elapsed,
        "stats": stats
    }


# ==============================
# 질병 정보 Transform Worker
# ==============================

def run_info_transform(chunk_size: int = 1500, chunk_overlap: int = 200) -> Dict[str, Any]:
    """
    질병 정보 Transform 실행 (병렬 처리용)

    Args:
        chunk_size: INFO 청크당 최대 문자 수
        chunk_overlap: INFO 청크 간 중복 문자 수

    Returns:
        Transform 결과 통계
    """
    print("🔄 [INFO] Transform 시작...")
    start_time = time.time()

    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / 'data' / 'raw' / 'diseases_info.json'
    output_chunks = project_root / 'data' / 'vector_db' / 'info_chunks.json'
    output_images = project_root / 'data' / 'rdb' / 'image_metadata.json'

    # 출력 디렉토리 생성
    output_chunks.parent.mkdir(parents=True, exist_ok=True)
    output_images.parent.mkdir(parents=True, exist_ok=True) 

    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        diseases_data = json.load(f)

    print(f"📂 [INFO] 입력: {len(diseases_data)}개 질병")

    # Transform
    transformer = DiseaseDataTransformer(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

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

    elapsed = time.time() - start_time

    # 통계
    images_with_alt = sum(1 for img in all_images if img.alt_text and not img.alt_text.startswith("["))
    visual_chunks = sum(1 for c in all_chunks if c.metadata.get('has_visual'))

    return {
        "task": "INFO",
        "input_file": str(input_file),
        "output_files": [str(output_chunks), str(output_images)],
        "input_count": len(diseases_data),
        "chunks_count": len(all_chunks),
        "images_count": len(all_images),
        "images_with_alt": images_with_alt,
        "visual_chunks": visual_chunks,
        "elapsed_time": elapsed
    }


# ==============================
# 병렬 실행 관리자
# ==============================

def run_parallel_transform(chunk_size: int = 1500, chunk_overlap: int = 200):
    """
    FAQ와 질병 정보 Transform을 병렬로 실행

    Args:
        chunk_size: FAQ/INFO 청크당 최대 문자 수
        chunk_overlap: FAQ/INFO 청크 간 중복 문자 수
    """
    print("=" * 60)
    print("🚀 Transform 병렬 실행 시작")
    print("=" * 60)

    start_time = time.time()

    # 병렬 실행
    with ProcessPoolExecutor(max_workers=2) as executor:
        # 작업 제출
        future_faq = executor.submit(run_faq_transform, chunk_size, chunk_overlap)
        future_info = executor.submit(run_info_transform, chunk_size, chunk_overlap)

        # 결과 수집
        results = []
        for future in as_completed([future_faq, future_info]):
            try:
                result = future.result()
                results.append(result)
                print(f"✅ [{result['task']}] 완료 ({result['elapsed_time']:.2f}초)")
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                raise

    total_elapsed = time.time() - start_time

    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 Transform 결과 요약")
    print("=" * 60)

    for result in sorted(results, key=lambda x: x['task']):
        print(f"\n[{result['task']}]")
        print(f"  입력: {result['input_file']}")

        if result['task'] == 'FAQ':
            print(f"  출력: {result['output_file']}")
            print(f"  FAQ 개수: {result['input_count']}개")
            print(f"  생성된 청크: {result['output_count']}개")
            print(f"  평균 청크 크기: {result['stats']['avg_chunk_size']:.0f}자")
        else:  # INFO
            print(f"  출력:")
            for out_file in result['output_files']:
                print(f"    - {out_file}")
            print(f"  질병 개수: {result['input_count']}개")
            print(f"  생성된 청크: {result['chunks_count']}개")
            print(f"  이미지 메타데이터: {result['images_count']}개")
            print(f"    - alt 텍스트 보유: {result['images_with_alt']}개")
            print(f"    - 시각 자료 포함 청크: {result['visual_chunks']}개")

        print(f"  실행 시간: {result['elapsed_time']:.2f}초")

    print(f"\n총 실행 시간: {total_elapsed:.2f}초")
    print("=" * 60)


def run_sequential_transform(chunk_size: int = 1500, chunk_overlap: int = 200):
    """
    FAQ와 질병 정보 Transform을 순차적으로 실행 (디버깅용)

    Args:
        chunk_size: FAQ/INFO 청크당 최대 문자 수
        chunk_overlap: FAQ/INFO 청크 간 중복 문자 수
    """
    print("=" * 60)
    print("🔄 Transform 순차 실행 시작 (디버깅 모드)")
    print("=" * 60)

    start_time = time.time()

    # FAQ Transform
    result_faq = run_faq_transform(chunk_size, chunk_overlap)
    print(f"✅ [FAQ] 완료 ({result_faq['elapsed_time']:.2f}초)\n")

    # INFO Transform
    result_info = run_info_transform(chunk_size, chunk_overlap)
    print(f"✅ [INFO] 완료 ({result_info['elapsed_time']:.2f}초)\n")

    total_elapsed = time.time() - start_time

    # 결과 출력 (병렬 실행과 동일)
    print("\n" + "=" * 60)
    print("📊 Transform 결과 요약")
    print("=" * 60)

    for result in [result_faq, result_info]:
        print(f"\n[{result['task']}]")
        print(f"  입력: {result['input_file']}")

        if result['task'] == 'FAQ':
            print(f"  출력: {result['output_file']}")
            print(f"  FAQ 개수: {result['input_count']}개")
            print(f"  생성된 청크: {result['output_count']}개")
            print(f"  평균 청크 크기: {result['stats']['avg_chunk_size']:.0f}자")
        else:  # INFO
            print(f"  출력:")
            for out_file in result['output_files']:
                print(f"    - {out_file}")
            print(f"  질병 개수: {result['input_count']}개")
            print(f"  생성된 청크: {result['chunks_count']}개")
            print(f"  이미지 메타데이터: {result['images_count']}개")
            print(f"    - alt 텍스트 보유: {result['images_with_alt']}개")
            print(f"    - 시각 자료 포함 청크: {result['visual_chunks']}개")

        print(f"  실행 시간: {result['elapsed_time']:.2f}초")

    print(f"\n총 실행 시간: {total_elapsed:.2f}초")
    print("=" * 60)


# ==============================
# 메인 실행
# ==============================

def main():
    """Transform CLI 메인 함수"""
    parser = argparse.ArgumentParser(
        description='FAQ 및 질병 정보 데이터 Transform (병렬 실행)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 실행 (병렬)
  python transform_cli.py

  # FAQ 청크 크기 조정
  python transform_cli.py --chunk-size 2000 --chunk-overlap 300

  # 순차 실행 (디버깅)
  python transform_cli.py --sequential
        """
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1500,
        help='FAQ/INFO 청크당 최대 문자 수 (기본값: 1500)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='FAQ/INFO 청크 간 중복 문자 수 (기본값: 200)'
    )
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='순차 실행 모드 (디버깅용)'
    )

    args = parser.parse_args()

    # 실행
    if args.sequential:
        run_sequential_transform(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
    else:
        run_parallel_transform(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )


if __name__ == '__main__':
    main()
