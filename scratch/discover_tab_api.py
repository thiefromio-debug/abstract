import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Capture all requests to find the right one
        async def handle_request(request):
            if "wips" in request.url:
                print(f"[Request]: {request.method} {request.url}")
                if request.post_data:
                    print(f"  [Post Data]: {request.post_data}")

        async def handle_response(response):
            if "wips" in response.url and response.request.resource_type in ["fetch", "xhr"]:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = await response.json()
                        data_str = json.dumps(data, ensure_ascii=False)
                        if len(data_str) > 1000:
                            print(f"[Response from {response.url}]: {data_str[:500]}...")
                except:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        target_url = "http://newsd.wips.co.kr/wipslink/api/djpdshtm.wips?skey=2725040000516"
        print(f"Navigating to {target_url}")
        await page.goto(target_url, wait_until="networkidle")
        
        # Click "발명의 설명" tab. 
        # Based on subagent's coordinates or common patterns, let's try to find it by text.
        try:
            print("Clicking '발명의 설명' tab...")
            # '발명의 설명' 혹은 '상세한 설명'
            await page.click('text="발명의 설명"', timeout=5000)
            print("Clicked!")
        except:
            print("Could not find '발명의 설명' tab by text, trying coordinates or waiting...")
            # Sometimes it's inside an iframe or uses different text
            await page.mouse.click(240, 186) # coordinates from subagent

        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
