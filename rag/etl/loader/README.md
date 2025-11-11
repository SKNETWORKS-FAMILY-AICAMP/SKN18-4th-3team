# Loader (데이터 적재)

변환된 데이터를 데이터베이스에 저장하는 폴더입니다.

## 🎯 역할

Transform 단계에서 생성된 임베딩 데이터를 벡터 DB와 RDB에 저장합니다.

## 📝 파일 설명

### loader.py
**기능**: 데이터베이스 적재
- 벡터 DB(pgvector)에 임베딩 저장
- RDB(PostgreSQL)에 메타데이터 저장
- 배치 처리로 대량 데이터 효율적 저장

**입력**: 
- `data/faq_chunks.csv`
- `data/info_chunks.csv`

**출력**: 
- pgvector 테이블에 임베딩 저장
- PostgreSQL 테이블에 메타데이터 저장

## 🔄 적재 프로세스

```
1. 데이터 로드
   CSV 파일 읽기
   ↓
2. 데이터 검증
   필수 필드 확인
   임베딩 벡터 형식 검증
   ↓
3. 벡터 DB 저장
   pgvector에 임베딩 저장
   인덱스 생성 (유사도 검색 최적화)
   ↓
4. RDB 저장
   PostgreSQL에 메타데이터 저장
   관계 설정
   ↓
5. 완료
   저장 결과 로깅
```

## 💡 사용 예시

### CLI 사용
```bash
# FAQ 데이터 적재
python rag/etl/loader/loader.py --type faq

# 질병 정보 적재
python rag/etl/loader/loader.py --type info

# 전체 데이터 적재
python rag/etl/loader/loader.py --all
```

### Python 코드에서 사용
```python
from rag.etl.loader.loader import VectorLoader, RDBLoader

# 1. 벡터 DB 로더 초기화
vector_loader = VectorLoader()

# 2. FAQ 임베딩 적재
vector_loader.load_from_csv("data/faq_chunks.csv", table="faq_embeddings")

# 3. 질병 정보 임베딩 적재
vector_loader.load_from_csv("data/info_chunks.csv", table="info_embeddings")

# 4. 메타데이터 적재
rdb_loader = RDBLoader()
rdb_loader.load_metadata("data/image_metadata.csv")
```

## 🗄️ 데이터베이스 스키마

### pgvector 테이블 (faq_embeddings)
```sql
CREATE TABLE faq_embeddings (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embedding 차원
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 유사도 검색을 위한 인덱스
CREATE INDEX ON faq_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### pgvector 테이블 (info_embeddings)
```sql
CREATE TABLE info_embeddings (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON info_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### PostgreSQL 테이블 (metadata)
```sql
CREATE TABLE image_metadata (
    id SERIAL PRIMARY KEY,
    image_path TEXT,
    description TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

## ⚙️ 설정 옵션

### 배치 설정
- `batch_size`: 한 번에 저장할 레코드 수 (기본: 1000)
- `commit_interval`: 커밋 주기 (기본: 5000)

### 연결 설정
- `db_host`: 데이터베이스 호스트
- `db_port`: 포트 번호
- `db_name`: 데이터베이스 이름
- `db_user`: 사용자명
- `db_password`: 비밀번호

## 🔍 검증 및 모니터링

### 적재 후 검증
```python
from rag.etl.loader.loader import validate_load

# 적재된 데이터 검증
stats = validate_load("faq_embeddings")
print(f"총 레코드 수: {stats['total_records']}")
print(f"임베딩 차원: {stats['embedding_dim']}")
```

### 로깅
- 적재 시작/종료 시간
- 처리된 레코드 수
- 에러 발생 시 상세 정보

## 🔗 연관 모듈

- `rag/vector_store.py`: 벡터 DB 검색 기능
- `rag/etl/transform/`: 적재할 데이터 생성
- `data/`: 적재할 CSV 파일 위치
