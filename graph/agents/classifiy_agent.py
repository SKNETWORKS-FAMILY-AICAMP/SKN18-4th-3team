"""
ClassifyAgent - 쿼리 분류 에이전트

[역할]
사용자 질문을 분석하여 "정보형" 또는 "상담형"으로 분류합니다.

[사용 노드]
- query_classifier_node.py: 쿼리 타입 분류

[분기 로직]
QueryClassifierNode 결과에 따라:
- query_type = "정보형" → InformationAgent로 라우팅
- query_type = "상담형" → CounselingAgent로 라우팅
"""

# TODO: ClassifyAgent 구현
