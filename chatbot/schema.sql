-- ===================================
-- 멘탈헬스 챗봇 데이터베이스 스키마
-- ===================================
-- DBMS: PostgreSQL 14+
-- 생성일: 2025-11-13
-- Django 마이그레이션과 동일한 스키마
-- ===================================

-- 1. Django 기본 사용자 테이블 (auth_user)
-- Django가 자동으로 생성하므로 참고용으로만 포함
-- CREATE TABLE auth_user (
--     id BIGSERIAL PRIMARY KEY,
--     username VARCHAR(150) UNIQUE NOT NULL,
--     email VARCHAR(254),
--     password VARCHAR(128) NOT NULL,
--     first_name VARCHAR(150),
--     last_name VARCHAR(150),
--     is_active BOOLEAN NOT NULL DEFAULT TRUE,
--     is_staff BOOLEAN NOT NULL DEFAULT FALSE,
--     is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
--     date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
--     last_login TIMESTAMP WITH TIME ZONE
-- );

-- ===================================
-- 2. 대화 세션 테이블 (chat_session)
-- ===================================
CREATE TABLE chat_session (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL DEFAULT 'info',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT check_session_type CHECK (
        session_type IN ('info', 'counseling')
    )
);

-- 인덱스
CREATE INDEX idx_chat_session_user_id ON chat_session(user_id);
CREATE INDEX idx_chat_session_created_at ON chat_session(created_at DESC);
CREATE INDEX idx_chat_session_user_created ON chat_session(user_id, created_at DESC);

-- 코멘트
COMMENT ON TABLE chat_session IS '사용자의 챗봇 대화 세션 정보';
COMMENT ON COLUMN chat_session.user_id IS '사용자 ID (FK)';
COMMENT ON COLUMN chat_session.session_type IS '대화 타입: info(정보형), counseling(상담형)';
COMMENT ON COLUMN chat_session.created_at IS '세션 시작 시간';
COMMENT ON COLUMN chat_session.updated_at IS '마지막 업데이트 시간';
COMMENT ON COLUMN chat_session.is_active IS '활성 상태';

-- ===================================
-- 3. 메시지 테이블 (message)
-- ===================================
CREATE TABLE message (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES chat_session(id) ON DELETE CASCADE,
    sender VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT check_sender CHECK (
        sender IN ('user', 'bot')
    )
);

-- 인덱스
CREATE INDEX idx_message_session_id ON message(session_id);
CREATE INDEX idx_message_created_at ON message(created_at);
CREATE INDEX idx_message_session_created ON message(session_id, created_at);

-- 코멘트
COMMENT ON TABLE message IS '사용자와 챗봇이 주고받은 메시지';
COMMENT ON COLUMN message.session_id IS '세션 ID (FK)';
COMMENT ON COLUMN message.sender IS '발신자: user(사용자), bot(챗봇)';
COMMENT ON COLUMN message.content IS '메시지 내용';
COMMENT ON COLUMN message.created_at IS '메시지 생성 시간';

-- ===================================
-- 4. 감정 분석 테이블 (sentiment_analysis)
-- ===================================
CREATE TABLE sentiment_analysis (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT UNIQUE NOT NULL REFERENCES message(id) ON DELETE CASCADE,
    sentiment_type VARCHAR(20) NOT NULL,
    sentiment_score FLOAT NOT NULL,
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT check_sentiment_type CHECK (
        sentiment_type IN ('positive', 'negative', 'neutral')
    ),
    CONSTRAINT check_sentiment_score CHECK (
        sentiment_score >= 0.0 AND sentiment_score <= 1.0
    )
);

-- 인덱스
CREATE UNIQUE INDEX idx_sentiment_message_id ON sentiment_analysis(message_id);
CREATE INDEX idx_sentiment_analyzed_at ON sentiment_analysis(analyzed_at DESC);
CREATE INDEX idx_sentiment_type ON sentiment_analysis(sentiment_type);
-- JSONB 키워드 검색용 GIN 인덱스
CREATE INDEX idx_sentiment_keywords ON sentiment_analysis USING GIN (keywords);

