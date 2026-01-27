from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth 
import urllib.parse
import json
import pandas as pd
import time
from datetime import datetime
import pytz
from google.cloud import storage
import gspread
from gspread_dataframe import set_with_dataframe
from google.auth import default

gsheet = 'YellowPages Physiotherapists'
sheet_name = 'data'

# Scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

tz = pytz.timezone('Australia/Sydney')
NOW = datetime.now(tz)
FORMATTED_NOW = NOW.strftime("%Y%m%d_%H%M%S")

MAX_RETRIES = 3
WAIT_TIMEOUT = 10000

def load_page_with_retries(url):
    tiles = []
    for attempt in range(1, MAX_RETRIES+1):
        context = browser.new_context()
        page = context.new_page()
        Stealth().use_sync(page)
        try:
            page.goto(url)
            page.wait_for_selector('div.MuiPaper-root', timeout=WAIT_TIMEOUT)

            tiles = page.query_selector_all('div.MuiPaper-root')
            if tiles:
                return tiles, context
            else:
                print(f'No tiles found on attempt {attempt}. Retrying...')
        except PlaywrightTimeoutError:
            print(f'Timeout on attempt {attempt}. Retrying...')
        except Exception as e:
            print(f'Error on attempt {attempt}: {e}. Retrying...')
        
        context.close()
        time.sleep(2)
    
    raise RuntimeError(f'Failed to load page correctly after {MAX_RETRIES} attempts')

base_url = "https://www.yellowpages.com.au/search/listings"

params = {
    'clue': 'Physiotherapist',
    'locationClue': 'Greater Sydney, NSW'
}

page_number = 1
data = []

seen_names_before = set()
seen_names_after = set()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False
    )

    while True:
        seen_names_before = seen_names_after
        params['pageNumber'] = page_number
        url = f'{base_url}?{urllib.parse.urlencode(params)}'

        print(f'Going to {url}')
        tiles, context = load_page_with_retries(url)

        if not tiles:
            print(f'No tiles found - End')
            print(f'{len(seen_names_after)} unique business were found overall')
            break

        print(f'{len(tiles)} tiles found')

        for tile in tiles:
            name_tag = tile.query_selector('h3.MuiTypography-root')
            name = name_tag.inner_text().strip() if name_tag else None
            print(f'Business name: {name}')

            phone_tag = tile.query_selector('a[href^="tel:"]')
            phone = phone_tag.get_attribute('href') if phone_tag else None
            phone = phone.replace('tel:', '').strip() if phone else None
            print(f'Business phone: {phone}')

            website_tag = tile.query_selector('a[href^="http:"]')
            website_link = website_tag.get_attribute('href') if website_tag else None

            listing_tag = tile.query_selector('a.MuiTypography-root.MuiLink-root.MuiLink-underlineNone.MuiTypography-colorPrimary')
            listing_link = 'https://www.yellowpages.com.au/' + listing_tag.get_attribute('href') if listing_tag else None 

            if name is None and phone is None:
                print('No data - continue')
                continue

            data.append({
                'business_name': name,
                'phone_number': phone,
                'city': 'Sydney',
                'state': 'NSW',
                'source': 'Yellow Pages',
                'website_link' : website_link,
                'listing_link': listing_link

            })

        seen_names_after = set([i['business_name'] for i in data])

        # Stopping on page 5 to test big runs
        if seen_names_after == seen_names_before or page_number > 5:
            print(f'No new businesses found on page {page_number}. End')
            print(f'{len(seen_names_after)} unique business were found overall')
            break

        page_number += 1
        context.close()
        time.sleep(2)
    
    browser.close()

df = pd.DataFrame(data)
df = df.drop_duplicates(subset=['business_name', 'phone_number'])
data = df.to_dict(orient='records')

with open('data.json', 'w') as f:
    json.dump(data, f, indent=2)

### SAVE RUN TO GCS ###

client = storage.Client()
bucket = client.bucket('yellowpages_physiotherapists')
blob = bucket.blob(f'data_{FORMATTED_NOW}')

blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')

### SEND TO GOOGLE SHEETS ###

creds, project = default(scope)
client = gspread.authorize(creds)

spreadsheet = client.open(gsheet)
try:
    sheet = spreadsheet.worksheet(sheet_name)
except:
    sheet = spreadsheet.add_worksheet(
        sheet_name,
        cols=20,
        rows=1000
    )

set_with_dataframe(sheet, df)