from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import pandas as pd
from datetime import datetime
import streamlit as st
import os
import requests
import re
import json

from geopy.geocoders import Nominatim

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
    
CACHE_FILE = 'geocode_cache.json'
SALVOS_FILE = 'salvos_stores.json'

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        geocode_cache = json.load(f)
else:
    geocode_cache = {}

geolocator = Nominatim(user_agent="opshop_locator")

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

now = datetime.now()
formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")

def get_salvos_stores():
    if os.path.exists(SALVOS_FILE):
        with open(SALVOS_FILE, 'r') as f:
            salvos_stores = json.load(f)
    else:
        # ## Selenium for Salvos website 
        # driver = webdriver.Chrome()
        # driver.get("https://www.salvosstores.com.au/stores")

        # # Execute JS inside the browser context to fetch the JSON
        # salvos_stores = driver.execute_script("""
        # return fetch('/api/uplister/store-list')
        #     .then(response => response.json())
        # """)

        # print(len(salvos_stores))  # total stores
        # driver.quit()

        # with open(SALVOS_FILE, 'w') as f:
        #     json.dump(salvos_stores, f)
        salvos_stores = {
            "1": {
                "EnablePickUp": 0,
                "FeaturedProducts": [],
                "FullAddress": "Units 3&4/38-40 Weedon Close<br>Belconnen ACT 2617",
                "GoogleMapLink": "https://www.google.com/maps/dir//38+Weedon+Cl,+Belconnen+ACT+2617/@-35.2418099,149.0608735",
                "HiddenStore": 0,
                "Images": [],
                "Introduction": None,
                "LastEdited": "2025-09-29 09:36:13",
                "Latitude": "-35.2418099",
                "Longitude": "149.0608735",
                "Name": "Belconnen",
                "Number": "Units 3&4/38-40",
                "OnlineOnly": 0,
                "OpeningDate": None,
                "OpeningHours": {
                    "Friday": {
                        "Closing": "17:30:00",
                        "Opening": "09:00:00"
                    },
                    "Monday": {
                        "Closing": "17:30:00",
                        "Opening": "09:00:00"
                    },
                    "Saturday": {
                        "Closing": "17:00:00",
                        "Opening": "09:00:00"
                    },
                    "Sunday": "Close",
                    "Thursday": {
                        "Closing": "17:30:00",
                        "Opening": "09:00:00"
                    },
                    "Tuesday": {
                        "Closing": "17:30:00",
                        "Opening": "09:00:00"
                    },
                    "Wednesday": {
                        "Closing": "17:30:00",
                        "Opening": "09:00:00"
                    }
                },
                "Phone": "(02) 6251 0843",
                "Postcode": "2617",
                "SaleorId": "V2FyZWhvdXNlOmU3ZjRlOWRmLTY3MTgtNDdhYi1hMjM5LTU1NjM2NjRhYmZiNQ==",
                "SeoCopyLeft": None,
                "SeoCopyRight": None,
                "StateAbbreviation": "ACT",
                "StateName": "Australian Capital Territory",
                "StoreID": "8607",
                "StoreLink": "https://uplister.com.au/stores/act/2617-belconnen-8607",
                "StreetName": "Weedon",
                "StreetType": "Close",
                "SuburbName": "Belconnen",
                "URL": "https://uplister.com.au/act/2617-belconnen-8607",
                "VirtualTourLink": None,
                "isBooksToysCDs": 1,
                "isClosed": 0,
                "isClothing": 1,
                "isElectricalGoods": 1,
                "isFurniture": 0,
                "isHomewares": 1,
                "isNewMattresses": 1,
                "isOpeningSoon": 0,
                "isPermanentlyClosed": 0,
                "isStreetBoutique": 0,
                "isSundayDonation": 0
            }
        }


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
                'Store': 'Save The Children',
                'StoreID': '',
                'Suburb': name,
                'Address': address,
                'Latitude': lat,
                'Longitude': lon,
                'Hours': hours
            }
        )

    return STC_data

def check_changes(data):
    dummy_changes = [
        {
        'Store': 'Save The Children',
        'StoreID': '',
        'Suburb': 'Annerley',
        'Address': '518 Ipswich Rd, Annerley, Australia',
        'Latitude': -27.5116885,
        'Longitude': 153.0320563,
        'Hours': 'Mon-Fri: 9am-4.30pm Sat-Sun: 9am-2pm'
        }
    ]
    dummy_df = pd.DataFrame(dummy_changes)
    merged_df = data.merge(dummy_df, on=['Store', 'StoreID', 'Suburb'], how='left', suffixes=('_new', '_old'))

    check_cols = ['Address', 'Hours']

    def detect_changes(row):
        if not pd.isna(row['Address_old']):
            changed_cols = [col for col in check_cols if row[f"{col}_new"] != row[f"{col}_old"]]

            row['data_changed'] = bool(changed_cols)
            row['Columns Changed'] = ', '.join(f"{col}: from {row[f'{col}_old']} to {row[f'{col}_new']}" for col in changed_cols)
        else:
            row['data_changed'] = False
            row['Columns Changed'] = ''

        return row
    
    merged_df = merged_df.apply(detect_changes, axis=1)

    data = merged_df[[
        'Store',
        'StoreID',
        'Suburb',
        'Address_new',
        'Latitude_new',
        'Longitude_new',
        'Hours_new',
        'data_changed',
        'Columns Changed'
        ]]
    
    data = data.rename(columns={'Address_new': 'Address', 'Latitude_new': 'Latitude', 'Longitude_new': 'Longitude', 'Hours_new': 'Hours'})

    return data

@st.cache_data
def get_store_data():

    store_data = get_salvos_stores()

    STC_data = get_stc_stores()

    all_stores = store_data + STC_data

    all_df = pd.json_normalize(all_stores)

    all_df = check_changes(all_df)

    all_df.sort_values('Suburb', ascending=True, inplace=True)

    return all_df

