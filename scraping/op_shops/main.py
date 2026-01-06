"""
Op Shop Store Scraper & Change Tracker

This script scrapes store data from multiple charity op shop chains in Australia,
geocodes addresses, detects changes to store information (hours/address),
flags recent changes, and saves current and historical records to JSON files.

Key features:
- Salvos: scraped using Selenium due to API restrictions
- Save the Children: scraped via their API
- Geocoding with caching
- Detect changes in store hours or addresses
- Track last changes per store
- Flag changes within last 7 days
- Save current and historical data in JSON
"""

import os
import re
import json
from datetime import datetime, timedelta

import pandas as pd
import requests
from geopy.geocoders import Nominatim
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from google.cloud import storage
from google.api_core.exceptions import NotFound

# ---------------------- GLOBAL CONFIG ----------------------
NOW = datetime.now()
FORMATTED_NOW = NOW.strftime("%Y-%m-%d %H:%M:%S")

# Cache file for geocoding to avoid repeated API calls
GEOCODE_CACHE_FILE = 'geocode_cache.json'
if os.path.exists(GEOCODE_CACHE_FILE):
    with open(GEOCODE_CACHE_FILE, 'r') as f:
        geocode_cache = json.load(f)
else:
    geocode_cache = {}

geolocator = Nominatim(user_agent="opshop_locator")

# ---------------------- HELPER FUNCTIONS ----------------------

def get_latlon(address: str):
    """
    Retrieve latitude and longitude for a given address.
    Checks a local cache first to reduce API calls.
    """
    if address in geocode_cache:
        return geocode_cache[address]

    location = geolocator.geocode(address, timeout=10)
    
    # Retry with simplified address if first attempt fails
    if not location and ',' in address:
        parts = address.split(',', 1)
        location = geolocator.geocode(parts[1].strip(), timeout=10)

    if location:
        latlon = (location.latitude, location.longitude)
    else:
        latlon = (None, None)

    # Save result to cache
    geocode_cache[address] = latlon
    with open(GEOCODE_CACHE_FILE, 'w') as f:
        json.dump(geocode_cache, f, indent=2)

    return latlon


def format_address(addr: str) -> str:
    """
    Clean and standardize raw address strings.
    - Expands common abbreviations
    - Moves unit/shop prefixes
    - Ensures country is appended
    """
    if not addr:
        return ''

    addr = re.sub(r'\r?\n\s*\((.*?)\)', r', \1', addr)  # newline + parentheses
    addr = re.sub(r'\s*\((.*?)\)', r', \1', addr)       # parentheses
    addr = re.sub(r'\bCnr\b', 'Corner of', addr, flags=re.IGNORECASE)  # Cnr -> Corner
    addr = re.sub(r'^\d+/\s*', '', addr)  # remove unit/shop prefixes
    addr = re.sub(r',\s*,+', ',', addr).strip(', ')  # clean trailing commas

    if 'Australia' not in addr:
        addr += ', Australia'

    return addr.strip()


# ---------------------- SCRAPERS ----------------------

