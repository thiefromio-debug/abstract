import asyncio
import json
import os
import sys
import re
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

async def extract_description():
    if not os.path.exists("api_data"):
        os.makedirs("api_data")

    with open("web_address.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"총 {len(urls)}개의 URL을 재처리합니다.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        for i, url in enumerate(urls, 1):
            skey = url.split("skey=")[-1]
            print(f"[{i}/{len(urls)}] 처리 중: {skey}...")
            
            page = await context.new_page()
            
            # API 데이터를 담을 리스트 (가장 긴 것을 선택하기 위함)
            potential_json_data = []

            async def handle_response(response):
                if response.request.resource_type in ["fetch", "xhr"]:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            data = await response.json()
                            data_str = json.dumps(data, ensure_ascii=False)
                            # 텍스트가 충분히 길고 설명 관련 키워드가 있는지 확인
                            if len(data_str) > 1000:
                                potential_json_data.append(data_str)
                    except:
                        pass

            page.on("response", handle_response)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # '발명의 설명' 탭 클릭 시도
                tabs = ["발명의 설명", "상세한 설명", "Description", "発明の詳細な説明"]
                clicked = False
                for tab_text in tabs:
                    try:
                        tab_element = await page.get_by_text(tab_text).first
                        if await tab_element.is_visible():
                            await tab_element.click()
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    # 좌표로 클릭 시도 (여러 좌표 시도)
                    await page.mouse.click(160, 180) # JP/KR 탭 위치
                
                await page.wait_for_timeout(4000)

                # 1. JSON API 데이터 우선 확인
                if potential_json_data:
                    # 가장 긴 데이터를 상세 설명으로 간주
                    best_json = max(potential_json_data, key=len)
                    # 만약 JSON 내부에 특정 키(description 등)가 있다면 그것만 추출
                    try:
                        data_obj = json.loads(best_json)
                        if "resultData" in data_obj and "description" in data_obj["resultData"]:
                            content = data_obj["resultData"]["description"]
                        elif "description" in data_obj:
                            content = data_obj["description"]
                        else:
                            content = best_json
                    except:
                        content = best_json
                    
                    file_path = f"api_data/{skey}.txt"
                    with open(file_path, "w", encoding="utf-8") as out:
                        out.write(content)
                    print(f"  => API 데이터 저장 완료")
                
                else:
                    # 2. DOM에서 텍스트 추출 (Fallback)
                    # 상세 설명 섹션으로 추정되는 키워드들
                    keywords = [
                        "발명의 상세한 설명", "상세한 설명", "발명의 설명", 
                        "発明の詳細な説明", "発明の実施の形態", 
                        "DETAILED DESCRIPTION", "Description of the Invention"
                    ]
                    
                    body_text = await page.evaluate("() => document.body.innerText")
                    found_kw = None
                    for kw in keywords:
                        if kw.upper() in body_text.upper():
                            found_kw = kw
                            break
                    
                    if found_kw:
                        # 해당 키워드 이후의 텍스트를 추출 (너무 앞의 메뉴 등 제외)
                        idx = body_text.upper().find(found_kw.upper())
                        content = body_text[idx:]
                        file_path = f"api_data/{skey}.txt"
                        with open(file_path, "w", encoding="utf-8") as out:
                            out.write(content)
                        print(f"  => DOM 추출 저장 완료 (Keyword: {found_kw})")
                    else:
                        # 키워드가 없어도 본문에서 가장 긴 텍스트 덩어리 추출 시도
                        print("  => 데이터를 찾지 못했습니다.")

            except Exception as e:
                print(f"  => 에러 발생: {e}")
            
            finally:
                await page.close()

        await browser.close()
    print("\n모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    asyncio.run(extract_description())
