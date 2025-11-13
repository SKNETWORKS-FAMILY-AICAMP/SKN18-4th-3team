"""
챗봇 유틸리티 함수 모음
감정 분석, 질환명 추출 등의 기능을 제공
"""

import re
from typing import Dict, List
from transformers import pipeline

# 감정 분석 모델 초기화 (전역 변수로 한 번만 로드)
_sentiment_analyzer = None

def get_sentiment_analyzer():
    """
    감정 분석 모델을 반환하는 함수
    모델을 한 번만 로드하여 재사용

    사용 모델: cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual
    - 다국어(한국어 포함) 감정 분석 모델
    - 긍정(positive), 부정(negative), 중립(neutral) 3가지로 분류
    - CPU 사용
    """
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        # 검증된 다국어 감정 분석 모델 (한국어 지원, CPU 사용)
        _sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
            device=-1  # CPU 사용
        )
        print("✓ cardiffnlp 다국어 감정 분석 모델 로드 성공 (CPU)")
    return _sentiment_analyzer


def analyze_sentiment(text: str) -> Dict[str, any]:
    """
    Fine-tuned LLM 모델을 사용하여 텍스트의 감정을 분석하는 함수

    Args:
        text: 분석할 텍스트

    Returns:
        dict: {
            'sentiment_type': 'positive' | 'negative' | 'neutral',
            'sentiment_score': float (0.0 ~ 1.0)
        }
    """
    if not text or len(text.strip()) == 0:
        return {
            'sentiment_type': 'neutral',
            'sentiment_score': 0.5
        }

    try:
        analyzer = get_sentiment_analyzer()
        result = analyzer(text[:512])[0]  # 최대 512자까지만 분석

        # 라벨을 우리 형식으로 변환
        label = result['label'].lower()
        score = result['score']

        # sentiment_type 결정
        # cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual: 'positive', 'negative', 'neutral'
        if 'positive' in label or label == 'pos':
            sentiment_type = 'positive'
        elif 'negative' in label or label == 'neg':
            sentiment_type = 'negative'
        else:
            sentiment_type = 'neutral'

        return {
            'sentiment_type': sentiment_type,
            'sentiment_score': score
        }

    except Exception as e:
        print(f"감정 분석 오류: {e}")
        return {
            'sentiment_type': 'neutral',
            'sentiment_score': 0.5
        }


def extract_disease_names(text: str) -> List[str]:
    """
    텍스트에서 질환명을 추출하는 함수

    Args:
        text: 분석할 텍스트

    Returns:
        list: 추출된 질환명 리스트
    """
    # 정신 건강 관련 질환 목록
    disease_patterns = [
        r'주요우울장애', r'우울장애', r'우울증', r'노인우울증', r'여성우울증', r'MDD', r'우울',
        r'범불안장애', r'불안장애', r'불안증', r'사회불안장애', r'사회공포증', r'GAD', r'불안',
        r'공황장애', r'공황발작', r'공황증', r'공황',
        r'외상후스트레스장애', r'외상후 스트레스장애', r'PTSD', r'트라우마', r'적응장애', r'스트레스장애', r'스트레스',
        r'강박장애', r'강박증', r'OCD',
        r'조현병', r'정신분열증', r'정신증', r'망상장애', r'섬망',
        r'1형 양극성장애', r'2형 양극성장애', r'양극성장애', r'조울증', r'bipolar',
        r'수면장애', r'불면장애', r'불면증', r'기면증', r'수면무호흡증', r'일주기리듬수면각성장애', r'야경증',
        r'섭식장애', r'거식증', r'신경성 폭식증', r'폭식증',
        r'경계성성격장애', r'경계성 성격장애', r'반사회성인격장애', r'반사회성 인격장애',
        r'연극성인격장애', r'연극성 인격장애', r'성격장애', r'BPD',
        r'주의력결핍과잉행동장애', r'주의력결핍 과잉행동장애', r'성인ADHD', r'ADHD',
        r'알츠하이머 치매', r'알츠하이머', r'치매', r'경도인지장애', r'전두측두엽신경인지장애',
        r'알코올사용장애', r'물질관련장애', r'도박장애', r'중독',
        r'자폐스펙트럼장애', r'틱장애', r'품행장애', r'배설장애', r'지적장애', r'특정학습장애',
        r'신체증상장애', r'월경전불쾌감증상', r'자살'
    ]

    found_diseases = []

    # 각 패턴에 대해 검색
    for pattern in disease_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in found_diseases:
                found_diseases.append(match)

    return found_diseases