-- 코멘트
COMMENT ON TABLE sentiment_analysis IS '메시지의 감정 분석 결과';
COMMENT ON COLUMN sentiment_analysis.message_id IS '메시지 ID (FK, 1:1 관계)';
COMMENT ON COLUMN sentiment_analysis.sentiment_type IS '감정 타입: positive(긍정), negative(부정), neutral(중립)';
COMMENT ON COLUMN sentiment_analysis.sentiment_score IS '감정 점수 (0.0 ~ 1.0)';
COMMENT ON COLUMN sentiment_analysis.keywords IS '감정 키워드 배열 (JSONB)';
COMMENT ON COLUMN sentiment_analysis.analyzed_at IS '분석 수행 시간';

-- ===================================
-- 5. 질환 검색 테이블 (disease_query)
-- ===================================
CREATE TABLE disease_query (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES message(id) ON DELETE CASCADE,
    disease_name VARCHAR(100) NOT NULL,
    searched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_disease_message_id ON disease_query(message_id);
CREATE INDEX idx_disease_searched_at ON disease_query(searched_at DESC);
-- 복합 인덱스 (질환별 최근 검색 조회 최적화)
CREATE INDEX disease_que_disease_5396f7_idx ON disease_query(disease_name, searched_at DESC);

-- 코멘트
COMMENT ON TABLE disease_query IS '사용자가 검색한 질환 정보';
COMMENT ON COLUMN disease_query.message_id IS '메시지 ID (FK)';
COMMENT ON COLUMN disease_query.disease_name IS '질환명 (우울증, 불안장애 등)';
COMMENT ON COLUMN disease_query.searched_at IS '검색 시간';

-- ===================================
-- 트리거 함수: updated_at 자동 업데이트
-- ===================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- chat_session의 updated_at 자동 업데이트 트리거
CREATE TRIGGER trigger_chat_session_updated_at
BEFORE UPDATE ON chat_session
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ===================================
-- 샘플 데이터 (선택 사항)
-- ===================================
-- 테스트 사용자 생성 (선택 사항)
-- INSERT INTO auth_user (username, email, password, is_active, is_staff, is_superuser, date_joined)
-- VALUES ('testuser', 'test@example.com', 'pbkdf2_sha256$...(hashed_password)', TRUE, FALSE, FALSE, NOW());

-- ===================================
-- 유용한 뷰 (선택 사항)
-- ===================================

-- 사용자별 감정 분포 통계 뷰
CREATE OR REPLACE VIEW v_user_sentiment_stats AS
SELECT
    cs.user_id,
    sa.sentiment_type,
    COUNT(*) as count,
    ROUND(AVG(sa.sentiment_score)::numeric, 3) as avg_score
FROM sentiment_analysis sa
JOIN message m ON sa.message_id = m.id
JOIN chat_session cs ON m.session_id = cs.id
GROUP BY cs.user_id, sa.sentiment_type
ORDER BY cs.user_id, sa.sentiment_type;

-- 인기 질환 검색 순위 뷰
CREATE OR REPLACE VIEW v_popular_diseases AS
SELECT
    disease_name,
    COUNT(*) as search_count,
    COUNT(DISTINCT dq.message_id) as unique_searches,
    MAX(searched_at) as last_searched
FROM disease_query dq
GROUP BY disease_name
ORDER BY search_count DESC;

-- 일별 대화 통계 뷰
CREATE OR REPLACE VIEW v_daily_session_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_sessions,
    SUM(CASE WHEN session_type = 'info' THEN 1 ELSE 0 END) as info_sessions,
    SUM(CASE WHEN session_type = 'counseling' THEN 1 ELSE 0 END) as counseling_sessions
FROM chat_session
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ===================================
-- 데이터베이스 권한 설정 (선택 사항)
-- ===================================
-- Django 사용자에게 권한 부여
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO django_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO django_user;
