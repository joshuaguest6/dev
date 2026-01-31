from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import json

data = []

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

        print(f'Listings loaded: {current_count}')

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


def generate_list():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        Stealth().use_sync(page)

        page.goto('https://www.google.com/maps/search/dentist+berlin/')
        page.wait_for_selector('div[role="feed"]', timeout=60000)

        # load_results(page)

        feed = page.query_selector('div[role="feed"]')

        articles = feed.query_selector_all('div[role="article"]')

        data = parse_results(articles)

        browser.close()

    with open('data_list.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    return data

def extract_details(records):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        for record in records:
            context = browser.new_context()
            page = context.new_page()
            Stealth().use_sync(page)

            page.goto(record['details_link'])
            page.wait_for_selector('a[aria-label^="Website:"]', timeout=60000)

            website_tag = page.query_selector('a[aria-label^="Website:"]')
            website_link = website_tag.get_attribute('href') if website_tag else None

            phone_button = page.query_selector('button[aria-label^="Phone:"]')
            phone_tag = phone_button.query_selector('div.fontBodyMedium') if phone_button else None
            phone = phone_tag.inner_text().strip() if phone_tag else None

            record['website_link'] = website_link
            record['phone'] = phone

            context.close()
            time.sleep(3)

        browser.close()
    
    return records

def enrich_data(records):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        for record in records:
            context = browser.new_context()
            page = context.new_page()
            Stealth().use_sync(page)

            page.goto(record['website_link'], timeout=60000)
            
            try:
                page.wait_for_selector('a[href^="tel:"]', timeout=10000)
            except:
                record['website_phone'] = None
                context.close()
                continue

            phone_tag = page.query_selector('a[href^="tel:"]')
            phone = phone_tag.get_attribute('href') if phone_tag else None
            phone = phone.replace('tel:', '').strip() if phone else None

            record['website_phone'] = phone

            context.close()
        
        browser.close()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

def main():
    records = generate_list()

    records = extract_details(records)

    enrich_data(records)


main()