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
            'sentiment_score': float (0.0 ~ 1.0),
            'keywords': list (감정 키워드 리스트)
        }
    """
    if not text or len(text.strip()) == 0:
        return {
            'sentiment_type': 'neutral',
            'sentiment_score': 0.5,
            'keywords': []
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

        # 감정 키워드 추출
        keywords = extract_emotion_keywords(text, sentiment_type)

        return {
            'sentiment_type': sentiment_type,
            'sentiment_score': score,
            'keywords': keywords
        }

    except Exception as e:
        print(f"감정 분석 오류: {e}")
        return {
            'sentiment_type': 'neutral',
            'sentiment_score': 0.5,
            'keywords': []
        }


def extract_emotion_keywords(text: str, sentiment_type: str = None) -> List[str]:
    """
    텍스트에서 감정 키워드를 추출하는 함수

    Args:
        text: 분석할 텍스트
        sentiment_type: 감정 타입 (positive/negative/neutral), None이면 모든 키워드 추출

    Returns:
        list: 추출된 감정 키워드 리스트
    """
    # 감정 키워드 사전
    emotion_keywords = {
        'positive': [
            '행복', '기쁨', '즐거움', '좋아', '감사', '사랑', '희망', '만족', '평온',
            '기대', '안심', '편안', '웃음', '미소', '고마', '감동', '뿌듯', '성취',
            '자신감', '긍정', '밝은', '따뜻', '설렘', '신남', '재미', '즐겁', '유쾌',
            '활기', '생기', '활발', '쾌활', '상쾌', '흐뭇', '흡족', '고맙', '기쁜', '행복한'
        ],
        'negative': [
            '우울', '슬픔', '불안', '걱정', '두려움', '스트레스', '화', '외로움',
            '괴로움', '고통', '힘듦', '피곤', '지침', '무기력', '답답', '막막',
            '후회', '죄책감', '수치심', '분노', '짜증', '불편', '불쾌', '싫음',
            '혐오', '증오', '원망', '서러움', '쓸쓸', '고독', '절망', '좌절',
            '실망', '허탈', '허무', '공허', '막연', '혼란', '당황', '놀람',
            '충격', '공포', '무서움', '겁', '긴장', '초조', '조급', '억울', '힘든'
        ]
    }

    found_keywords = []

    # sentiment_type이 지정되면 해당 타입의 키워드만 검색
    if sentiment_type and sentiment_type in emotion_keywords:
        keywords_to_search = emotion_keywords[sentiment_type]
    else:
        # 모든 감정 키워드 검색
        keywords_to_search = []
        for keywords in emotion_keywords.values():
            keywords_to_search.extend(keywords)

    # 텍스트에서 키워드 검색
    for keyword in keywords_to_search:
        if keyword in text:
            found_keywords.append(keyword)

    return found_keywords


DISEASE_NORMALIZATION_MAP = {
    # 우울
    '주요우울장애': '우울장애', '우울장애': '우울장애', '우울증': '우울장애',
    '노인우울증': '우울장애', '여성우울증': '우울장애', '우울과 우울장애': '우울장애',
    '우울': '우울장애', 'MDD': '우울장애',

    # 불안
    '범불안장애': '불안장애', '불안장애': '불안장애', '불안증': '불안장애',
    '사회불안장애': '불안장애', '사회공포증': '불안장애', '불안': '불안장애',
    'GAD': '불안장애',

    # 공황
    '공황장애': '공황장애', '공황증': '공황장애', '공황발작': '공황장애', '공황': '공황장애',

    # 외상
    '외상후스트레스장애': '외상후스트레스장애', '외상후 스트레스장애': '외상후스트레스장애',
    '트라우마': '외상후스트레스장애', '스트레스장애': '외상후스트레스장애',
    '스트레스': '외상후스트레스장애', '적응장애': '외상후스트레스장애', 'PTSD': '외상후스트레스장애',

    # 강박
    '강박장애': '강박장애', '강박증': '강박장애', 'OCD': '강박장애',

    # 조현병
    '조현병': '조현병', '정신분열증': '조현병', '정신증': '조현병',
    '망상장애': '조현병', '섬망': '조현병',

    # 양극성
    '양극성장애': '양극성장애', '조울증': '양극성장애', '1형 양극성장애': '양극성장애',
    '2형 양극성장애': '양극성장애', 'bipolar': '양극성장애',

    # 수면
    '수면장애': '수면장애', '불면장애': '수면장애', '불면증': '수면장애',
    '기면증': '수면장애', '수면무호흡증': '수면장애', '일주기리듬수면각성장애': '수면장애',
    '야경증': '수면장애',

    # 섭식
    '섭식장애': '섭식장애', '거식증': '섭식장애', '신경성 폭식증': '섭식장애', '폭식증': '섭식장애',

    # 성격
    '경계성성격장애': '성격장애', '반사회성인격장애': '성격장애', '연극성인격장애': '성격장애',
    '성격장애': '성격장애', 'BPD': '성격장애',

    # ADHD
    'ADHD': 'ADHD', '성인ADHD': 'ADHD', '성인 ADHD': 'ADHD',
    '주의력결핍과잉행동장애': 'ADHD', '주의력결핍 과잉행동장애': 'ADHD',
    '주의력 결핍 과잉행동장애': 'ADHD',

    # 치매
    '알츠하이머 치매': '치매', '알츠하이머': '치매', '치매': '치매',
    '경도인지장애': '치매', '전두측두엽신경인지장애': '치매',

    # 중독
    '알코올사용장애': '중독', '물질관련장애': '중독', '도박장애': '중독', '중독': '중독',

    # 기타
    '자폐스펙트럼장애': '자폐스펙트럼장애', '틱장애': '틱장애', '품행장애': '품행장애',
    '배설장애': '배설장애', '지적장애': '지적장애', '특정학습장애': '특정학습장애',
    '신체증상장애': '신체증상장애', '월경전불쾌감증상': '월경전불쾌감증상',
    '자살': '자살', '자살과 자살예방': '자살',
}

_DISEASE_NORMALIZATION_LOWER = {
    key.lower(): value for key, value in DISEASE_NORMALIZATION_MAP.items()
}

_DISEASE_TEXT_PATTERNS = [
    (pattern, normalize, pattern.lower())
    for pattern, normalize in DISEASE_NORMALIZATION_MAP.items()
]


def normalize_disease_name(name: str) -> str:
    if not name:
        return ''
    key = name.strip()
    if key in DISEASE_NORMALIZATION_MAP:
        return DISEASE_NORMALIZATION_MAP[key]
    lower_key = key.lower()
    if lower_key in _DISEASE_NORMALIZATION_LOWER:
        return _DISEASE_NORMALIZATION_LOWER[lower_key]
    return key


def detect_diseases_in_text(text: str) -> List[str]:
    """부분 문자열 검색으로 텍스트에서 질환명 후보 추출"""
    if not text:
        return []

    text_str = str(text)
    text_lower = text_str.lower()
    found: List[str] = []
    seen = set()

    for pattern, canonical, pattern_lower in _DISEASE_TEXT_PATTERNS:
        if not pattern:
            continue
        if pattern in text_str or (pattern_lower != pattern and pattern_lower in text_lower):
            normalized = normalize_disease_name(canonical)
            if normalized and normalized not in seen:
                seen.add(normalized)
                found.append(normalized)

    return found
