import asyncio
import os
import sys

# Set encoding to utf-8 for stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

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
            # Wait for the element to be visible
            await page.wait_for_selector('text="발명의 설명"', timeout=5000)
            await page.click('text="발명의 설명"')
        except:
            await page.mouse.click(240, 186)
        
        await page.wait_for_timeout(5000)
        
        text = await page.evaluate("() => document.body.innerText")
        
        with open("scratch/page_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print(f"Saved page text to scratch/page_text.txt (length: {len(text)})")
        
        # Look for description sections
        keywords = ["발명의 상세한 설명", "Detailed Description", "발명의 설명", "상세한 설명"]
        found = False
        for kw in keywords:
            if kw in text:
                print(f"Found keyword: {kw}")
                found = True
                break
        
        if not found:
            print("No keywords found in text.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
