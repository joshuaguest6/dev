from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import json
import os
from google.cloud import storage
import logging
import requests
import random 

USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",

    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",

    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",

    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",

    # Mac Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:117.0) Gecko/20100101 Firefox/117.0",

    # Mobile Chrome (Android)
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Mobile Safari/537.36",
]

logging.basicConfig(level=logging.INFO)

data = []

def load_search(idx=None):
    with open('searches.json', 'r') as f:
        searches = json.load(f)

    if idx is None:
        # for when in cloud, get idx
        idx = os.environ.get('CLOUD_RUN_TASK_INDEX', None)

    if idx is not None:
        idx = int(idx)

    try:
        search = searches[idx]['search']
        logging.info(f'Search index: {idx}')
        logging.info(f'Search: {search}')
    except:
        logging.info('No search returned')
        logging.info(f'Index passed: {idx}')
        search = None

    return search

def load_results(page):
    scrollable_div = page.locator('div[role="feed"]')

    previous_count = 0

    while True:
        scrollable_div.evaluate(
            """(el) => { el.scrollBy(0, el.scrollHeight); }"""
        )

        time.sleep(3)

        listings = page.locator('div[role="article"]')
        current_count = listings.count()

        logging.info(f'Listings loaded: {current_count}')

        if current_count == previous_count:
            break

        previous_count = current_count

def parse_results(articles):
    data = []
    for article in articles:
        name_tag = article.query_selector('div.fontHeadlineSmall')
        name = name_tag.inner_text().strip() if name_tag else None

        details_tag = article.query_selector('a[href^="https://"]')
        details_link = details_tag.get_attribute('href') if details_tag else None

        data.append({
            'name': name,
            'details_link': details_link
        })
    
    return data

def random_fingerprint():
    ua = random.choice(USER_AGENTS)
    width = random.choice([1280, 1366, 1440, 1920])
    height = random.choice([720, 800, 900, 1080])
    locale = random.choice(['en-US', 'en-GB', 'de-DE'])
    timezone = random.choice(['Europe/Berlin', 'Europe/London', 'America/New_York'])

    return {
        'user_agent': ua,
        'viewport': {'width': width, 'height': height},
        'locale': locale,
        'timezone_id': timezone
    }

def generate_list(search):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(**random_fingerprint())
        page = context.new_page()
        Stealth().use_sync(page)


        logging.info('Loading google maps...')
        page.goto(f'https://www.google.com/maps/search/{search.replace(" ", "+")}/', timeout=60000)
        page.wait_for_selector('div[role="feed"]', timeout=60000)

        load_results(page)

        feed = page.query_selector('div[role="feed"]')

        articles = feed.query_selector_all('div[role="article"]')
        logging.info(f'{len(articles)} businesses found')

        data = parse_results(articles)

        browser.close()

    with open('data_list.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    return data

def extract_details(records):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        logging.info('Extracting business website links...')
        for record in records:
            context = browser.new_context()
            page = context.new_page()
            Stealth().use_sync(page)

            try:
                page.goto(record['details_link'], timeout=60000)
                page.wait_for_selector('a[aria-label^="Website:"]', timeout=30000)
                website_tag = page.query_selector('a[aria-label^="Website:"]')
            except:
                website_tag = None
            
            website_link = website_tag.get_attribute('href') if website_tag else None

            phone_button = page.query_selector('button[aria-label^="Phone:"]')
            phone_tag = phone_button.query_selector('div.fontBodyMedium') if phone_button else None
            phone = phone_tag.inner_text().strip() if phone_tag else None

            record['website_link'] = website_link
            record['phone'] = phone

            context.close()
            time.sleep(random.uniform(2, 5))

        logging.info(f'{len([record for record in records if record["website_link"] is not None])} website links found')
        logging.info(f'{len([record for record in records if record["website_link"] is None])} website links not found')

        browser.close()
    
    return records

def enrich_data(records):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        logging.info('Visiting business websites...')
        for record in records:
            context = browser.new_context()
            page = context.new_page()
            Stealth().use_sync(page)

            try:
                page.goto(record['website_link'], timeout=60000)
            except:
                record['website_phone'] = None
                record['error'] = 'Website not found'
                context.close()
                continue

            try:
                page.wait_for_selector('a[href^="tel:"]', timeout=10000)
            except:
                record['website_phone'] = None
                record['error'] = 'Phone not found'
                context.close()
                continue

            phone_tag = page.query_selector('a[href^="tel:"]')
            phone = phone_tag.get_attribute('href') if phone_tag else None
            phone = phone.replace('tel:', '').strip() if phone else None

            record['website_phone'] = phone
            record['error'] = None

            context.close()

        logging.info('Finished visiting business websites...')
        
        logging.info(f'{len([record for record in records if record["website_phone"] is not None])} phone numbers found')
        logging.info(f'{len([record for record in records if record["website_phone"] is None])} phone numbers not found')

        browser.close()

    return records

def save_records(records, search):
    client = storage.Client()
    bucket = client.bucket('maps-crawler')
    blob = bucket.blob(f'germany/{search.replace(" ", "_").lower()}.json')

    blob.upload_from_string(json.dumps(records, indent=2), content_type='application/json')

def main(search):
    # Stagger the cloud run job workers
    time.sleep(random.uniform(2, 5))

    public_ip = requests.get("https://api.ipify.org").text
    logging.info(f"Public IP: {public_ip}")

    logging.info(f'Searching google maps for: {search}')
    records = generate_list(search)

    records = extract_details(records)

    records = enrich_data(records)

    save_records(records, search)

if __name__ == '__main__':
    # for when local, get the idx
    idx = os.environ.get('idx', None)
    if idx is not None:
        idx = int(idx)

    SEARCH = load_search(idx)
    if not SEARCH:
        raise ValueError("SEARCH variable is required")

    main(SEARCH)
    