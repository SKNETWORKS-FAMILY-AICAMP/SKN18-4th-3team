import json
import asyncio
import re
import sys
from playwright.async_api import async_playwright
from pathlib import Path

# 출력 버퍼링 비활성화 (크롤링 진행 상황 실시간 출력)
sys.stdout.reconfigure(line_buffering=True)


# ==============================
# 1단계: 총 페이지 수 추출
# ==============================
async def get_total_pages(page):
    """
    FAQ 페이지의 총 페이지 수를 추출하는 함수
    
    Args:
        page: Playwright 페이지 객체
        
    Returns:
        int: 총 페이지 수
    """
    try:
        # 페이지네이션 요소 찾기
        paging = page.locator('ul.paging').first
        if await paging.count() == 0:
            return 1
        
        # 페이지 번호 링크들 찾기
        page_links = await paging.locator('li.num a').all()
        if not page_links:
            return 1
        
        # 마지막 페이지 번호 찾기
        max_page = 1
        for link in page_links:
            text = await link.inner_text()
            onclick = await link.get_attribute('onclick')
            if onclick and 'linkPage' in onclick:
                # onclick="linkPage(10);return false;" 형식에서 페이지 번호 추출
                match = re.search(r'linkPage\((\d+)\)', onclick)
                if match:
                    page_num = int(match.group(1))
                    max_page = max(max_page, page_num)
        
        return max_page
    except Exception as e:
        print(f"총 페이지 수 추출 중 오류: {e}")
        return 1


# ==============================
# 2단계: 페이지 이동
# ==============================
async def navigate_to_faq_page(page, page_number):
    """
    특정 FAQ 페이지로 이동하는 함수
    
    Args:
        page: Playwright 페이지 객체
        page_number: 이동할 페이지 번호
        
    Returns:
        bool: 페이지 이동 성공 여부
    """
    try:
        # JavaScript 함수 호출로 페이지 이동
        await page.evaluate(f'linkPage({page_number})')
        await page.wait_for_timeout(2000)  # 페이지 로드 대기
        
        # FAQ 항목이 로드되었는지 확인
        await page.wait_for_selector('span.faq-q, span.faq-keyword', timeout=5000)
        return True
    except Exception as e:
        print(f"페이지 {page_number}로 이동 실패: {e}")
        return False


# ==============================
# 3단계: FAQ 항목 추출
# ==============================
async def extract_faq_items(page):
    """
    현재 페이지의 모든 FAQ 항목을 추출하는 함수

    페이지 구조:
    <ul class="accordi_list">
      <li class="trigger">
        <div class="tit">
          <a href="#">
            <span class="faq-keyword">키워드</span>
            <span class="faq-title">
              <span class="faq-q">Q</span>질문 텍스트
            </span>
          </a>
        </div>
        <div class="accordi_con">
          <span class="faq-a">A</span>
          <span class="faq-com">답변 텍스트</span>
        </div>
      </li>
    </ul>

    Args:
        page: Playwright 페이지 객체

    Returns:
        list: FAQ 항목 딕셔너리 리스트 (keyword, question, answer)
    """
    faq_items = []

    try:
        # FAQ 항목 컨테이너 찾기: ul.accordi.faq 아래의 모든 li 요소들
        # (li.trigger 클래스는 첫 번째 항목에만 있고, 나머지는 클래스가 없음)
        faq_list = await page.query_selector('ul.accordi.faq')
        if not faq_list:
            print("  경고: FAQ 리스트 컨테이너를 찾을 수 없습니다.")
            return faq_items

        faq_containers = await faq_list.query_selector_all(':scope > li')

        if not faq_containers:
            print("  경고: FAQ 항목을 찾을 수 없습니다.")
            return faq_items

        for container in faq_containers:
            try:
                # 키워드 추출
                keyword = None
                keyword_element = await container.query_selector('span.faq-keyword')
                if keyword_element:
                    keyword = await keyword_element.inner_text()
                    keyword = keyword.strip() if keyword else None

                # 질문 추출: faq-title의 텍스트에서 'Q' 제거
                question = None
                question_element = await container.query_selector('span.faq-title')
                if question_element:
                    question_text = await question_element.inner_text()
                    # 'Q' 제거 및 공백 정리
                    question = question_text.replace('Q', '', 1).strip() if question_text else None

                # 답변 추출: faq-com의 텍스트
                answer = None
                answer_element = await container.query_selector('span.faq-com')
                if answer_element:
                    # 답변이 보이지 않으면 아코디언 열기
                    is_visible = await answer_element.is_visible()
                    if not is_visible:
                        # div.tit > a 클릭하여 아코디언 열기
                        clickable = await container.query_selector('div.tit > a')
                        if clickable:
                            await clickable.click()
                            await page.wait_for_timeout(300)  # 애니메이션 대기

                    # 답변 텍스트 추출
                    answer = await answer_element.inner_text()
                    answer = answer.strip() if answer else None

                # FAQ 항목이 완전한 경우만 추가 (질문과 답변이 모두 있어야 함)
                if question and answer:
                    faq_item = {
                        'question': question,
                        'answer': answer
                    }
                    # 키워드가 있는 경우에만 추가
                    if keyword:
                        faq_item['keyword'] = keyword

                    faq_items.append(faq_item)

            except Exception as e:
                print(f"  FAQ 항목 추출 중 오류: {e}")
                continue

    except Exception as e:
        print(f"  FAQ 항목 추출 중 전체 오류: {e}")

    return faq_items


