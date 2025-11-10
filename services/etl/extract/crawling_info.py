import json
import asyncio
import re
import sys
from urllib.parse import quote
from playwright.async_api import async_playwright
from pathlib import Path

# 출력 버퍼링 비활성화 (크롤링 진행 상황 실시간 출력)
sys.stdout.reconfigure(line_buffering=True)


# ==============================
# 1단계: 질환 목록 페이지에서 링크 추출
# ==============================
async def crawl_disease_list(page):
    """
    질환 목록 페이지에서 모든 질환 링크를 추출하는 함수
    
    Args:
        page: Playwright 페이지 객체
        3
    Returns:
        list: 질환명과 URL을 포함한 딕셔너리 리스트
    """
    disease_links = []
    
    # 페이지 로드 대기
    try:
        await page.wait_for_selector('.in_box, a[href*="diseaseView"], a[href*="disease"]', timeout=10000)
    except:
        pass
    
    # 질환 목록 항목 찾기
    disease_items = await page.query_selector_all('a[href*="javascript:dissView"]')
    
    # 각 질환 링크 추출 및 URL 정규화
    seen_urls = set()
    for item in disease_items:
        try:
            href = await item.get_attribute('href')
            onclick = await item.get_attribute('onclick')
            full_url = None
            disease_name = None
            
            # JavaScript 함수 호출 형태 처리 (dissView 함수)
            if href and 'javascript:dissView' in href:
                # href="javascript:dissView('25', '1형 양극성장애')" 형식에서 파라미터 추출
                match = re.search(r"dissView\s*\(\s*['\"]?(\d+)['\"]?\s*,\s*['\"]([^'\"]+)['\"]", href)
                if match:
                    disease_cd = match.group(1)
                    disease_name = match.group(2)
                    # URL 생성 (올바른 패턴: diseaseDetail.do?dissId=25&srCodeNm=질환명)
                    full_url = f"https://www.mentalhealth.go.kr/portal/disease/diseaseDetail.do?dissId={disease_cd}&srCodeNm={quote(disease_name)}"
            # onclick 속성에서 URL 추출 (JavaScript 함수 호출 형태 처리)
            elif onclick and ('diseaseView' in onclick or 'dissView' in onclick):
                # dissView 함수 파라미터 추출
                match = re.search(r"dissView\s*\(\s*['\"]?(\d+)['\"]?\s*,\s*['\"]([^'\"]+)['\"]", onclick)
                if match:
                    disease_cd = match.group(1)
                    disease_name = match.group(2)
                    full_url = f"https://www.mentalhealth.go.kr/portal/disease/diseaseDetail.do?dissId={disease_cd}&srCodeNm={quote(disease_name)}"
            elif href and not href.startswith('javascript:'):
                # 상대 경로를 절대 경로로 변환
                if href.startswith('/'):
                    full_url = f"https://www.mentalhealth.go.kr{href}"
                elif href.startswith('http'):
                    full_url = href
                elif 'diseaseView.do' in href:
                    full_url = f"https://www.mentalhealth.go.kr/portal/{href}"
            
            if not full_url:
                continue
            
            # 중복 제거
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            # 질환명 추출 (JavaScript에서 추출하지 못한 경우)
            if not disease_name:
                disease_name = await item.inner_text()
                if not disease_name or not disease_name.strip():
                    # strong 태그 내부에서 질환명 추출 시도
                    strong_elem = await item.query_selector('strong')
                    if strong_elem:
                        disease_name = await strong_elem.inner_text()
            
            if disease_name and disease_name.strip():
                disease_links.append({
                    'name': disease_name.strip(),
                    'url': full_url
                })
        except Exception as e:
            print(f"질환 링크 추출 중 오류: {e}")
            continue
    
    return disease_links


# ==============================
# 2단계: 페이지네이션 처리
# ==============================
async def navigate_to_page(page, page_number):
    """
    특정 페이지 번호로 이동하는 함수
    
    Args:
        page: Playwright 페이지 객체
        page_number: 이동할 페이지 번호
        
    Returns:
        bool: 페이지 이동 성공 여부
    """
    try:
        # 페이지 번호 링크 찾기
        page_link = page.locator(f'li.num a:has-text("{page_number}")').first
        if await page_link.count() > 0:
            # 현재 페이지가 아닌 경우만 클릭
            class_attr = await page_link.get_attribute('class')
            if class_attr and 'on' in class_attr:
                return True  # 이미 해당 페이지에 있음
            
            # 페이지 클릭 및 로드 대기
            await page_link.click()
            await page.wait_for_timeout(2000)  # 페이지 로드 대기
            
            # 페이지 로드 확인
            await page.wait_for_selector('.in_box, a[href*="diseaseView"]', timeout=5000)
            return True
    except Exception as e:
        print(f"페이지 {page_number}로 이동 실패: {e}")
    return False


