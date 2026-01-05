from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import os
import requests
import re
import json

from geopy.geocoders import Nominatim

now = datetime.now()
formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")

# for saving latlon, so don't have to generate it every time
CACHE_FILE = 'geocode_cache.json'

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        geocode_cache = json.load(f)
else:
    geocode_cache = {}

geolocator = Nominatim(user_agent="opshop_locator")

# function to search for address in geocode cache and return latlon
# or generate latlon
def get_latlon(address):
    if address in geocode_cache:
        return geocode_cache[address]
    
    location = geolocator.geocode(address, timeout=10)
    if not location:
        # Retry: drop first part (like a store name)
        parts = address.split(',', 1)
        if len(parts) > 1:
            location = geolocator.geocode(parts[1].strip(), timeout=10)
    if location:
        latlon = (location.latitude, location.longitude)
    else:
        latlon = (None, None)
    
    geocode_cache[address] = latlon

    with open(CACHE_FILE, 'w') as f:
        json.dump(geocode_cache, f)

    return latlon
    
# Format the raw addresses
def format_address(addr):
    if not addr:
        return ''
    # Replace newline and parentheses pattern: "X\r\n (Y)" → "X, Y"
    addr = re.sub(r'\r?\n\s*\((.*?)\)', r', \1', addr)
    # Also handle "X (Y)" → "X, Y"
    addr = re.sub(r'\s*\((.*?)\)', r', \1', addr)
    # return addr.strip()

    addr = addr.strip()

    # Expand "Cnr" → "Corner of"
    addr = re.sub(r'\bCnr\b', 'Corner of', addr, flags=re.IGNORECASE)

    # Simplify shop/unit prefixes (1/107–109 Main St → 107–109 Main St)
    addr = re.sub(r'^\d+/\s*', '', addr)

    # Remove trailing commas or stray punctuation
    addr = re.sub(r',\s*,+', ',', addr).strip(', ')

    # Always add country
    if 'Australia' not in addr:
        addr += ', Australia'

    return addr

# Scrape salvos stores
# cant access the API normally, 
# So using selenium to simulate a browser instead
def get_salvos_stores():
    ## Selenium for Salvos website 
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://www.salvosstores.com.au/stores")

    # Execute JS inside the browser context to fetch the JSON
    salvos_stores = driver.execute_script("""
    return fetch('/api/uplister/store-list')
        .then(response => response.json())
    """)

    print(len(salvos_stores))  # total stores
    driver.quit()


    store_data = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for key, value in salvos_stores.items():
        store_id = value['StoreID']
        name = value['Name']
        address = value['FullAddress']
        lat = value['Latitude'] if value['Latitude'] else None
        lon = value['Longitude'] if value['Longitude'] else None
        if 'OpeningHours' in value.keys():
            oh = value['OpeningHours']

            hours = {day: f"{oh[day]['Opening']} to {oh[day]['Closing']}" if isinstance(oh[day], dict) else 'Closed' for day in days}

        else:
            hours = {}

        store_data.append(
            {
                'Date': formatted_now,
                'Store': "Salvos",
                'StoreID': store_id,
                'Suburb': name,
                'Address': address,
                'Latitude': lat,
                'Longitude': lon,
                'Hours': ', '.join(f"{k}: {v}" for k, v in hours.items())
            }
        )

    return store_data

def get_stc_stores():
    ## Save the Children Op Shops API
    url = "https://www.savethechildren.org.au/api/opshop/getopshoplist"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/141.0.0.0 Safari/537.36",
        "Referer": "https://www.savethechildren.org.au/",
    }

    resp = requests.get(url, headers=headers)

    STC_stores = resp.json()['data']['contentData']

    STC_stores[4]

    STC_data = []
    for item in STC_stores:
        name = item['title']
        address = format_address(item['excerpt'])
        lat, lon = get_latlon(address)
        hours = item['hours']

        STC_data.append(
            {
                'Date': formatted_now,
                'Store': 'Save The Children',
                'StoreID': 'STC'+'-'+address,
                'Suburb': name,
                'Address': address,
                'Latitude': lat,
                'Longitude': lon,
                'Hours': hours
            }
        )

    return STC_data


def save_current(data):
    with open('stores_current.json', 'w') as f:
        records = data.to_dict(orient='records')
        json.dump(records, f, indent=2)


