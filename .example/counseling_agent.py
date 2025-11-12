"""
CounselingAgent - 상담형 쿼리 처리 에이전트

[역할]
사용자의 감정, 상황, 증상을 파악하고 상담 답변을 생성합니다.

[사용 노드]
- guideline_checker_node.py: 필수 정보 확인
- symptom_extractor_node.py: 증상 추출
- follow_up_question_node.py: 추가 질문 생성
- retrieval_agent.py: 검색
- evaluate_node.py: 검색 결과 평가
- create_answer_node.py: 답변 생성

[분기 로직]
GuidelineCheckerNode 결과에 따라:
- is_sufficient = True → SymptomExtractorNode → 답변 생성
- is_sufficient = False → FollowUpQuestionNode → 다시 GuidelineCheckerNode로 루프
"""

# TODO: CounselingAgent 구현