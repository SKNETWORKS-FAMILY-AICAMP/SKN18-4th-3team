"""
SQL Search Node
---------------

[기능 설명]
- 검증된 chunk의 메타데이터를 사용하여 RDB에서 관련 이미지 추출
- 문서 ID, 페이지 번호 등의 메타데이터로 이미지 조회
- 이미지 URL 반환

[입력 State]
- verified_chunks: list[dict] - 검증된 chunk 리스트
  - metadata: dict - chunk 메타데이터

[출력 State]
- verified_chunks: list[dict] - 검증된 chunk (전달)
- related_images: list[str] - 관련 이미지 경로/URL 리스트
"""

def sql_search_node(state):
    """
    RDB에서 관련 이미지를 검색하는 노드
    """
    verified_chunks = state.get("verified_chunks", [])
    
    # TODO: 메타데이터 기반 RDB 이미지 검색
    related_images = []
    
    for chunk in verified_chunks:
        metadata = chunk.get("metadata", {})
        # RDB 쿼리 로직
        pass
    
    return {
        "verified_chunks": verified_chunks,
        "related_images": related_images
    }