def get_salvos_stores() -> list:
    """
    Scrape Salvos stores using Selenium (API blocked).
    Returns a list of dictionaries with store info.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://www.salvosstores.com.au/stores")

    # Fetch the store list JSON via JavaScript
    salvos_stores = driver.execute_script("""
        return fetch('/api/uplister/store-list')
            .then(response => response.json())
    """)

    print(f"Total Salvos stores found: {len(salvos_stores)}")
    driver.quit()

    store_data = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for store in salvos_stores.values():
        store_id = store['StoreID']
        name = store['Name']
        address = store['FullAddress']
        lat = store.get('Latitude', None)
        lon = store.get('Longitude', None)

        if 'OpeningHours' in store:
            oh = store['OpeningHours']
            hours = {day: f"{oh[day]['Opening']} to {oh[day]['Closing']}" 
                     if isinstance(oh[day], dict) else 'Closed' for day in days}
        else:
            hours = {}

        store_data.append({
            'Date': FORMATTED_NOW,
            'Store': "Salvos",
            'StoreID': store_id,
            'Suburb': name,
            'Address': address,
            'Latitude': lat,
            'Longitude': lon,
            'Hours': ', '.join(f"{k}: {v}" for k, v in hours.items())
        })

    return store_data


def get_stc_stores() -> list:
    """
    Scrape Save The Children op shops via API.
    Geocode addresses and format data into consistent dictionary.
    """
    url = "https://www.savethechildren.org.au/api/opshop/getopshoplist"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.savethechildren.org.au/",
    }

    resp = requests.get(url, headers=headers)
    store_list = resp.json()['data']['contentData']

    store_data = []
    for item in store_list:
        name = item['title']
        address = format_address(item['excerpt'])
        lat, lon = get_latlon(address)
        hours = item.get('hours', '')

        store_data.append({
            'Date': FORMATTED_NOW,
            'Store': 'Save The Children',
            'StoreID': 'STC-' + address,
            'Suburb': name,
            'Address': address,
            'Latitude': lat,
            'Longitude': lon,
            'Hours': hours
        })

    return store_data


# ---------------------- DATA STORAGE ----------------------

def save_current(data: pd.DataFrame, filename='stores_current.json'):
    """Save current scraped data to JSON."""
    # with open(filename, 'w') as f:
    #     json.dump(data.to_dict(orient='records'), f, indent=2)

    client = storage.Client()
    bucket = client.bucket('op-shop-data')
    blob = bucket.blob('stores_current.json')

    blob.upload_from_string(
        json.dumps(data.to_dict(orient='records'), indent=2),
        content_type='application/json'
    )


def save_history(data: pd.DataFrame, filename='stores_history.json'):
    """Append new data to history JSON file."""
    records = data.to_dict(orient='records')
    # if os.path.exists(filename):
    #     with open(filename, 'r') as f:
    #         hist = json.load(f)
    #     hist += records
    # else:
    #     hist = records
    # with open(filename, 'w') as f:
    #     json.dump(hist, f, indent=2)

    client = storage.Client()
    bucket = client.bucket('op-shop-data')
    blob = bucket.blob('stores_history.json')

    try:
        existing = blob.download_as_string()
        hist = json.loads(existing)
    except NotFound:
        hist = []

    hist += records

    blob.upload_from_string(
        json.dumps(hist, indent=2),
        content_type='application/json'
    )


# ---------------------- CHANGE DETECTION ----------------------

def check_changes(data: pd.DataFrame) -> pd.DataFrame:
    """
    Compare current scrape to last scrape to detect changes.
    Flags stores with differences in 'Hours' or 'Address'.
    """
    if os.path.exists('stores_current.json'):
        with open('stores_current.json', 'r') as f:
            stores_current = json.load(f)
    else:
        stores_current = []

    # Merge current scrape with previous data
    stores_current_df = pd.DataFrame(stores_current)
    merged_df = data.merge(
        stores_current_df, 
        on=['Store', 'StoreID', 'Suburb'], 
        how='left', 
        suffixes=('_new', '_old')
    )

    check_cols = ['Address', 'Hours']

    def detect_changes(row):
        """Detect which columns changed."""
        changed_cols = [col for col in check_cols 
                        if row[f"{col}_new"] != row[f"{col}_old"] 
                        and not pd.isna(row[f"{col}_old"])]
        row['change_flag'] = bool(changed_cols)
        row['Columns Changed'] = ', '.join(
            f"{col} before: {row[f'{col}_old']}\n{col} after: {row[f'{col}_new']}"
            for col in changed_cols
        )
        return row

    merged_df = merged_df.apply(detect_changes, axis=1)

    # Save current scrape for next comparison
    save_current(data)

    # Keep only relevant columns and rename to original names
    result_df = merged_df[[
        'Date_new', 'Store', 'StoreID', 'Suburb', 
        'Address_new', 'Latitude_new', 'Longitude_new', 
        'Hours_new', 'change_flag', 'Columns Changed'
    ]].rename(columns={
        'Date_new': 'Date', 
        'Address_new': 'Address',
        'Latitude_new': 'Latitude',
        'Longitude_new': 'Longitude',
        'Hours_new': 'Hours'
    })

    return result_df


def check_history_changes(data: pd.DataFrame) -> pd.DataFrame:
    """
    Tracks:
    - Stores that had any changes in the last 7 days
    - Most recent change per store
    """
    # Load historical data
    if os.path.exists('stores_history.json'):
        with open('stores_history.json', 'r') as f:
            hist = json.load(f)
    else:
        hist = []

    hist_df = pd.DataFrame(hist)
    all_data = pd.concat([data, hist_df], axis=0, ignore_index=True)

    # Most recent change per store
    last_changes = all_data[all_data['change_flag'] == True]
    idx = last_changes.groupby('StoreID')['Date'].idxmax()
    last_changes = last_changes.loc[idx, ['StoreID', 'Date', 'Columns Changed']]
    last_changes = last_changes.rename(columns={
        'Date': 'Last Change Date',
        'Columns Changed': 'Last Columns Changed'
    })

    # Flag stores with changes in last 7 days
    cutoff_date = (datetime.now() - timedelta(days=7)).date()
    all_data['Date'] = pd.to_datetime(all_data['Date']).dt.date
    recent_data = all_data[all_data['Date'] >= cutoff_date]
    store_changes = recent_data.groupby('StoreID')['change_flag'].any().reset_index()
    store_changes.rename(columns={'change_flag': 'change_in_last_7_days'}, inplace=True)

    # Merge flags and last change info back to current data
    data = data.merge(store_changes, on='StoreID', how='left')
    data = data.merge(last_changes, on='StoreID', how='left')

    # Ensure string types for JSON serialization
    data[['Last Change Date', 'Last Columns Changed']] = data[['Last Change Date', 'Last Columns Changed']].fillna('').astype(str)

    return data


# ---------------------- DATA CLEANING ----------------------

def data_cleaning(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean latitude and longitude columns.
    - Remove commas and convert to string
    """
    data['Latitude'] = data['Latitude'].astype(str).str.replace(',', '')
    data['Longitude'] = data['Longitude'].astype(str).str.replace(',', '')
    return data


# ---------------------- MAIN FUNCTION ----------------------

def get_store_data() -> pd.DataFrame:
    """
    Master function to:
    - Scrape all op shop chains
    - Detect changes
    - Flag recent changes
    - Save current and historical data
    - Return combined DataFrame
    """
    # Scrape stores
    salvos_data = get_salvos_stores()
    stc_data = get_stc_stores()

    # Combine into one DataFrame
    all_stores = salvos_data + stc_data
    df = pd.json_normalize(all_stores)

    # Clean lat/lon
    df = data_cleaning(df)

    # Detect changes from previous scrape
    df = check_changes(df)

    # Track last changes and recent changes
    df = check_history_changes(df)

    # Save historical data
    save_history(df)

    # Sort alphabetically by suburb
    df.sort_values('Suburb', inplace=True)

    # Save output to JSON
    with open('output.json', 'w') as f:
        json.dump(df.to_dict(orient='records'), f, indent=2)

    return df


# ---------------------- RUN SCRIPT ----------------------
if __name__ == "__main__":
    all_df = get_store_data()