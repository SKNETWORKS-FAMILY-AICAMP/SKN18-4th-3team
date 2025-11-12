"""
RetrievalAgent - 검색 에이전트

[역할]
RDB와 VectorDB를 병렬로 검색하여 관련 문서를 가져옵니다.

[사용 노드]
- search_rdb_node.py: 이미지 메타데이터 검색
- search_vector_db_node.py: 텍스트 청크 검색

[분기 로직]
분기 없음 (병렬 실행 후 병합)
"""

# TODO: RetrievalAgent 구현