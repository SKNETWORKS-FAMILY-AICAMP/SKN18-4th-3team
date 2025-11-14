#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트 기준)
BASE_DIR = Path(__file__).resolve().parent.parent  # 프로젝트 루트
load_dotenv(BASE_DIR / '.env')

# 프로젝트 루트를 sys.path에 추가 (rag 패키지 import를 위해)
# Python 패키지 구조로 rag.build_graph 같은 형식으로 import 가능
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # runserver 명령어 실행 시 환경 변수에서 포트 읽기
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        django_port = os.getenv('DJANGO_PORT', '8000')
        # 포트가 명시적으로 지정되지 않은 경우 환경 변수 포트 사용
        if len(sys.argv) == 2:
            sys.argv.append(django_port)
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
