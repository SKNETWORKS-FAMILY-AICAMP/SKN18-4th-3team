# 환경변수 설정 가이드

## 환경변수 파일 위치

### 1. 프로젝트 루트 `.env` (Django 백엔드용)

**위치**: `/Users/jina/Documents/GitHub/SKN18-4th-3team/.env`

Django는 프로젝트 루트의 `.env` 파일을 읽습니다.

```bash
# React 개발 서버 포트
REACT_PORT=3001

# PostgreSQL 포트 (사용하는 경우)
PG_PORT=5432

# 기타 Django 설정 (필요시 추가)
# SECRET_KEY=your-secret-key
# DEBUG=True
```

### 2. `frontend/.env` (React 프론트엔드용)

**위치**: `/Users/jina/Documents/GitHub/SKN18-4th-3team/frontend/.env`

React는 `frontend/.env` 파일에서 `REACT_APP_` 접두사가 붙은 환경변수를 읽습니다.

```bash
# React 개발 서버 포트
PORT=3001

# Django 백엔드 API 설정
REACT_APP_DJANGO_HOST=localhost
REACT_APP_DJANGO_PORT=8000
```

## 생성 방법

터미널에서 다음 명령어를 실행하세요:

```bash
# 프로젝트 루트에 .env 파일 생성
cat > .env << 'EOF'
REACT_PORT=3001
PG_PORT=5432
EOF

# frontend/.env 파일 생성
cat > frontend/.env << 'EOF'
PORT=3001
REACT_APP_DJANGO_HOST=localhost
REACT_APP_DJANGO_PORT=8000
EOF
```

## 중요 사항

1. **React 환경변수**: `REACT_APP_` 접두사가 필수입니다.
2. **포트 변경**: 포트를 변경하려면 두 파일 모두 수정해야 합니다.
   - `REACT_PORT` (프로젝트 루트 `.env`): Django의 CORS 설정에 사용
   - `PORT` (frontend/.env): React 개발 서버 포트
   - `REACT_APP_DJANGO_PORT` (frontend/.env): React에서 Django API 호출 시 사용
3. **서버 재시작**: 환경변수 변경 후에는 서버를 재시작해야 합니다.