# ==============================
# 4단계: 메인 크롤링 프로세스
# ==============================
async def main():
    """
    메인 FAQ 크롤링 함수
    
    전체 크롤링 프로세스를 관리:
    1. FAQ 목록 페이지 접속
    2. 총 페이지 수 확인
    3. 각 페이지를 순회하며 FAQ 항목 추출
    4. 10개마다 JSON 파일에 append
    5. 최종 저장
    
    Returns:
        int: 크롤링된 FAQ 개수
    """
    base_url = "https://www.mentalhealth.go.kr/portal/faq/portalFaqList.do"
    
    # 출력 파일 경로 설정 (프로젝트 루트의 data/raw/)
    project_root = Path(__file__).parent.parent.parent.parent
    output_file = project_root / 'data' / 'raw' / 'diseases_faq.json'
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
            # 1. FAQ 목록 페이지로 이동
            print(f"FAQ 목록 페이지 접속 중: {base_url}")
            await page.goto(base_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # 2. 총 페이지 수 확인
            print("\n총 페이지 수 확인 중...")
            total_pages = await get_total_pages(page)
            print(f"총 {total_pages}개 페이지 발견\n")
            
            # 3. 각 페이지를 순회하며 FAQ 항목 추출
            total_count = 0
            buffer = []  # 10개씩 모아서 저장할 버퍼
            
            for page_num in range(1, total_pages + 1):
                print(f"\n[페이지 {page_num}/{total_pages}] 크롤링 중...")
                
                # 페이지 이동
                if page_num > 1:
                    success = await navigate_to_faq_page(page, page_num)
                    if not success:
                        print(f"페이지 {page_num} 이동 실패, 건너뜀")
                        continue
                
                # FAQ 항목 추출
                faq_items = await extract_faq_items(page)
                print(f"  {len(faq_items)}개 FAQ 항목 발견")
                
                # 버퍼에 추가
                buffer.extend(faq_items)
                total_count += len(faq_items)
                
                # 10개마다 파일에 저장
                while len(buffer) >= 10:
                    # 파일에서 기존 데이터 읽기
                    with open(output_file, 'r', encoding='utf-8') as f:
                        all_data = json.load(f)
                    
                    # 10개 추가
                    all_data.extend(buffer[:10])
                    buffer = buffer[10:]
                    
                    # 파일에 다시 저장
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"  ✓ 10개 저장 완료 (총 {len(all_data)}개)")
                
                # API 부하 방지를 위한 대기
                await page.wait_for_timeout(1000)
            
            # 남은 버퍼 데이터 저장
            if buffer:
                with open(output_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
                
                all_data.extend(buffer)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ 남은 {len(buffer)}개 저장 완료")
        
        finally:
            # 브라우저 종료
            await browser.close()
    
    print(f"\n크롤링 완료! 총 {total_count}개 FAQ 데이터 저장")
    print(f"저장 위치: {output_file}")
    
    return total_count


# ==============================
# 실행 진입점
# ==============================
if __name__ == "__main__":
    asyncio.run(main())