# ==============================
# 3단계: 탭별 내용 추출 (개요, 진단, 치료, 스스로 돕는 법)
# ==============================
async def extract_tab_content(page, tab_name):
    """
    특정 탭(개요, 진단, 치료, 스스로 돕는 법)의 내용을 추출하는 함수

    Args:
        page: Playwright 페이지 객체
        tab_name: 추출할 탭 이름 (예: '개요', '진단', '치료', '스스로 돕는 법')

    Returns:
        dict: 탭 내 아코디언 항목들을 키-값 쌍으로 저장한 딕셔너리
    """
    tab_content = {}

    try:
        # 탭 이름과 step 클래스 매핑
        tab_mapping = {
            '개요': 'step1',
            '진단': 'step2',
            '치료': 'step3',
            '스스로 돕는 법': 'step4'
        }

        # step 클래스로 탭 찾기
        step_class = tab_mapping.get(tab_name)
        if not step_class:
            print(f"알 수 없는 탭 이름: '{tab_name}'")
            return tab_content

        # div.tab_tit.stepN 형태의 탭 찾기
        tab_selector = f'div.tab_tit.{step_class}'
        tab_div = page.locator(tab_selector).first

        if await tab_div.count() == 0:
            print(f"탭 '{tab_name}'을 찾을 수 없습니다 (selector: {tab_selector})")
            return tab_content

        # active 클래스 확인
        class_attr = await tab_div.get_attribute('class')
        is_active = 'active' in class_attr if class_attr else False

        if not is_active:
            # 비활성화된 탭이므로 클릭
            tab_link = tab_div.locator('a').first
            if await tab_link.count() > 0:
                await tab_link.click()
                await page.wait_for_timeout(1500)  # 탭 전환 대기
                print(f"탭 '{tab_name}' 클릭 완료")
            else:
                print(f"탭 '{tab_name}'의 링크를 찾을 수 없습니다")
                return tab_content
        else:
            print(f"탭 '{tab_name}'은 이미 활성화되어 있습니다")
        
        # 아코디언 항목들 추출 - 현재 표시되는 아코디언만 추출
        await page.wait_for_timeout(500)  # 탭 전환 완료 대기

        # 모든 아코디언을 찾고 visible한 것만 선택
        all_accordions = await page.query_selector_all('ul.accordi.disease_info')
        current_accordion = None

        for accordion in all_accordions:
            if await accordion.is_visible():
                current_accordion = accordion
                break

        if not current_accordion:
            print(f"  탭 '{tab_name}'의 아코디언을 찾을 수 없습니다")
            return tab_content

        # 1. 아코디언 상단의 텍스트/이미지 내용 추출 (div.box_sty06 찾기)
        try:
            # 아코디언의 부모 요소(tab_content)에서 div.box_sty06 찾기
            intro_element = await page.evaluate('''(accordion) => {
                const parent = accordion.parentElement;
                if (!parent) return null;

                // tab_content 내의 div.box_sty06 찾기
                const boxDiv = parent.querySelector('div.box_sty06');
                return boxDiv ? boxDiv.innerHTML : null;
            }''', current_accordion)

            if intro_element:
                # HTML을 텍스트로 변환
                intro_text = await page.evaluate('''(html) => {
                    const div = document.createElement('div');
                    div.innerHTML = html;
                    return div.innerText;
                }''', intro_element)

                if intro_text and intro_text.strip():
                    tab_content['__intro__'] = intro_text.strip()
                    print(f"    - [상단 내용]: {len(intro_text.strip())}자")
        except Exception as e:
            print(f"  상단 내용 추출 중 오류 (무시): {e}")

        # 2. 아코디언 항목들 추출
        accordion_items = await current_accordion.query_selector_all('li')
        print(f"  탭 '{tab_name}'의 아코디언 항목 {len(accordion_items)}개 발견")

        # 각 아코디언 항목의 제목과 내용 추출
        for item in accordion_items:
            try:
                # 제목 추출
                title_element = await item.query_selector('div.tit a')
                if not title_element:
                    continue

                title = await title_element.inner_text()
                title = re.sub(r'\s+', ' ', title).strip()
                # sr-only 텍스트 제거
                title = title.replace('내용 펼치기', '').replace('내용 접기', '').strip()

                # 내용 추출
                content_element = await item.query_selector('div.accordi_con')
                if not content_element:
                    continue

                # 아코디언이 열려있지 않으면 클릭하여 열기
                is_visible = await content_element.is_visible()
                if not is_visible:
                    await title_element.click()
                    await page.wait_for_timeout(800)

                # 내용 추출 (텍스트 + 표 + 이미지)
                item_data = {}

                # 1) 표(table) 먼저 확인 - 첫 번째 열을 키로 사용
                tables = await content_element.query_selector_all('table')
                has_tables = len(tables) > 0

                if has_tables:
                    tables_data = []
                    for table in tables:
                        # 표를 2차원 배열로 추출 (이미지도 포함)
                        table_rows = await table.evaluate('''(table) => {
                            const rows = Array.from(table.querySelectorAll('tr'));
                            return rows.map(row => {
                                const cells = Array.from(row.querySelectorAll('th, td'));
                                return cells.map(cell => {
                                    // 셀 내 이미지 확인
                                    const img = cell.querySelector('img');
                                    if (img) {
                                        const src = img.getAttribute('src');
                                        const alt = img.getAttribute('alt') || '';
                                        // 이미지가 있으면 [이미지: URL] 형태로 저장
                                        let imageSrc = src;
                                        if (src && src.startsWith('/')) {
                                            imageSrc = 'https://www.mentalhealth.go.kr' + src;
                                        } else if (src && !src.startsWith('http')) {
                                            imageSrc = 'https://www.mentalhealth.go.kr/' + src;
                                        }
                                        const text = cell.innerText.trim();
                                        // 텍스트가 있으면 함께 저장, 없으면 이미지만
                                        if (text) {
                                            return `[이미지: ${imageSrc}] ${text}`;
                                        } else {
                                            return `[이미지: ${imageSrc}]`;
                                        }
                                    }
                                    // 이미지가 없으면 일반 텍스트
                                    return cell.innerText.trim();
                                });
                            });
                        }''')

                        # 빈 행이 아닌 경우만 추가 (2D 배열 그대로 저장)
                        if table_rows and len(table_rows) > 0:
                            tables_data.append(table_rows)

                    if tables_data:
                        item_data['tables'] = tables_data

                # 2) 텍스트 내용 추출 (표 제외)
                if has_tables:
                    # 표가 있으면 표를 제외한 텍스트만 추출
                    text_content = await content_element.evaluate('''(element) => {
                        const clone = element.cloneNode(true);
                        // 모든 table 요소 제거
                        const tables = clone.querySelectorAll('table');
                        tables.forEach(table => table.remove());
                        return clone.innerText.trim();
                    }''')
                else:
                    # 표가 없으면 전체 텍스트 추출
                    text_content = await content_element.inner_text()
                    text_content = text_content.strip()

                if text_content:
                    item_data['text'] = text_content

                # 3) 이미지 정보 추출 (이 섹션에 속한 이미지만)
                # alt 텍스트는 다음과 같이 활용됨:
                # - AI 이미지 분석 시 힌트로 제공 (프롬프트에 포함)
                # - alt가 충분히 상세하면 AI 분석 생략하여 비용 절약 가능
                # - Vector DB 메타데이터에 포함하여 검색 품질 향상
                images = await content_element.query_selector_all('img')
                if images:
                    image_list = []
                    for img in images:
                        src = await img.get_attribute('src')
                        alt = await img.get_attribute('alt')  # HTML alt 속성 추출

                        if src:
                            # 상대 경로를 절대 경로로 변환
                            if src.startswith('/'):
                                src = f"https://www.mentalhealth.go.kr{src}"
                            elif not src.startswith('http'):
                                src = f"https://www.mentalhealth.go.kr/{src}"

                            # 이미지가 테이블 안에 있는지 확인
                            # location 정보는 transform 시 이미지 분석 전략 결정에 사용
                            is_in_table = await img.evaluate('''(img) => {
                                let parent = img.parentElement;
                                while (parent) {
                                    if (parent.tagName === 'TABLE') return true;
                                    if (parent.classList && parent.classList.contains('accordi_con')) break;
                                    parent = parent.parentElement;
                                }
                                return false;
                            }''')

                            # 이미지 주변의 <strong> 태그에서 제목/캡션 추출
                            # 이미지 위아래에 있는 strong 태그를 찾아서 제목으로 사용
                            # div로 감싸져 있으면 그 div 안에서만 검색
                            caption = await img.evaluate('''(img) => {
                                let caption = '';
                                
                                // 이미지가 div로 감싸져 있는지 확인하고, 가장 가까운 div 컨테이너 찾기
                                let container = img.parentElement;
                                if (!container) return '';
                                
                                // div로 감싸져 있으면 그 div를 컨테이너로 사용
                                while (container && container.tagName !== 'DIV' && container.tagName !== 'BODY') {
                                    container = container.parentElement;
                                }
                                
                                // div 컨테이너를 찾지 못했으면 부모 요소 사용
                                if (!container || container.tagName === 'BODY') {
                                    container = img.parentElement;
                                }
                                
                                // 이미지의 바로 위쪽 형제 요소 확인 (최대 2개까지만)
                                let prevSibling = img.previousElementSibling;
                                let prevCount = 0;
                                while (prevSibling && prevCount < 2) {
                                    // div 컨테이너를 벗어나면 중단
                                    if (container && !container.contains(prevSibling)) {
                                        break;
                                    }
                                    
                                    // strong 태그 직접 확인
                                    if (prevSibling.tagName === 'STRONG') {
                                        const text = prevSibling.innerText.trim();
                                        if (text && text.length > 0 && text.length < 100) {
                                            caption = text;
                                            break;
                                        }
                                    }
                                    // 이전 형제 요소 내부의 strong 태그 확인 (가장 마지막 것만)
                                    const strongs = prevSibling.querySelectorAll('strong');
                                    if (strongs.length > 0) {
                                        const text = strongs[strongs.length - 1].innerText.trim();
                                        if (text && text.length > 0 && text.length < 100) {
                                            caption = text;
                                            break;
                                        }
                                    }
                                    prevSibling = prevSibling.previousElementSibling;
                                    prevCount++;
                                }
                                
                                // 위쪽에서 찾지 못했으면 아래쪽 확인 (최대 2개까지만)
                                if (!caption) {
                                    let nextSibling = img.nextElementSibling;
                                    let nextCount = 0;
                                    while (nextSibling && nextCount < 2) {
                                        // div 컨테이너를 벗어나면 중단
                                        if (container && !container.contains(nextSibling)) {
                                            break;
                                        }
                                        
                                        // strong 태그 직접 확인
                                        if (nextSibling.tagName === 'STRONG') {
                                            const text = nextSibling.innerText.trim();
                                            if (text && text.length > 0 && text.length < 100) {
                                                caption = text;
                                                break;
                                            }
                                        }
                                        // 다음 형제 요소 내부의 strong 태그 확인 (가장 첫 번째 것만)
                                        const strongs = nextSibling.querySelectorAll('strong');
                                        if (strongs.length > 0) {
                                            const text = strongs[0].innerText.trim();
                                            if (text && text.length > 0 && text.length < 100) {
                                                caption = text;
                                                break;
                                            }
                                        }
                                        nextSibling = nextSibling.nextElementSibling;
                                        nextCount++;
                                    }
                                }
                                
                                return caption;
                            }''')

                            # alt와 caption이 둘 다 없는 이미지는 제외
                            alt_text = alt or ''
                            caption_text = caption or ''
                            
                            if alt_text or caption_text:
                                image_list.append({
                                    'url': src,
                                    'alt': alt_text,
                                    'caption': caption_text,  # 원본 캡션 별도 저장
                                    'location': 'table' if is_in_table else 'text'
                                })

                    if image_list:
                        item_data['images'] = image_list

                # 추출한 제목과 내용을 딕셔너리에 추가
                if item_data:
                    # 표나 이미지가 있으면 dict로, 텍스트만 있으면 단순 문자열로 저장
                    if 'tables' in item_data or 'images' in item_data:
                        tab_content[title] = item_data
                    elif 'text' in item_data:
                        tab_content[title] = item_data['text']
                    else:
                        tab_content[title] = item_data

                    text_len = len(item_data.get('text', ''))
                    table_count = len(item_data.get('tables', []))
                    image_count = len(item_data.get('images', []))
                    info_parts = [f"{text_len}자"]
                    if table_count > 0:
                        info_parts.append(f"표 {table_count}개")
                    if image_count > 0:
                        info_parts.append(f"이미지 {image_count}개")
                    print(f"    - {title}: " + ", ".join(info_parts))
            except Exception as e:
                print(f"  아코디언 항목 추출 중 오류: {e}")
                continue
    except Exception as e:
        print(f"탭 '{tab_name}' 추출 중 오류: {e}")
    
    return tab_content


