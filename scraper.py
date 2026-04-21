import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_patent_data(input_file):
    # 저장 경로 설정
    output_dir = "c:\\coding\\patent\\abstract\\extracted_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 웹드라이버 설정 (Chrome)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # 브라우저 창을 띄우지 않으려면 주석 해제
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]

        for url in urls:
            # skey 추출 (파일명으로 사용)
            skey = url.split('skey=')[-1]
            print(f"Processing: {skey}...")

            driver.get(url)
            wait = WebDriverWait(driver, 10)
            
            # 페이지 로드 대기 (본문 영역이 보일 때까지)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2) # 안정적인 로딩을 위한 짧은 대기

            # 1. ']' 키 한 번 입력 -> 청구항(Claims)
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys("]")
            time.sleep(1.5) # 탭 전환 대기
            
            claims_text = ""
            try:
                # 청구항 컨텐츠 영역의 ID나 Class를 특정해야 함 (예시로 body 내 텍스트 추출)
                # 실제 웹사이트의 구조에 따라 By.ID나 By.CLASS_NAME으로 정교화 필요
                claims_text = driver.find_element(By.ID, "divClaimContent").text 
            except:
                claims_text = "청구항 정보를 찾을 수 없습니다."

            # 2. ']' 키 한 번 더 입력 -> 상세한 설명(Description)
            body.send_keys("]")
            time.sleep(1.5) # 탭 전환 대기
            
            desc_text = ""
            try:
                desc_text = driver.find_element(By.ID, "divDetailContent").text
            except:
                desc_text = "상세 설명 정보를 찾을 수 없습니다."

            # 파일 저장
            save_path = os.path.join(output_dir, f"{skey}.txt")
            with open(save_path, "w", encoding="utf-8") as out_f:
                out_f.write(f"=== CLAIMS ===\n{claims_text}\n\n")
                out_f.write(f"=== DESCRIPTION ===\n{desc_text}\n")
            
            print(f"Saved: {save_path}")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    input_path = "c:\\coding\\patent\\abstract\\web_address.txt"
    if os.path.exists(input_path):
        scrape_patent_data(input_path)
    else:
        print(f"파일을 찾을 수 없습니다: {input_path}")