def check_changes(data):
    if os.path.exists('stores_current.json'):
        print("Opening stores_current.json")
        with open('stores_current.json', 'r') as f:
            stores_current = json.load(f)
    else:
        print('stores_current.json not found')
        stores_current = []

    print('current store hours:')
    print(f'Store ID: {stores_current[0]["StoreID"]}')
    print(f"Store hours: {stores_current[0]['Hours']}")
    dummy_changes = [
        {
            "Date": "2026-01-05 13:39:04",
            'Store': 'Save The Children',
            'StoreID': '',
            'Suburb': 'Annerley',
            'Address': '518 Ipswich Rd, Annerley, Australia',
            'Latitude': -27.5116885,
            'Longitude': 153.0320563,
            'Hours': 'Mon-Fri: 9am-4.30pm Sat-Sun: 9am-2pm'
        }
    ]
    stores_current += dummy_changes
    stores_current_df = pd.DataFrame(stores_current)
    merged_df = data.merge(stores_current_df, on=['Store','StoreID', 'Suburb'], how='left', suffixes=('_new', '_old'))

    check_cols = ['Address', 'Hours']

    def detect_changes(row):
        changed_cols = [col for col in check_cols if row[f"{col}_new"] != row[f"{col}_old"] and not pd.isna(row[f"{col}_old"])]

        row['change_flag'] = bool(changed_cols)
        row['Columns Changed'] = ', '.join(f"{col} before: {row[f'{col}_old']}\n{col} after: {row[f'{col}_new']}" for col in changed_cols)

        return row
    
    merged_df = merged_df.apply(detect_changes, axis=1)

    # replace previous scrape with current scrape
    save_current(data)

    data = merged_df[[
        'Date_new',
        'Store',
        'StoreID',
        'Suburb',
        'Address_new',
        'Latitude_new',
        'Longitude_new',
        'Hours_new',
        'change_flag',
        'Columns Changed'
        ]]
    
    data = data.rename(columns={'Date_new': 'Date', 'Address_new': 'Address', 'Latitude_new': 'Latitude', 'Longitude_new': 'Longitude', 'Hours_new': 'Hours'})

    return data

def check_history_changes(data):
    if os.path.exists('stores_history.json'):
        with open('stores_history.json', 'r') as f:
            hist = json.load(f)
    else:
        hist = []

    hist_df = pd.DataFrame(hist)
    all_data = pd.concat([data, hist_df], axis=0)

    last_changes = all_data[all_data['change_flag'] == True]
    idx = last_changes.groupby('StoreID')['Date'].idxmax()

    last_changes = last_changes.loc[idx].reset_index(drop=True)
    last_changes = last_changes[['StoreID', 'Date', 'Columns Changed']]
    last_changes = last_changes.rename(columns={'Date': 'Last Change Date', 'Columns Changed': 'Last Columns Changed'})

    cutoff_date = (datetime.now() - timedelta(days=7)).date()
    all_data['Date'] = pd.to_datetime(all_data['Date']).dt.date
    all_data = all_data[all_data['Date'] >= cutoff_date]

    store_changes = all_data.groupby('StoreID')['change_flag'].any().reset_index()
    store_changes.rename(columns={'change_flag': 'change_in_last_7_days'}, inplace=True)

    data = pd.merge(data, store_changes, on='StoreID', how='left')
    data = data.merge(last_changes, on='StoreID', how='left')

    data[['Last Change Date', 'Last Columns Changed']] = data[['Last Change Date', 'Last Columns Changed']].astype(str)
    data = data.fillna({'Last Change Date': '', 'Last Columns Changed': ''})


    return data


def data_cleaning(data):
    data['Latitude'] = data['Latitude'].astype(str).str.replace(',', '')
    data['Longitude'] = data['Longitude'].astype(str).str.replace(',', '')

    return data

def save_history(data):
    data = data[[
        'Date',
        'Store',
        'StoreID',
        'Suburb',
        'Address',
        'Latitude',
        'Longitude',
        'Hours',
        'change_flag',
        'Columns Changed'
        ]]
    data = data.to_dict(orient='records')
    if os.path.exists('stores_history.json'):
        with open('stores_history.json', 'r') as f:
            hist = json.load(f)
        hist += data
    else:
        hist = data
    with open('stores_history.json', 'w') as f:
        json.dump(hist, f, indent=2)


# @st.cache_data
def get_store_data():

    # Scrape stores and format data
    store_data = get_salvos_stores()

    # Scrape data, format address, generate latlon, format into dictionary
    STC_data = get_stc_stores()

    # Combine stores
    all_stores = store_data + STC_data

    # Convert to df
    all_df = pd.json_normalize(all_stores)

    # Clean latlon
    all_df = data_cleaning(all_df)

    all_df = check_changes(all_df)

    # check number of changes in last 7 days
    all_df = check_history_changes(all_df)

    # save history after check history, because we dont want to compare current records to themselves
    save_history(all_df)

    all_df.sort_values('Suburb', ascending=True, inplace=True)

    records = all_df.to_dict(orient='records')
    with open('output.json', 'w') as f:
        json.dump(records, f, indent=2)

    return all_df

get_store_data()