# ==============================
# 4단계: 개별 질환 상세 페이지 정보 추출
# ==============================
async def extract_disease_detail(page, disease_url):
    """
    개별 질환 상세 페이지에서 모든 정보를 추출하는 함수

    Args:
        page: Playwright 페이지 객체
        disease_url: 질환 상세 페이지 URL

    Returns:
        dict: 질환명, 각 탭별 내용(섹션), 이미지 URL 리스트를 포함한 딕셔너리
    """
    # 임시 데이터 딕셔너리
    temp_data = {}

    try:
        # 질환 상세 페이지로 이동
        await page.goto(disease_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)

        # 질환명 추출
        name_element = page.locator('div.tbl_tit h2').first
        disease_name = None
        if await name_element.count() > 0:
            name_text = await name_element.inner_text()
            if name_text and name_text.strip():
                disease_name = name_text.strip()

        # 각 탭의 내용 추출 (개요, 진단, 치료, 스스로 돕는 법)
        # 이미지는 각 섹션 내부에 저장되므로 최상위 '이미지' 배열은 생성하지 않음
        tabs = ['개요', '진단', '치료', '스스로 돕는 법']

        for tab_name in tabs:
            try:
                tab_content = await extract_tab_content(page, tab_name)
                temp_data[tab_name] = tab_content
            except Exception as e:
                print(f"탭 '{tab_name}' 추출 실패: {e}")
                temp_data[tab_name] = {}

    except Exception as e:
        print(f"질환 상세 페이지 추출 중 오류 ({disease_url}): {e}")

    # 질환명이 제일 앞에 오도록 순서를 보장하여 딕셔너리 생성
    disease_data = {}
    if disease_name:
        disease_data['질환명'] = disease_name

    # 나머지 데이터 추가
    disease_data.update(temp_data)

    return disease_data


