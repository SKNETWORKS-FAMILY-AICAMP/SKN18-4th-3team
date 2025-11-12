-- ==============================
-- PostgreSQL + pgvector 스키마
-- ==============================

-- 타임존 설정 (한국 시간)
SET TIME ZONE 'Asia/Seoul';

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- ==============================
-- 1. 이미지 메타데이터 테이블 (RDB)
-- ==============================

CREATE TABLE IF NOT EXISTS image_metadata (
    -- 기본키
    image_id VARCHAR(50) PRIMARY KEY,
    disease_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,

    -- 이미지 정보
    image_url TEXT NOT NULL,
    image_type VARCHAR(50),  -- 'graph', 'table', 'diagram', 'photo'

    -- 메타데이터
    alt_text TEXT,
    caption TEXT,

    -- 관계 정보
    related_chunk_id VARCHAR(50),
    table_context JSONB,  -- 테이블 내 위치 정보 {"row_index": 1, "column_index": 0, "column_header": "..."}

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_image_disease ON image_metadata(disease_name);
CREATE INDEX IF NOT EXISTS idx_image_category ON image_metadata(category);
CREATE INDEX IF NOT EXISTS idx_image_chunk ON image_metadata(related_chunk_id);
CREATE INDEX IF NOT EXISTS idx_image_type ON image_metadata(image_type);


-- ==============================
-- 2. 임베딩 테이블 (Vector DB)
-- ==============================

-- 2-1. KM-BERT 임베딩 (768 차원)
CREATE TABLE IF NOT EXISTS embeddings_kmbert (
    -- 기본키
    chunk_id VARCHAR(50) PRIMARY KEY,

    -- 콘텐츠
    content TEXT NOT NULL,

    -- 임베딩 벡터 (768 차원)
    embedding vector(768) NOT NULL,

    -- 메타데이터
    disease_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    has_visual BOOLEAN DEFAULT FALSE,
    content_type VARCHAR(50),  -- 'faq', 'info', 'text', 'table', 'test' 등

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- KM-BERT 임베딩 벡터 검색용 HNSW 인덱스
CREATE INDEX IF NOT EXISTS idx_kmbert_embedding_hnsw
ON embeddings_kmbert
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 메타데이터 필드 인덱스
CREATE INDEX IF NOT EXISTS idx_kmbert_disease ON embeddings_kmbert(disease_name);
CREATE INDEX IF NOT EXISTS idx_kmbert_category ON embeddings_kmbert(category);
CREATE INDEX IF NOT EXISTS idx_kmbert_content_type ON embeddings_kmbert(content_type);
CREATE INDEX IF NOT EXISTS idx_kmbert_has_visual ON embeddings_kmbert(has_visual);


-- 2-2. OpenAI text-embedding-3-small (1536 차원)
CREATE TABLE IF NOT EXISTS embeddings_openai_small (
    -- 기본키
    chunk_id VARCHAR(50) PRIMARY KEY,

    -- 콘텐츠
    content TEXT NOT NULL,

    -- 임베딩 벡터 (1536 차원)
    embedding vector(1536) NOT NULL,

    -- 메타데이터
    disease_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    has_visual BOOLEAN DEFAULT FALSE,
    content_type VARCHAR(50),

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- OpenAI Small 임베딩 벡터 검색용 HNSW 인덱스
CREATE INDEX IF NOT EXISTS idx_openai_small_embedding_hnsw
ON embeddings_openai_small
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 메타데이터 필드 인덱스
CREATE INDEX IF NOT EXISTS idx_openai_small_disease ON embeddings_openai_small(disease_name);
CREATE INDEX IF NOT EXISTS idx_openai_small_category ON embeddings_openai_small(category);
CREATE INDEX IF NOT EXISTS idx_openai_small_content_type ON embeddings_openai_small(content_type);
CREATE INDEX IF NOT EXISTS idx_openai_small_has_visual ON embeddings_openai_small(has_visual);


-- 2-3. OpenAI text-embedding-3-large (3072 차원)
CREATE TABLE IF NOT EXISTS embeddings_openai_large (
    -- 기본키
    chunk_id VARCHAR(50) PRIMARY KEY,

    -- 콘텐츠
    content TEXT NOT NULL,

    -- 임베딩 벡터 (3072 차원)
    embedding vector(3072) NOT NULL,

    -- 메타데이터
    disease_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    has_visual BOOLEAN DEFAULT FALSE,
    content_type VARCHAR(50),

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- OpenAI Large 임베딩 테이블은 2000차원 초과 벡터를 사용하므로 pgvector의 HNSW/IVF_FLAT 인덱스를 생성할 수 없음
-- 고차원 벡터는 순차 검색 사용

-- 메타데이터 필드 인덱스
CREATE INDEX IF NOT EXISTS idx_openai_large_disease ON embeddings_openai_large(disease_name);
CREATE INDEX IF NOT EXISTS idx_openai_large_category ON embeddings_openai_large(category);
CREATE INDEX IF NOT EXISTS idx_openai_large_content_type ON embeddings_openai_large(content_type);
CREATE INDEX IF NOT EXISTS idx_openai_large_has_visual ON embeddings_openai_large(has_visual);

-- ==============================
-- 3. 검색 함수
-- ==============================

-- 임베딩 유사도 검색 함수 (KM-BERT)
CREATE OR REPLACE FUNCTION search_kmbert_similarity(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    chunk_id VARCHAR,
    content TEXT,
    disease_name VARCHAR,
    category VARCHAR,
    content_type VARCHAR,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.chunk_id,
        e.content,
        e.disease_name,
        e.category,
        e.content_type,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings_kmbert e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- 임베딩 유사도 검색 함수 (OpenAI Small)
CREATE OR REPLACE FUNCTION search_openai_small_similarity(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    chunk_id VARCHAR,
    content TEXT,
    disease_name VARCHAR,
    category VARCHAR,
    content_type VARCHAR,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.chunk_id,
        e.content,
        e.disease_name,
        e.category,
        e.content_type,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings_openai_small e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- 임베딩 유사도 검색 함수 (OpenAI Large)
CREATE OR REPLACE FUNCTION search_openai_large_similarity(
    query_embedding vector(3072),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    chunk_id VARCHAR,
    content TEXT,
    disease_name VARCHAR,
    category VARCHAR,
    content_type VARCHAR,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.chunk_id,
        e.content,
        e.disease_name,
        e.category,
        e.content_type,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings_openai_large e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ==============================
-- 초기화 완료
-- ==============================
DO $$
BEGIN
    RAISE NOTICE '데이터베이스 초기화 완료!';
    RAISE NOTICE '   - image_metadata: 이미지 메타데이터';
    RAISE NOTICE '   - embeddings_kmbert: KM-BERT (768차원)';
    RAISE NOTICE '   - embeddings_openai_small: OpenAI Small (1536차원)';
    RAISE NOTICE '   - embeddings_openai_large: OpenAI Large (3072차원)';
    RAISE NOTICE '   - diagnostic_tests: 진단 검사 데이터';
END $$;
