from selenium import webdriver

import pandas as pd
import streamlit as st
from datetime import datetime
import os
import requests
import re

from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="opshop_locator")

def normalize_address(addr):
    if not addr:
        return ''
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

def get_latlon(address):
    try:
        location = geolocator.geocode(address, timeout=10)
        if not location:
            # Retry: drop first part (like a store name)
            parts = address.split(',', 1)
            if len(parts) > 1:
                location = geolocator.geocode(parts[1].strip(), timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print("Error:", e)
        return None, None
    
def clean_address(addr):
    if not addr:
        return ''
    # Replace newline and parentheses pattern: "X\r\n (Y)" → "X, Y"
    addr = re.sub(r'\r?\n\s*\((.*?)\)', r', \1', addr)
    # Also handle "X (Y)" → "X, Y"
    addr = re.sub(r'\s*\((.*?)\)', r', \1', addr)
    return addr.strip()

file_path = 'salvos_stores.csv'
write_header = not os.path.exists(file_path)

now = datetime.now()
formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")

@st.cache_data
def get_store_data():

    ## Selenium for Salvos website 
    driver = webdriver.Chrome()
    driver.get("https://www.salvosstores.com.au/stores")

    # Execute JS inside the browser context to fetch the JSON
    salvos_stores = driver.execute_script("""
    return fetch('/api/uplister/store-list')
        .then(response => response.json())
    """)

    print(len(salvos_stores))  # total stores
    driver.quit()

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

            hours = []
            for day in days:
                if isinstance(oh[day], dict):
                    hours.append(f"{day}: {oh[day]['Opening']} to {oh[day]['Closing']}")
                else:
                    hours.append(f"{day}: Closed")
        else:
            hours = []

        store_data.append(
            {
                'Store': "Salvos",
                'StoreID': store_id,
                'Suburb': name,
                'Address': address,
                'Latitude': lat,
                'Longitude': lon,
                'Hours': str(hours)
            }
        )

    STC_stores[4]

    STC_data = []
    for item in STC_stores:
        name = item['title']
        address = normalize_address(clean_address(item['excerpt']))
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

    len(store_data)
    len(STC_data)
    STC_data[7]
    # get_latlon('Stockland Riverton, Corner of High Road and Willeri Drive, Riverton')
    # get_latlon('20-21 Bankstown City Plaza, Bankstown')
    # get_latlon('107-109 Main St, Blacktown')
    # 3: 'address': 'Stockland Riverton, Cnr High Road and Willeri Drive, Riverton', 'latitude': None, 'longitude': None
    # 5: 'address': 'Ground Floor, 20-21 Bankstown City Plaza, Bankstown', 'latitude': None, 'longitude': None,
    # 7: 'address': '1/107-109 Main St, Blacktown', 'latitude': None, 'longitude': None

    # len([i['latitude'] for i in STC_data if i['latitude'] is not None])
    # 61 of 69 addresses worked 

    all_stores = store_data + STC_data

    all_df = pd.json_normalize(all_stores)
    all_df.head(10)
    all_df.sort_values('Suburb', ascending=True, inplace=True)
    all_df.tail()
    all_df.head()

    # hist_data = pd.read_csv('salvos_stores.csv')
    # hist_data['runtime'] = pd.to_datetime(hist_data['runtime'], errors='coerce')
    # recent = hist_data[hist_data['runtime'] >= pd.Timestamp.today() - pd.Timedelta(days=7)]
    # first_week_snapshot = recent.sort_values('runtime').groupby('StoreID').first().reset_index()
    # first_week_snapshot = first_week_snapshot.astype(str)

    save_data = all_df
    save_data['runtime'] = formatted_now

    all_df = all_df.astype(str)

    save_data.to_csv(
        file_path,
        mode='a',             # append mode
        header=write_header,  # only write header if file doesn’t exist
        index=False
    )

# merged = store_df.merge(first_week_snapshot, on='StoreID', suffixes=("_new", "_old"))
# # Compare columns
# merged['name_changed'] = merged['name_new'] != merged['name_old']
# merged['address_changed'] = merged['address_new'] != merged['address_old']
# merged['latitude_changed'] = merged['latitude_new'] != merged['latitude_old']
# merged['longitude_changed'] = merged['longitude_new'] != merged['longitude_old']
# merged['hours_changed'] = merged['hours_new'] != merged['hours_old']
# merged['recent_changes'] = merged[['name_changed', 'address_changed', 'hours_changed', 'latitude_changed', 'longitude_changed']].any(axis=1)

# output = merged[
#     [
#         'name_new', 
#         'address_new', 
#         'hours_new', 
#         'latitude_new', 
#         'longitude_new', 
#         'name_changed',
#         'address_changed',
#         'latitude_changed',
#         'longitude_changed',
#         'hours_changed',
#         'recent_changes'
#         ]]

# output.rename(columns={
#     'name_new': 'name ',
#     'address_new': 'address', 
#     'hours_new': 'hours', 
#     'latitude_new': 'latitude',
#     'longitude_new': 'longitude'
#     }, inplace=True)

    return all_df

