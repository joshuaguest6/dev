from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from google.auth import default
from google.cloud import storage
import pandas as pd

gsheet = 'lumens.com Scrape'
sheet_name = 'data'

# Scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]


BRANDS = {
    'AND': 'a-n-d'
    }

products = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        storage_state="state.json"
    )
    page = context.new_page()
    Stealth().use_sync(page)

    for brand in BRANDS:
        page.goto(f"https://www.lumens.com/{BRANDS[brand]}/", timeout=60000)
        time.sleep(random.uniform(2, 4))
        page.wait_for_selector("span.total-sort-count", state="visible", timeout=60000)

        # --- HUMAN-LIKE SCROLL ---
        page.evaluate("""() => {
            window.scrollBy(0, document.body.scrollHeight / 2);
        }""")
        time.sleep(random.uniform(1,2))
        page.evaluate("""() => {
            window.scrollBy(0, document.body.scrollHeight);
        }""")
        time.sleep(random.uniform(1,2))

        # --- HUMAN-LIKE MOUSE MOVEMENT ---
        page.mouse.move(random.randint(100, 400), random.randint(100, 300))
        time.sleep(random.uniform(0.5, 1))
        page.mouse.move(random.randint(400, 800), random.randint(300, 600))
        time.sleep(random.uniform(0.5, 1))

        el_results = page.query_selector("span.total-sort-count")
        results_text = el_results.inner_text()
        print(f"Results for {brand}: {results_text}")
        results = int(results_text.split()[0])

        time.sleep(random.uniform(2, 4))

        for start in range(0, results, 24):
            page.goto(f"https://www.lumens.com/{BRANDS[brand]}/?start={start}&sz=24", timeout=60000)
            time.sleep(random.uniform(2, 4))

            # --- HUMAN-LIKE SCROLL ---
            page.evaluate("""() => {
                window.scrollBy(0, document.body.scrollHeight / 2);
            }""")
            time.sleep(random.uniform(1,2))
            page.evaluate("""() => {
                window.scrollBy(0, document.body.scrollHeight);
            }""")
            time.sleep(random.uniform(1,2))

            # --- HUMAN-LIKE MOUSE MOVEMENT ---
            page.mouse.move(random.randint(100, 400), random.randint(100, 300))
            time.sleep(random.uniform(0.5, 1))
            page.mouse.move(random.randint(400, 800), random.randint(300, 600))
            time.sleep(random.uniform(0.5, 1))

            try:
                page.wait_for_selector("div.product-tile", timeout=60000)
            except:
                break # no more products

            tiles = page.query_selector_all("div.product-tile")
            if not tiles:
                break

            for tile in tiles:
                sku = tile.get_attribute("data-itemid")
                name_el = tile.query_selector(".product-name a")
                name = name_el.inner_text().strip() if name_el else None

                img = tile.query_selector("img")
                img_link = img.get_attribute("data-img-url")

                swatches_ul = tile.query_selector("ul.swatchesdisplay")

                colour_options = []
                if swatches_ul:
                    swatches = swatches_ul.query_selector_all("li.swatch-li")

                    
                    for swatch in swatches:
                        a = swatch.query_selector("a")
                        colour = a.get_attribute("title")

                        colour_options.append(colour)

                products.append(
                    {
                    "Brand": brand,
                    "SKU": sku,
                    "Name": name,
                    "Image Link": img_link,
                    "Colour Options": colour_options
                }
                )

                time.sleep(random.uniform(0.05, 0.2))

            time.sleep(random.uniform(2, 4))
            
        time.sleep(random.uniform(20, 30))

    browser.close()

print(len(products))

products[0]

df = pd.DataFrame(products)

### TO GOOGLE SHEETS ###

creds, project = default(scopes=scope)
client = gspread.authorize(creds)

spreadsheet = client.open(gsheet)
try:
    sheet = spreadsheet.worksheet(sheet_name)
except gspread.WorksheetNotFound:
    sheet = spreadsheet.add_worksheet(
        sheet_name, 
        cols=20, 
        rows=1000
        )
    
set_with_dataframe(sheet, df)
