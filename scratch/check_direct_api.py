import requests

url = "http://newsd.wips.co.kr/wipslink/api/djpdshtm.wips?skey=2725040000516"
response = requests.get(url)
print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Preview: {response.text[:1000]}")
