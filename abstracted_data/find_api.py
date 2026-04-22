import asyncio
import json
import re
from playwright.async_api import async_playwright

async def run():
    found_apis = []
    all_responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        async def handle_response(response):
            if response.request.resource_type in ["fetch", "xhr"]:
                url = response.url
                try:
                    text = await response.text()
                    all_responses.append({
                        "url": url,
                        "method": response.request.method,
                        "headers": response.request.headers,
                        "post_data": response.request.post_data,
                        "body": text
                    })
                except:
                    pass

        page.on("response", handle_response)

        target_url = "http://newsd.wips.co.kr/wipslink/api/djpdshtm.wips?skey=2725040000516"
        print(f"접속 중: {target_url}")

        await page.goto(target_url, wait_until="networkidle")

        # ']' 키를 두 번 눌러 '상세 설명'으로 이동 유도 (메모리 힌트)
        print("']' 키를 눌러 상세 설명 페이지 로딩 유도...")
        await page.keyboard.press("]")
        await asyncio.sleep(2)
        await page.keyboard.press("]")
        await asyncio.sleep(5) # 로딩 대기

        # 수집된 응답들 분석
        # [0001] 또는 【0001】 또는 {0001} 등 다양한 패턴 고려
        target_pattern = re.compile(r"[\[【{]\d{4}[\]】}]")

        for res in all_responses:
            if target_pattern.search(res["body"]):
                print(f"!!! 패턴 발견 !!! : {res['url']}")
                found_apis.append(res)

        if found_apis:
            output = []
            for api in found_apis:
                api_copy = api.copy()
                api_copy["body_preview"] = api["body"][:2000]
                # HTML 태그 제거 후 텍스트만 추출해서 패턴 확인
                clean_text = re.sub('<[^<]+?>', '', api["body"])
                api_copy["clean_text_preview"] = clean_text[:2000]
                del api_copy["body"]
                output.append(api_copy)

            with open("found_api_details.json", "w", encoding="utf-8") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            print(f"\n패턴 발견 API {len(found_apis)}개 저장됨.")
        else:
            print("\n패턴 발견된 API 없음. (키 입력 후 재시도)")

        # 전체 응답 백업 (디버깅용)
        with open("all_xhr_responses.json", "w", encoding="utf-8") as f:
            json.dump(all_responses, f, indent=4, ensure_ascii=False)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
