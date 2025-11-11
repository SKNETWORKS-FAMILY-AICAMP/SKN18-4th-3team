# Transform (데이터 변환)

수집된 원본 데이터를 가공하고 임베딩을 생성하는 폴더입니다.

## 🎯 역할

Extract 단계에서 수집된 데이터를 전처리하고, 청킹하며, 임베딩 벡터를 생성합니다.

## 📝 파일 설명

### transform_faq.py
**기능**: FAQ 데이터 변환
- 텍스트 정제 (HTML 태그 제거, 특수문자 처리)
- 질문-답변 쌍 구조화
- 메타데이터 추가

**입력**: `data/diseases_faq.json`
**출력**: 전처리된 FAQ 데이터

### transform_info.py
**기능**: 질병 정보 변환
- 긴 텍스트 청킹 (chunking)
- 문장 단위 분할
- 컨텍스트 유지하며 분할

**입력**: `data/diseases_info.json`
**출력**: 청크 단위 질병 정보

### transform_cli.py
**기능**: 변환 및 임베딩 생성 CLI
- 전처리 실행
- 임베딩 벡터 생성
- CSV 파일로 저장

**출력**: 
- `data/faq_chunks.csv`
- `data/info_chunks.csv`

## 🔄 변환 프로세스

```
1. 전처리 (Preprocessing)
   - HTML 태그 제거
   - 특수문자 정규화
   - 공백 정리

2. 청킹 (Chunking)
   - 긴 텍스트를 작은 단위로 분할
   - 오버랩 설정 (컨텍스트 유지)
   - 최대 토큰 수 제한

3. 임베딩 생성 (Embedding)
   - OpenAI Embeddings API 호출
   - 텍스트 → 벡터 변환
   - 배치 처리로 효율성 향상

4. 저장 (Save)
   - CSV 형식으로 저장
   - 텍스트 + 임베딩 벡터 + 메타데이터
```

## 💡 사용 예시

### CLI 사용
```bash
# FAQ 변환
python rag/etl/transform/transform_cli.py --type faq

# 질병 정보 변환
python rag/etl/transform/transform_cli.py --type info

# 전체 변환 및 임베딩 생성
python rag/etl/transform/transform_cli.py --all
```

### Python 코드에서 사용
```python
from rag.etl.transform.transform_faq import transform_faq
from rag.etl.transform.transform_info import transform_info
from rag.embeddings import create_embeddings

# 1. FAQ 변환
faq_data = load_json("data/diseases_faq.json")
processed_faq = transform_faq(faq_data)

# 2. 임베딩 생성
faq_embeddings = create_embeddings(processed_faq)

# 3. 저장
save_csv(faq_embeddings, "data/faq_chunks.csv")
```

## 📊 출력 데이터 형식

### faq_chunks.csv
```csv
id,text,embedding,metadata
1,"당뇨병의 주요 증상은...","[0.123, -0.456, ...]","{\"category\": \"당뇨병\"}"
```

### info_chunks.csv
```csv
id,text,embedding,metadata
1,"당뇨병은 혈당 조절...","[0.789, -0.234, ...]","{\"disease\": \"당뇨병\", \"chunk\": 1}"
```

## ⚙️ 설정 옵션

### 청킹 설정
- `chunk_size`: 청크 크기 (기본: 500 토큰)
- `chunk_overlap`: 오버랩 크기 (기본: 50 토큰)

### 임베딩 설정
- `model`: 임베딩 모델 (기본: "text-embedding-3-small")
- `batch_size`: 배치 크기 (기본: 100)

## 🔗 연관 모듈

- `rag/embeddings.py`: 임베딩 생성 기능
- `rag/etl/extract/`: 원본 데이터 소스
- `rag/etl/loader/`: 변환된 데이터 적재