# ==============================
# 5단계: 메인 크롤링 프로세스
# ==============================
async def main():
    """
    메인 크롤링 함수

    전체 크롤링 프로세스를 관리:
    1. 질환 목록 페이지 접속
    2. 한 페이지에서 모든 질환 링크 수집 (상단 테이블에 모든 질환 목록 포함)
    3. 각 질환 상세 페이지 크롤링하면서 하나씩 파일에 저장 (append)
    4. JSON 파일로 저장 (UTF-8 인코딩)

    Returns:
        int: 크롤링된 질환 개수
    """
    base_url = "https://www.mentalhealth.go.kr/portal/disease/diseaseList.do"

    # 출력 파일 경로 설정 (프로젝트 루트의 data/raw/)
    project_root = Path(__file__).parent.parent.parent.parent
    output_file = project_root / 'data' / 'raw' / 'diseases_info.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 기존 파일이 있으면 백업
    if output_file.exists():
        backup_file = output_file.with_suffix('.json.backup')
        import shutil
        shutil.copy2(output_file, backup_file)
        print(f"기존 파일 백업: {backup_file}")

    # 새 파일 시작 (빈 배열로 초기화)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

    # Playwright 브라우저 초기화
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # 1. 질환 목록 페이지로 이동
            print(f"질환 목록 페이지 접속 중: {base_url}")
            await page.goto(base_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # 2. 한 페이지에서 모든 질환 링크 수집 (상단 테이블에 모든 질환 포함)
            print("\n질환 링크 수집 중...")
            all_disease_links = await crawl_disease_list(page)
            print(f"총 {len(all_disease_links)}개 질환 발견\n")

            # 3. 각 질환의 상세 정보 추출 및 즉시 저장
            success_count = 0
            for idx, disease_link in enumerate(all_disease_links, 1):
                print(f"\n[{idx}/{len(all_disease_links)}] {disease_link['name']} 크롤링 중...")

                try:
                    disease_data = await extract_disease_detail(page, disease_link['url'])

                    # 질환명이 없으면 링크에서 가져온 이름 사용
                    if not disease_data.get('질환명'):
                        disease_data['질환명'] = disease_link['name']

                    # 파일에서 기존 데이터 읽기
                    with open(output_file, 'r', encoding='utf-8') as f:
                        all_data = json.load(f)

                    # 새 데이터 추가
                    all_data.append(disease_data)

                    # 파일에 다시 저장
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, ensure_ascii=False, indent=2)

                    success_count += 1
                    print(f"✓ 저장 완료 ({success_count}/{len(all_disease_links)})")

                except Exception as e:
                    print(f"✗ 크롤링 실패: {e}")

                # API 부하 방지를 위한 대기
                await page.wait_for_timeout(1000)

        finally:
            # 브라우저 종료
            await browser.close()

    print(f"\n크롤링 완료! 총 {success_count}개 질환 데이터 저장")
    print(f"저장 위치: {output_file}")

    return success_count


# ==============================
# 실행 진입점
# ==============================
if __name__ == "__main__":
    asyncio.run(main())
