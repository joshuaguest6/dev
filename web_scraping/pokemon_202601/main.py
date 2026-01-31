from playwright.sync_api import sync_playwright
import pandas as pd
import json

url = 'https://www.cardrush-pokemon.jp/'

data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto(url)
    page.wait_for_selector('li.list_item_cell', timeout=60000)

    card_tiles = page.query_selector_all('li.list_item_cell')

    print(len(card_tiles))

    for tile in card_tiles:
        link_tag = tile.query_selector('a.item_data_link')
        link = link_tag.get_attribute('href') if link_tag else None

        name_tag = tile.query_selector('span.goods_name')
        name = name_tag.inner_text().strip() if name_tag else None

        print(name)

        data.append({
            'name': name,
            'link': link
        })
    
    browser.close()

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

