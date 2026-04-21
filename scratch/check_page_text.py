import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        target_url = "http://newsd.wips.co.kr/wipslink/api/djpdshtm.wips?skey=2725040000516"
        print(f"Navigating to {target_url}")
        await page.goto(target_url, wait_until="networkidle")
        
        print("Clicking '발명의 설명' tab...")
        try:
            await page.click('text="발명의 설명"', timeout=5000)
        except:
            await page.mouse.click(240, 186)
        
        await page.wait_for_timeout(3000)
        
        # Get all text content
        content = await page.content()
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(content)
        
        text = await page.evaluate("() => document.body.innerText")
        print(f"Page text length: {len(text)}")
        print(f"Preview: {text[:1000]}")
        
        if "발명의 상세한 설명" in text or "Detailed Description" in text:
            print("Found '발명의 상세한 설명' in page text!")
            # Find the index
            idx = text.find("발명의 상세한 설명")
            if idx == -1: idx = text.find("Detailed Description")
            print(f"Snippet: {text[idx:idx+500]}")
        else:
            print("Could not find description in page text.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
