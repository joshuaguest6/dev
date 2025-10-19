from selenium import webdriver

import pandas as pd
import streamlit as st
from datetime import datetime
import os

file_path = 'salvos_stores.csv'
write_header = not os.path.exists(file_path)

now = datetime.now()
formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")

@st.cache_data
def get_store_data():

    driver = webdriver.Chrome()
    driver.get("https://www.salvosstores.com.au/stores")

    # Execute JS inside the browser context to fetch the JSON
    stores = driver.execute_script("""
    return fetch('/api/uplister/store-list')
        .then(response => response.json())
    """)

    print(len(stores))  # total stores
    driver.quit()

    stores['100']

    store_data = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for key, value in stores.items():
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
                'StoreID': store_id,
                'name': name,
                'address': address,
                'latitude': lat,
                'longitude': lon,
                'hours': hours
            }
        )

    len(store_data)

    store_df = pd.json_normalize(store_data)
    store_df.head(10)
    store_df.sort_values('name', ascending=True, inplace=True)
    store_df.tail()
    store_df.head()

    hist_data = pd.read_csv('salvos_stores.csv')
    hist_data['runtime'] = pd.to_datetime(hist_data['runtime'], errors='coerce')
    recent = hist_data[hist_data['runtime'] >= pd.Timestamp.today() - pd.Timedelta(days=7)]
    first_week_snapshot = recent.sort_values('runtime').groupby('StoreID').first().reset_index()
    first_week_snapshot = first_week_snapshot.astype(str)

    save_data = store_df
    save_data['runtime'] = formatted_now

    store_df = store_df.astype(str)

    save_data.to_csv(
        file_path,
        mode='a',             # append mode
        header=write_header,  # only write header if file doesn’t exist
        index=False
    )

    merged = store_df.merge(first_week_snapshot, on='StoreID', suffixes=("_new", "_old"))
    # Compare columns
    merged['name_changed'] = merged['name_new'] != merged['name_old']
    merged['address_changed'] = merged['address_new'] != merged['address_old']
    merged['latitude_changed'] = merged['latitude_new'] != merged['latitude_old']
    merged['longitude_changed'] = merged['longitude_new'] != merged['longitude_old']
    merged['hours_changed'] = merged['hours_new'] != merged['hours_old']
    merged['recent_changes'] = merged[['name_changed', 'address_changed', 'hours_changed', 'latitude_changed', 'longitude_changed']].any(axis=1)

    output = merged[
        [
            'name_new', 
            'address_new', 
            'hours_new', 
            'latitude_new', 
            'longitude_new', 
            'name_changed',
            'address_changed',
            'latitude_changed',
            'longitude_changed',
            'hours_changed',
            'recent_changes'
            ]]

    output.rename(columns={
        'name_new': 'name ',
        'address_new': 'address', 
        'hours_new': 'hours', 
        'latitude_new': 'latitude',
        'longitude_new': 'longitude'
        }, inplace=True)

    return output

