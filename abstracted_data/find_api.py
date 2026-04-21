import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # 브라우저 실행 (headless=False로 설정하여 실제 동작 확인 가능)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 응답 가로채기 설정
        async def handle_response(response):
            # 주로 API는 'fetch' 또는 'xhr' 타입임
            if response.request.resource_type in ["fetch", "xhr"]:
                url = response.url
                try:
                    content_type = response.headers.get("content-type", "")
                    
                    # JSON 데이터이거나 URL에 'api' 또는 'wips'가 포함된 요청을 가로챔
                    if "application/json" in content_type or "wips" in url:
                        print(f"\n{'='*80}")
                        print(f"[API URL Found]: {url}")
                        print(f"[Method]: {response.request.method}")
                        
                        # 1. 나중에 requests 라이브러리에서 사용할 Headers 출력
                        print("\n[Request Headers - 직접 호출 시 필요]:")
                        print(json.dumps(response.request.headers, indent=2, ensure_ascii=False))
                        
                        # 2. POST 요청인 경우 데이터 확인
                        if response.request.post_data:
                            print(f"\n[Post Data]: {response.request.post_data}")

                        # 3. 실제 들어오는 JSON 데이터의 구조 확인
                        data = await response.json()
                        print("\n[Response Data Preview (First 500 chars)]:")
                        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
                        print(f"{'='*80}\n")
                except Exception:
                    pass

        # 응답 이벤트 리스너 등록
        page.on("response", handle_response)

        # 대상 URL로 이동
        print("페이지 접속 중...")
        target_url = "http://newsd.wips.co.kr/wipslink/api/djpdshtm.wips?skey=2725040000516"
        await page.goto(target_url, wait_until="networkidle")

        # 모든 데이터가 로드될 수 있도록 충분히 대기
        await page.wait_for_timeout(10000)

        print("탐색 종료.")
        await browser.close()

asyncio.run(run())
