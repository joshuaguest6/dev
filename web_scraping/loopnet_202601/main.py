from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random
import re


sf_regex = re.compile(r'([\d,]+)\s*SF', re.IGNORECASE)
price_regex = re.compile(r'\$\d{1,3}(?:,\d{3})*(?:\s*-\s*\$\d{1,3}(?:,\d{3})*)?\s*/\s*SF/YR', re.IGNORECASE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()
    Stealth().use_sync(page)

    page.goto("https://www.loopnet.com/Listing/667-Madison-Ave-New-York-NY/20044350/")
    time.sleep(random.uniform(10, 20))

    # page.wait_for_selector('header.no-name header', timeout=60000)
    # page.wait_for_selector('div.placard-content', timeout=60000)

    # Wrap in list for now, as only returning one
    # headers = [page.query_selector('header.no-name header', timeout=60000)]
    # tiles = [page.query_selector('div.placard-content', timeout=60000)]

    # for header, tile in zip(headers, tiles):

    #     address_tag = header.query_selector('a.left-h4')
    #     address = address_tag.inner_text().strip()

    #     suburb_tag = header.query_selector('a.right-h6')
    #     suburb = suburb_tag.inner_text().strip()

    #     full_address = address + suburb

    #     details_tag = tile.query_selector('a.toggle-favorite')
    #     details_link = details_tag.get_attribute('href') if details_tag else None

    #     tile_info = tile.query_selector('div.placard-info div.data ul.data-points')
    #     fields = tile_info.query_selector_all('li')

    #     properties = []
    #     for field in fields:
    #         text = field.inner_text().strip()
    #         sqf_match = sf_regex.search(text)
    #         price_match = price_regex.search(text)

    #         if sqf_match and price_match:
    #             properties.append({
    #                 'Address': full_address,
    #                 'SF': sqf_match.group(1),
    #                 'Price': price_match.group(1),
    #                 'Details link': details_link
    #             })

    # print(properties)



