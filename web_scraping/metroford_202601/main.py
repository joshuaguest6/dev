import requests
import pandas as pd
import json
from datetime import datetime, timedelta

NOW = datetime.now()
FORMATTED_NOW = NOW.strftime("%Y-%m-%d %H:%M:%S")

url = "https://cloud.inventorysearch.com.au/api/json/search/stocklist/"

params = {
    "filtercode": "metroford.com.au_all_stock",
    "baseURL": "https%3A%2F%2Fwww.metroford.com.au%2Fall-stock",
    "settingsHash": "302BE3545D7EDED3187382B9759511C1",
    "page": 1,
    "limit": 110
}


resp = requests.get(url, params=params)
data = resp.json()

items = []
for item in data['items']:
    details = item['Details']

    items.append({
        'Date': FORMATTED_NOW,
        'Make': details.get('Manufacturer'),
        'Model': details.get('Model'),
        'Trim': details.get('Trim'),
        'Year': details.get('ManufactureYear'),
        'Price': details.get('AdvertisedPrice'),
        'Description': details.get('Description'),
        'Condition': details.get('Condition'),
        'VIN': details.get('VIN')
    })
    

# with open('inventory_current.json', 'w') as f:
#     json.dump(items, f, indent=2)

df = pd.DataFrame(items)

# Define the columns you expect
expected_cols = ['Date', 'Make', 'Model', 'Trim', 'Year', 'Price', 'Description', 'Condition', 'VIN']

# import data for the previous run
try:
    with open('inventory_current.json', 'r') as f:
        inventory_current = json.load(f)
except:
    inventory_current = []

# Make DataFrame with expected columns even if empty
inventory_current_df = pd.DataFrame(inventory_current, columns=expected_cols)

# Merge current scrape with previous data
# full merge: so if data is new, Make_old will be null - flag that it's new
# if VIN isn't in fresh scrape - Make_new will be null - flag that it's removed
merged_df = df.merge(
    inventory_current_df, 
    on=['VIN'], 
    how='full', 
    suffixes=('_new', '_old')
)

# change detection: removed (if vin is in previous scrape but not fresh scrape)
# new (if vin is in fresh scrape but not previous scrape)
# price change (if price is different between previous scrape and fresh scrape)
merged_df['Status'] = merged_df.apply(lambda x: 'Removed' if x['Make_new'] is None else None)
merged_df['Status'] = merged_df.apply(lambda x: 'New' if x['Make_old'] is None else False)
merged_df['Status'] = merged_df.apply(lambda x: 'Price change' if x['Price_old'] != x['Price_new'] else False)

# Filter changed records into changed_df 
# TODO 'Removed' records will have None for all _new fields - figure out how to coalesce that
changed_df = merged_df[merged_df['Status'] != None]
changed_df = changed_df[[
    'Date', 'Make_new', 'Model_new', 'Trim_new', 
    'Year_new', 'Price_new', 'Description_new', 
    'Condition_new', 'VIN', 'Status'
]]

# all records from fresh scrape + removed records from previous scrape
result_df = merged_df[[
    'Date_new', 'Make_new', 'Model_new', 'Trim_new', 
    'Year_new', 'Price_new', 'Description_new', 
    'Condition_new', 'VIN', 'Status'
]].rename(columns={
    'Date_new': 'Date',
    'Make_new': 'Make', 
    'Model_new': 'Model', 
    'Trim_new': 'Trim', 
    'Year_new': 'Year', 
    'Price_new': 'Price', 
    'Description_new': 'Description', 
    'Condition_new': 'Condition'
})

try:
    with open('change_history.json', 'r') as f:
        change_history = json.load(f)
except:
    change_history = []

change_history_df = pd.DataFrame(change_history, columns=expected_cols)

all_data = pd.concat([result_df, change_history_df], axis=0, ignore_index=True)

last_changes = all_data[all_data['Status'] != None]
idx = last_changes.groupby('VIN')['Date'].idxmax()
last_changes = last_changes.iloc[idx, ['VIN', 'Date', 'Status']]
last_changes = last_changes.rename(columns={
    'Date': 'Last Change Date',
    'Status': 'Last Change'
})

result_df = result_df.merge(last_changes, on='VIN', how='full')
removed_df = result_df[result_df['Last Change'] == 'Removed']

with open('inventory_current.json', 'w') as f:
    json.dump(result_df.to_dict(orient='records'), f, indent=2)

with open('inventory_removed.json', 'w') as f:
    json.dump(removed_df.to_dict(orient='records'), f, indent=2)


changed_dict = changed_df.to_dict(orient='records')

if changed_dict:
    try:
        with open('change_history.json', 'r') as f:
            change_history = json.load(f)
    except:
        change_history = []

    change_history.append(changed_dict)

    with open('change_history.json', 'w') as f:
        json.dump(change_history, f, indent=2)