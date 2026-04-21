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
    # 저장 경로 설정 (상대 경로)
    output_dir = "extracted_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 웹드라이버 설정
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # 브라우저 창을 띄우지 않으려면 주석 처리
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    stats = {"success": 0, "failure": 0}
    try:
        if not os.path.exists(input_file):
            print(f"파일을 찾을 수 없습니다: {input_file}")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]

        print(f"Total URLs to process: {len(urls)}")

        for url in urls:
            skey = url.split('skey=')[-1]
            print(f"\n[Processing] skey: {skey}")
            print(f"URL: {url}")

            driver.get(url)
            wait = WebDriverWait(driver, 20)
            
            try:
                # 1. 페이지 로딩 대기
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except TimeoutException:
                    print(f"Warning: Timeout waiting for page body ({skey})")

                time.sleep(3) # SPA 앱의 안정적인 초기 로딩을 위해 충분히 대기

                # 2. ']' 키 입력 (두 번 입력하여 상세 설명으로 이동)
                actions = ActionChains(driver)
                print("Sending ']' key (1/2) for Claims/Description transition...")
                actions.send_keys("]").perform()
                time.sleep(2)

                print("Sending ']' key (2/2) for Detailed Description transition...")
                actions.send_keys("]").perform()
                time.sleep(4) # 상세 설명 컨텐츠 로딩 대기 (충분히 대기)

                # 3. 상세 설명 추출 시도
                desc_text = ""

                # 다양한 국가/구조별 Selector 정의
                # devDescriptionView: 일반적인 해외 특허 상세 설명
                # devFullTextView: 전문 보기 영역
                # dkr (한국)의 경우 특정 ID가 다를 수 있음
                selectors = [
                    (By.ID, "devDescriptionView"),
                    (By.ID, "devFullTextView"),
                    (By.ID, "devClaimView"), # 가끔 여기에 같이 나오는 경우 대비
                    (By.CLASS_NAME, "viewmode"),
                    (By.CSS_SELECTOR, ".content_inner"),
                ]

                for by, value in selectors:
                    try:
                        elements = driver.find_elements(by, value)
                        for element in elements:
                            text = element.text.strip()
                            # 【XXXX】 패턴이나 유의미한 길이가 있는지 확인
                            if len(text) > 200:
                                desc_text = text
                                print(f"Found content using selector: {value}")
                                break
                        if desc_text: break
                    except:
                        continue

                # 4. Fallback: 특정 패턴(【0001】 등)을 포함하는 단락들 직접 수집
                if not desc_text or len(desc_text) < 100:
                    print("Attempting fallback pattern-based extraction...")
                    # num 속성이 있거나 【00...】 패턴을 포함하는 p 태그 검색
                    p_elements = driver.find_elements(By.XPATH, "//p[@num] | //p[contains(text(), '【')] | //div[contains(@class, 'content')]//p")
                    collected_lines = []
                    for p in p_elements:
                        t = p.text.strip()
                        if t:
                            collected_lines.append(t)

                    if collected_lines:
                        desc_text = "\n\n".join(collected_lines)
                        print(f"Extracted {len(collected_lines)} paragraphs via fallback.")

                if not desc_text or len(desc_text) < 100:
                    desc_text = "상세 설명 정보를 추출하지 못했습니다. (페이지 구조가 다르거나 로딩 실패)"
                    # 디버깅용: 현재 페이지의 텍스트 일부 출력
                    # print("Page snippet:", driver.find_element(By.TAG_NAME, "body").text[:200])

                # 5. 파일 저장
                save_path = os.path.join(output_dir, f"{skey}.txt")
                with open(save_path, "w", encoding="utf-8") as out_f:
                    out_f.write(f"=== PATENT SKEY: {skey} ===\n")
                    out_f.write(f"=== SOURCE URL: {url} ===\n\n")
                    out_f.write(f"=== DETAILED DESCRIPTION ===\n\n")
                    out_f.write(desc_text)
                    out_f.write("\n")

                print(f"Success: Saved to {save_path}")
                stats["success"] += 1

            except Exception as e:
                print(f"Error processing {skey}: {str(e)}")
                stats["failure"] += 1

    except Exception as e:
        print(f"Global error: {str(e)}")
    finally:
        print(f"\nProcessing finished. Success: {stats['success']}, Failure: {stats['failure']}")
        driver.quit()

if __name__ == "__main__":
    input_path = "web_address.txt"
    scrape_patent_data(input_path)
