from playwright.sync_api import sync_playwright
import urllib.parse
import pandas as pd
import json
import numpy as np


base_url = "https://find-and-update.company-information.service.gov.uk/advanced-search/get-results"

params = {
    'companyNameIncludes': 'Gym',
    'incorporationFromDay': '1',
    'incorporationFromMonth': '1',
    'incorporationFromYear': '2025',
    'incorporationToDay': '31',
    'incorporationToMonth': '12',
    'incorporationToYear': '2025'
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto(f"{base_url}?{urllib.parse.urlencode(params)}")
    page.wait_for_selector('button[data-event-id="advanced-search-results-page-download-results"]', timeout=60000)

    with page.expect_download() as download_info:
        page.click('button[data-event-id="advanced-search-results-page-download-results"]')

    download = download_info.value
    DOWNLOAD_PATH = 'downloads/companies.csv'
    download.save_as(DOWNLOAD_PATH)

    browser.close()

df = pd.read_csv(DOWNLOAD_PATH)

df = df.replace({np.nan: None})

data = df.to_dict(orient='records')

with open('downloads/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
