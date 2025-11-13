"""
Extract CLI - 크롤링 스크립트 실행 관리

두 크롤링 스크립트를 병렬로 실행할 수 있는 CLI 도구입니다.
- FAQ 크롤링 (crawling_faq.py)
- 질환 정보 크롤링 (crawling_info.py)
"""
import asyncio
import argparse
import sys
from pathlib import Path

# 출력 버퍼링 비활성화 (크롤링 진행 상황 실시간 출력)
import os
os.environ['PYTHONUNBUFFERED'] = '1'

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.etl.extract.crawling_faq import main as crawl_faq
from services.etl.extract.crawling_info import main as crawl_info


async def run_parallel():
    """
    두 크롤링을 병렬로 실행
    
    Returns:
        tuple: (FAQ 개수, 질환 개수)
    """
    print("=" * 60)
    print("병렬 크롤링 시작")
    print("=" * 60)
    print("FAQ 크롤링과 질환 정보 크롤링을 동시에 실행합니다.")
    print("주의: 두 크롤링의 로그가 섞여서 출력될 수 있습니다.\n")
    
    try:
        # 두 크롤링을 병렬로 실행
        faq_count, info_count = await asyncio.gather(
            crawl_faq(),
            crawl_info()
        )
        
        print("\n" + "=" * 60)
        print("병렬 크롤링 완료")
        print("=" * 60)
        print(f"FAQ 크롤링: {faq_count}개")
        print(f"질환 정보 크롤링: {info_count}개")
        
        return faq_count, info_count
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        raise


async def run_sequential():
    """
    두 크롤링을 순차적으로 실행
    
    Returns:
        tuple: (FAQ 개수, 질환 개수)
    """
    print("=" * 60)
    print("순차 크롤링 시작")
    print("=" * 60)
    
    try:
        # FAQ 크롤링 먼저 실행
        print("\n[1/2] FAQ 크롤링 시작...")
        faq_count = await crawl_faq()
        print(f"\nFAQ 크롤링 완료: {faq_count}개\n")
        
        # 질환 정보 크롤링 실행
        print("\n[2/2] 질환 정보 크롤링 시작...")
        info_count = await crawl_info()
        print(f"\n질환 정보 크롤링 완료: {info_count}개")
        
        print("\n" + "=" * 60)
        print("순차 크롤링 완료")
        print("=" * 60)
        print(f"FAQ 크롤링: {faq_count}개")
        print(f"질환 정보 크롤링: {info_count}개")
        
        return faq_count, info_count
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        raise


async def run_faq_only():
    """
    FAQ 크롤링만 실행
    
    Returns:
        int: FAQ 개수
    """
    print("=" * 60)
    print("FAQ 크롤링 시작")
    print("=" * 60)
    
    try:
        faq_count = await crawl_faq()
        print(f"\nFAQ 크롤링 완료: {faq_count}개")
        return faq_count
    except Exception as e:
        print(f"\n오류 발생: {e}")
        raise


async def run_info_only():
    """
    질환 정보 크롤링만 실행
    
    Returns:
        int: 질환 개수
    """
    print("=" * 60)
    print("질환 정보 크롤링 시작")
    print("=" * 60)
    
    try:
        info_count = await crawl_info()
        print(f"\n질환 정보 크롤링 완료: {info_count}개")
        return info_count
    except Exception as e:
        print(f"\n오류 발생: {e}")
        raise


def main():
    """
    CLI 메인 함수
    """
    parser = argparse.ArgumentParser(
        description='크롤링 스크립트 실행 관리',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 두 크롤링 병렬 실행 (기본값)
  python extract_cli.py
  
  # 두 크롤링 병렬 실행 (명시적)
  python extract_cli.py --parallel
  
  # 두 크롤링 순차 실행
  python extract_cli.py --sequential
  
  # FAQ 크롤링만 실행
  python extract_cli.py --faq-only
  
  # 질환 정보 크롤링만 실행
  python extract_cli.py --info-only
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--parallel',
        action='store_true',
        help='두 크롤링을 병렬로 실행 (기본값)'
    )
    group.add_argument(
        '--sequential',
        action='store_true',
        help='두 크롤링을 순차적으로 실행'
    )
    group.add_argument(
        '--faq-only',
        action='store_true',
        help='FAQ 크롤링만 실행'
    )
    group.add_argument(
        '--info-only',
        action='store_true',
        help='질환 정보 크롤링만 실행'
    )
    
    args = parser.parse_args()
    
    # 실행 모드 결정
    if args.sequential:
        asyncio.run(run_sequential())
    elif args.faq_only:
        asyncio.run(run_faq_only())
    elif args.info_only:
        asyncio.run(run_info_only())
    else:
        # 기본값: 병렬 실행
        asyncio.run(run_parallel())


if __name__ == "__main__":
    main()

