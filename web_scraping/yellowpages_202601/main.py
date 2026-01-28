from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

import urllib.parse
import json
import time
from datetime import datetime
import pytz
import pandas as pd

from google.cloud import storage
import gspread
from gspread_dataframe import set_with_dataframe
from google.auth import default

# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://www.yellowpages.com.au/search/listings"

SEARCHES = [
    {
        "what": "Physiotherapists",
        "where": "Melbourne, VIC 3000",
    },
    {
        "what": "Physiotherapists",
        "where": "Sydney, NSW 2000",
    }
]

MAX_RETRIES = 1
WAIT_TIMEOUT_MS = 10_000
PAGE_SLEEP_SECONDS = 2
MAX_PAGES = 5  # safety limit for now

GCS_BUCKET = "yellowpages_physiotherapists"

GSHEET_NAME = "YellowPages Physiotherapists"
GSHEET_TAB = "data"

GSHEET_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# TIME HELPERS
# ============================================================

TZ = pytz.timezone("Australia/Sydney")
RUN_TIMESTAMP = datetime.now(TZ).strftime("%Y%m%d_%H%M%S")


# ============================================================
# PAGE LOADING
# ============================================================

def load_listing_tiles(browser, url, page_number):
    """
    Attempt to load a Yellow Pages search page and return listing tiles.
    Retries with fresh contexts to reduce detection issues.
    """
    errors = []

    for attempt in range(1, MAX_RETRIES + 1):
        context = browser.new_context()
        page = context.new_page()
        Stealth().use_sync(page)

        try:
            page.goto(url)
            page.wait_for_selector("div.MuiPaper-root", timeout=WAIT_TIMEOUT_MS)

            tiles = page.query_selector_all("div.MuiPaper-root")
            if tiles:
                return tiles, context, errors

            print(f"[WARN] No tiles found (attempt {attempt})")

        except PlaywrightTimeoutError:
            print(f"[WARN] Timeout loading page (attempt {attempt})")

        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

        context.close()
        time.sleep(PAGE_SLEEP_SECONDS)

    errors.append({
        "type": "page_load_failure",
        "url": url,
        "page_number": page_number,
        "attempts": MAX_RETRIES,
        "timestamp": RUN_TIMESTAMP,
    })

    return [], None, errors


# ============================================================
# TILE PARSING
# ============================================================

def parse_listing_tile(tile, where):
    """
    Extract business fields from a single listing tile.
    """
    name_tag = tile.query_selector("h3.MuiTypography-root")
    name = name_tag.inner_text().strip() if name_tag else None

    phone_tag = tile.query_selector('a[href^="tel:"]')
    phone = None
    if phone_tag:
        phone = phone_tag.get_attribute("href")
        phone = phone.replace("tel:", "").strip() if phone else None


    website_tag = tile.query_selector(
        'a.MuiButtonBase-root[href^="https://"], a.MuiButtonBase-root[href^="http://"]'
    )
    website = website_tag.get_attribute("href") if website_tag else None


    listing_tag = tile.query_selector(
        "a.MuiTypography-root.MuiLink-root.MuiLink-underlineNone.MuiTypography-colorPrimary"
    )
    listing_url = (
        "https://www.yellowpages.com.au/" + listing_tag.get_attribute("href")
        if listing_tag else None
    )


    if not name and not phone:
        return None

    return {
        "business_name": name,
        "phone_number": phone,
        "city": where,
        "source": "Yellow Pages",
        "website_link": website,
        "listing_link": listing_url,
    }


# ============================================================
# SEARCH SCRAPER
# ============================================================

def scrape_search(search):
    """
    Scrape all pages for a single (what, where) search.
    """
    params = {
        "clue": search["what"],
        "locationClue": search["where"],
    }

    records = []
    errors = []

    seen_names_previous = set()
    page_number = 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        while True:
            if page_number > MAX_PAGES:
                print(f'Finish after page {MAX_PAGES}')
                break

            params["pageNumber"] = page_number
            url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"

            print(f"\n[INFO] Loading page {page_number}")
            tiles, context, page_errors = load_listing_tiles(
                browser, url, page_number
            )
            errors.extend(page_errors)

            if not tiles:
                print(f"[WARN] No tiles on page {page_number}, skipping")
                page_number += 1
                if context:
                    context.close()
                continue

            for tile in tiles:
                record = parse_listing_tile(tile, search["where"])
                if record:
                    records.append(record)

            current_names = set([r['business_name'] for r in records])

            if current_names == seen_names_previous:
                print("[INFO] No new businesses found — stopping")
                if context:
                    context.close()
                break

            seen_names_previous = current_names
            page_number += 1

            if context:
                context.close()
            time.sleep(PAGE_SLEEP_SECONDS)

        browser.close()

    return records, errors


# ============================================================
# OUTPUT HELPERS
# ============================================================

def dedupe_records(records):
    df = pd.DataFrame(records)
    dup_rows = df[df.duplicated(
        subset=["business_name", "phone_number"],
        keep=False
    )]
    print('Duplicates:')
    if not dup_rows.empty:
        print(dup_rows[['business_name', 'phone_number', 'city']])
    else:
        print('No duplicates')

    before = len(df)
    df = df.drop_duplicates(subset=["business_name", "phone_number"])
    after = len(df)
    print(f"[INFO] Deduped {before} → {after}")
    return df


def upload_to_gcs(data, errors):
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)

    bucket.blob(
        f"yellowpages_data_{RUN_TIMESTAMP}.json"
    ).upload_from_string(json.dumps(data, indent=2), content_type="application/json")

    bucket.blob(
        f"yellowpages_errors_{RUN_TIMESTAMP}.json"
    ).upload_from_string(json.dumps(errors, indent=2), content_type="application/json")


def upload_to_google_sheets(df):
    creds, _ = default(GSHEET_SCOPE)
    client = gspread.authorize(creds)

    spreadsheet = client.open(GSHEET_NAME)
    try:
        sheet = spreadsheet.worksheet(GSHEET_TAB)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(
            GSHEET_TAB, rows=1000, cols=20
        )

    sheet.clear()
    set_with_dataframe(sheet, df)


# ============================================================
# MAIN
# ============================================================

def main():
    all_records = []
    all_errors = []

    for search in SEARCHES:
        records, errors = scrape_search(search)
        all_records.extend(records)
        all_errors.extend(errors)

    df = dedupe_records(all_records)

    upload_to_gcs(df.to_dict(orient="records"), all_errors)
    upload_to_google_sheets(df)

    # can remove this later
    with open('data.json', 'w') as f:
        json.dump(df.to_dict(orient='records'), f, indent=2)

    with open('data_errors.json', 'w') as f:
        json.dump(all_errors, f, indent=2)

    return "OK", 200


if __name__ == "__main__":
    main()
