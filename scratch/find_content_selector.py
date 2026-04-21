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
            await page.mouse.click(162, 180) # Revised X coordinate from subagent (162)
        
        await page.wait_for_timeout(3000)
        
        # List major divs
        divs = await page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('div').forEach(div => {
                if (div.innerText && div.innerText.length > 500) {
                    results.push({
                        id: div.id,
                        className: div.className,
                        textLength: div.innerText.length,
                        preview: div.innerText.substring(0, 100)
                    });
                }
            });
            return results;
        }""")
        
        for div in divs:
            print(f"ID: {div['id']}, Class: {div['className']}, Length: {div['textLength']}")
            print(f"  Preview: {div['preview']}...")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
