import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run():
    if not os.path.exists("api_data"):
        os.makedirs("api_data")

    with open("web_address.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()][:3]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        for url in urls:
            print(f"Processing: {url}")
            skey = url.split("skey=")[-1]
            page = await context.new_page()
            
            description_data = []

            async def handle_response(response):
                if response.request.resource_type in ["fetch", "xhr"]:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            data = await response.json()
                            data_str = json.dumps(data, ensure_ascii=False)
                            # 상세한 설명, Detailed Description, 혹은 특징적인 키워드 탐색
                            if "발명의 상세한 설명" in data_str or "Detailed Description" in data_str or "발명의 설명" in data_str:
                                description_data.append(data)
                                print(f"  [Found potential description data in {response.url}]")
                    except:
                        pass

            page.on("response", handle_response)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000) # 추가 로딩 대기
            except Exception as e:
                print(f"  [Error loading {url}: {e}]")
            
            if description_data:
                # 가장 큰 데이터를 상세 설명으로 간주 (보통 텍스트가 많으므로)
                best_data = max(description_data, key=lambda x: len(json.dumps(x)))
                with open(f"api_data/{skey}.txt", "w", encoding="utf-8") as out:
                    out.write(json.dumps(best_data, indent=2, ensure_ascii=False))
                print(f"  [Saved to api_data/{skey}.txt]")
            else:
                print(f"  [Description data not found for {skey}]")
            
            await page.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
