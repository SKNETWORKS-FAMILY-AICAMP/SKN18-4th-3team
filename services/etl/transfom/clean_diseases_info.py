import json
from pathlib import Path
from typing import Dict, Any, List


# ==============================
# diseases_info.json 정리 스크립트
# ==============================
def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    # 연속 공백 정규화 및 양끝 공백 제거
    return " ".join(text.split()).strip()


def pick_longer(a: Any, b: Any) -> Any:
    """
    두 값 중 텍스트 길이가 더 긴 것을 선택. dict/list는 길이 기준으로 판단.
    """
    if a is None:
        return b
    if b is None:
        return a
    try:
        len_a = len(a) if not isinstance(a, str) else len(a)
        len_b = len(b) if not isinstance(b, str) else len(b)
        return a if len_a >= len_b else b
    except Exception:
        return a if a else b


def merge_tab_dicts(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """
    탭(dict) 데이터 병합. 동일 키가 있으면 더 긴 내용을 유지.
    값이 dict인 경우에도 길이기준으로 선택.
    """
    if not isinstance(base, dict):
        base = {}
    if not isinstance(incoming, dict):
        return base

    for k, v in incoming.items():
        key = normalize_text(k)
        if not key:
            continue
        val = v
        if isinstance(val, str):
            val = normalize_text(val)
        if key in base:
            base[key] = pick_longer(base[key], val)
        else:
            base[key] = val
    return base


def unique_list(seq: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for item in seq or []:
        if isinstance(item, str):
            item_norm = normalize_text(item)
        else:
            item_norm = item
        key = json.dumps(item_norm, ensure_ascii=False, sort_keys=True) if isinstance(item_norm, (dict, list)) else item_norm
        if key in seen:
            continue
        seen.add(key)
        out.append(item_norm)
    return out


def clean_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    # url 키 제거
    entry.pop('url', None)

    # 질환명 정리
    if '질환명' in entry and isinstance(entry['질환명'], str):
        entry['질환명'] = normalize_text(entry['질환명'])

    # 탭 정리 및 중복 제거
    tabs = ['개요', '진단', '치료', '스스로 돕는 법']
    for tab in tabs:
        if tab in entry and isinstance(entry[tab], dict):
            cleaned = {}
            cleaned = merge_tab_dicts(cleaned, entry[tab])
            entry[tab] = cleaned

    # 이미지 URL 중복 제거
    if '이미지' in entry and isinstance(entry['이미지'], list):
        entry['이미지'] = unique_list(entry['이미지'])

    return entry


def main() -> None:
    # 프로젝트 루트 기준 경로
    project_root = Path(__file__).resolve().parents[3]
    src = project_root / 'data' / 'raw' / 'diseases_info.json'
    dst = project_root / 'data' / 'raw' / 'diseases_info_cleaned.json'

    if not src.exists():
        raise FileNotFoundError(f"입력 파일이 존재하지 않습니다: {src}")

    with open(src, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError('JSON 루트는 리스트여야 합니다.')

    # 질환명 기준으로 항목 병합하여 중복 제거
    merged: Dict[str, Dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        item = clean_entry(item)
        name = item.get('질환명')
        if not name:
            # 질환명 없는 경우는 고유 해시로 유지 (가능하면 병합하지 않음)
            name = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if name in merged:
            # 탭/이미지 병합
            for tab in ['개요', '진단', '치료', '스스로 돕는 법']:
                merged[ name ][ tab ] = merge_tab_dicts(merged[name].get(tab, {}), item.get(tab, {}))
            # 이미지 병합
            imgs = []
            if isinstance(merged[name].get('이미지'), list):
                imgs.extend(merged[name]['이미지'])
            if isinstance(item.get('이미지'), list):
                imgs.extend(item['이미지'])
            if imgs:
                merged[name]['이미지'] = unique_list(imgs)
        else:
            # 기본 탭 구조 보장
            base_entry = {
                '질환명': name,
                '개요': {},
                '진단': {},
                '치료': {},
                '스스로 돕는 법': {}
            }
            for tab in ['개요', '진단', '치료', '스스로 돕는 법']:
                base_entry[tab] = merge_tab_dicts(base_entry.get(tab, {}), item.get(tab, {}))
            if isinstance(item.get('이미지'), list):
                base_entry['이미지'] = unique_list(item['이미지'])
            merged[name] = base_entry

    cleaned_list = list(merged.values())

    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(cleaned_list, f, ensure_ascii=False, indent=2)

    print(f"원본 개수: {len(data)} -> 정리 후 개수: {len(cleaned_list)}")
    print(f"저장 위치: {dst}")


if __name__ == '__main__':
    main()


