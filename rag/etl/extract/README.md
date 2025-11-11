# Extract (데이터 추출)

외부 소스에서 원본 데이터를 수집하는 폴더입니다.

## 🎯 역할

웹사이트, API 등 외부 소스에서 필요한 데이터를 크롤링하여 수집합니다.

## 📝 파일 설명

### crawling_faq.py
**기능**: FAQ 데이터 크롤링
- 질문-답변 쌍 수집
- 카테고리별 FAQ 분류
- JSON 형식으로 저장

**출력**: `data/diseases_faq.json`

### crawling_info.py
**기능**: 질병 정보 크롤링
- 질병명, 증상, 치료법 등 수집
- 의료 정보 구조화
- JSON 형식으로 저장

**출력**: `data/diseases_info.json`

### extract_cli.py
**기능**: 크롤링 실행 CLI
- 명령줄에서 크롤링 실행
- 크롤링 옵션 설정
- 진행 상황 표시

## 💡 사용 예시

### CLI 사용
```bash
# FAQ 크롤링
python rag/etl/extract/extract_cli.py --type faq

# 질병 정보 크롤링
python rag/etl/extract/extract_cli.py --type info

# 전체 크롤링
python rag/etl/extract/extract_cli.py --all
```

### Python 코드에서 사용
```python
from rag.etl.extract.crawling_faq import FAQCrawler
from rag.etl.extract.crawling_info import InfoCrawler

# FAQ 크롤링
faq_crawler = FAQCrawler()
faq_data = faq_crawler.crawl()
faq_crawler.save(faq_data, "data/diseases_faq.json")

# 질병 정보 크롤링
info_crawler = InfoCrawler()
info_data = info_crawler.crawl()
info_crawler.save(info_data, "data/diseases_info.json")
```

## 📊 출력 데이터 형식

### FAQ 데이터 (diseases_faq.json)
```json
[
  {
    "id": 1,
    "category": "당뇨병",
    "question": "당뇨병의 주요 증상은 무엇인가요?",
    "answer": "당뇨병의 주요 증상은..."
  }
]
```

### 질병 정보 (diseases_info.json)
```json
[
  {
    "id": 1,
    "disease_name": "당뇨병",
    "symptoms": ["다뇨", "다음", "다식"],
    "treatment": "인슐린 치료...",
    "description": "당뇨병은..."
  }
]
```

## 🔗 다음 단계

수집된 데이터는 `rag/etl/transform/`에서 가공됩니다.
