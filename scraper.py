import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def scrape_patent_data(input_file):
    output_dir = "extracted_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        if not os.path.exists(input_file): return
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]

        for url in urls:
            skey = url.split('skey=')[-1]
            print(f"\n[Processing] skey: {skey}")
            
            try:
                driver.get(url)
                time.sleep(10)

                actions = ActionChains(driver)

                # --- 텍스트 수집 루프 ---
                # 0: 초기 상태 (보통 요약/서지사항)
                # 1: '[' 입력 후 (청구항 탭)
                # 2: '[' 또 입력 후 (상세 설명 탭)
                texts = []
                for i in range(3):
                    # 스크롤을 내려서 레이지 로딩 및 컨텐츠 활성화 유도
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")

                    # iframe이 있을 경우를 대비해 모든 프레임의 텍스트 수집 시도
                    t = driver.execute_script("return document.body.innerText")

                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for frame in iframes:
                        try:
                            driver.switch_to.frame(frame)
                            t += "\n" + driver.find_element(By.TAG_NAME, "body").text
                            driver.switch_to.default_content()
                        except:
                            driver.switch_to.default_content()

                    texts.append(t)
                    print(f"Captured state {i}, text length: {len(t)}")

                    actions.send_keys("[").perform()
                    time.sleep(12) # 탭 전환 및 데이터 로딩 대기 (충분히)

                claims_content = ""
                desc_content = ""

                # 1. 상세 설명 추출 (다양한 언어 마커 대응)
                desc_markers = [
                    r"【0001】", r"【技術分野】", r"기술분야", r"배경기술", r"발명의\s*내용",
                    r"BACKGROUND OF THE INVENTION", r"TECHNICAL FIELD", r"DETAILED DESCRIPTION"
                ]

                for t in texts:
                    for marker_pattern in desc_markers:
                        match = re.search(marker_pattern, t, re.IGNORECASE)
                        if match:
                            content = t[match.start():]
                            # 푸터 및 불필요한 영역 제거
                            for end_marker in ["Copyright", "help@wips.co.kr", "카톡상담", "고객센터", "이용약관"]:
                                content = content.split(end_marker)[0]

                            if len(content.strip()) > len(desc_content.strip()):
                                desc_content = content.strip()
                            break

                # 2. 청구항 추출
                claims_markers = [
                    r"【請求項1】", r"청구항\s*1항", r"\[Claim\s*1\]", r"CLAIMS", r"청구범위"
                ]

                for t in texts:
                    for marker_pattern in claims_markers:
                        match = re.search(marker_pattern, t, re.IGNORECASE)
                        if match:
                            content = t[match.start():]
                            # 상세 설명 섹션이나 다음 탭 데이터에서 자르기
                            for end_marker in ["【0001】", "【技術分野】", "기술분야", "배경기술", "발명의 설명", "문헌전체", "특허분류코드", "Copyright"]:
                                content = content.split(end_marker)[0]

                            if len(content.strip()) > len(claims_content.strip()):
                                claims_content = content.strip()
                            break

                # 저장
                save_path = os.path.join(output_dir, f"{skey}.txt")
                with open(save_path, "w", encoding="utf-8") as out_f:
                    out_f.write(f"=== PATENT SKEY: {skey} ===\n\n")
                    out_f.write("="*30 + "\n=== CLAIMS (청구항) ===\n" + "="*30 + "\n\n")
                    out_f.write(claims_content if claims_content else "청구항을 추출하지 못했습니다.")
                    out_f.write("\n\n" + "="*30 + "\n=== DETAILED DESCRIPTION (상세 설명) ===\n" + "="*30 + "\n\n")
                    out_f.write(desc_content if desc_content else "상세 설명을 추출하지 못했습니다.")

                print(f"Saved: {save_path}")

            except Exception as e:
                print(f"Error processing {skey}: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_patent_data("web_address.txt")
