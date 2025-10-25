from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests

from seleniumwire import webdriver  # instead of selenium
import json
import pandas as pd

driver = webdriver.Chrome()
driver.get("https://www.salvosstores.com.au/stores")

# Loop through all requests captured by Selenium Wire
for request in driver.requests:
    if request.response:
        if "store-list" in request.url:
            data = request.response.body.decode("utf-8")
            stores = json.loads(data)
            print(f"Found {len(stores)} stores")
            break

driver.quit()

url = "https://www.salvosstores.com.au/api/uplister/store-list"

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "x-requested-with":"XMLHttpRequest"} # add x-requested-with headers here to make sure the output is json format

resp = requests.get(url, headers=headers)
resp.status_code
resp.text[:500]
stores = resp.json()

chrome_options = Options()
chrome_options.add_argument("--headless")  # optional
chrome_options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.get(url)


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 10)
# wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'shadow-about-card')))
wait.until(lambda d: d.find_element(By.CSS_SELECTOR, 'div.shadow-about-card div.text-2xl').text != '')

from selenium.webdriver.common.action_chains import ActionChains
import time

last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # wait for JS to load more stores
    
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  # reached bottom
    last_height = new_height

store_cards = driver.find_elements(By.CLASS_NAME, 'shadow-about-card')

first = store_cards[0]
name = first.find_element(By.CLASS_NAME, 'text-2xl').text
address = first.find_element(By.CLASS_NAME, 'whitespace-pre-wrap').text
phone_div = first.find_element(By.XPATH, ".//div[span[text()='Phone:']]")
phone_text = phone_div.text.replace("Phone:", "").strip()
hours_divs = first.find_elements(By.CSS_SELECTOR, "div.h-10 div.flex")
hours = ' | '.join(div.text for div in hours_divs)
link = first.find_element(By.TAG_NAME, 'a').get_attribute('href')

print(f'{len(store_cards)} stores found')

stores = []

for store in store_cards:
    name = store.find_element(By.CLASS_NAME, 'text-2xl').text
    address = store.find_element(By.CLASS_NAME, 'whitespace-pre-wrap').text
    hours_divs = store.find_elements(By.CSS_SELECTOR, "div.h-10 div.flex")
    hours = ' | '.join(div.text for div in hours_divs)
    stores.append(
        {
            'name': name,
            'address': address,
            'hours': hours
        }
    )

stores[10:20]
store_cards[20]

driver.quit()
