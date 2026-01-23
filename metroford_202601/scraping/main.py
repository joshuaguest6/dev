import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import numpy as np
from google.cloud import storage

NOW = datetime.now()
FORMATTED_NOW = NOW.strftime("%Y-%m-%d %H:%M:%S")

# Show all columns when printing
pd.set_option('display.max_columns', None)

# Optional: widen the display so it doesn’t wrap
pd.set_option('display.width', 500)

# Define the columns you expect
expected_cols = ['Date', 'Make', 'Model', 'Trim', 'Year', 'Price', 'Description', 'Condition', 'VIN']


def save_current(df):

    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('inventory_current.json')

    blob.upload_from_string(
        json.dumps(df.replace({np.nan: None}).to_dict(orient='records'), indent=2),
        content_type='application/json'
    )

def save_removed(removed_df):

    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('inventory_removed.json')

    if blob.exists():
        content = blob.download_as_text()
        previous_removed = json.loads(content)
    else:
        previous_removed = []

    removed_df = removed_df.replace({np.nan: None})
    removed_dict = removed_df.to_dict(orient='records')
    all_removed = previous_removed + removed_dict

    blob.upload_from_string(
        json.dumps(all_removed, indent=2),
        content_type='application/json'
    )


def save_changes(changed_df):
    changed_df = changed_df.replace({np.nan: None})
    changed_dict = changed_df.to_dict(orient='records')

    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('change_history.json')

    # Append today's changed records to history
    if blob.exists():
        content = blob.download_as_text()
        change_history = json.loads(content)
    else:
        change_history = []

    change_history += changed_dict

    blob.upload_from_string(
        json.dumps(change_history, indent=2),
        content_type='application/json'
    )


def save_history(df):

    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('inventory_history.json')

    if blob.exists():
        content = blob.download_as_text()
        history_data = json.loads(content)
    else:
        history_data = []

    output_cols = ['Date', 'Make', 'Model', 'Trim', 
        'Year', 'Price', 'Description', 
        'Condition', 'VIN', 'Status']

    history_df = pd.DataFrame(history_data, columns=output_cols)

    history_df = pd.concat([df, history_df], axis=0, ignore_index=True)

    blob.upload_from_string(
        json.dumps(history_df.replace({np.nan: None}).to_dict(orient='records'), indent=2),
        content_type = 'application/json'
    )

def save_summary(df):
    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('summary_data.json')

    blob.upload_from_string(
        json.dumps(df.to_dict(orient='records'), indent=2),
        content_type='application/json'
    )

def get_payload():
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

    return df

def change_detection(df):

    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('inventory_current.json')

    # import data for the previous run
    if blob.exists():
        content = blob.download_as_text()
        inventory_current = json.loads(content)
    else:
        inventory_current = []

    # Make DataFrame with expected columns even if empty
    inventory_current_df = pd.DataFrame(inventory_current, columns=expected_cols)

    print(f'Previous scrape shape: {inventory_current_df.shape}')

    # Merge current scrape with previous data
    # full merge: so if data is new, Make_old will be null - flag that it's new
    # if VIN isn't in fresh scrape - Make_new will be null - flag that it's removed
    merged_df = df.merge(
        inventory_current_df, 
        on=['VIN'], 
        how='outer', 
        suffixes=('_new', '_old')
    )

    print(f'Merged df shape: {merged_df.shape}')

    # change detection: removed (if vin is in previous scrape but not fresh scrape)
    # new (if vin is in fresh scrape but not previous scrape)
    # price change (if price is different between previous scrape and fresh scrape)
    merged_df['Status'] = merged_df.apply(
        lambda x: 'Removed' if pd.isna(x['Date_new'])
            else 'New' if pd.isna(x['Date_old'])
                else 'Price change' if pd.notna(x['Price_old']) 
                                    and pd.notna(x['Price_new']) 
                                    and x['Price_old'] != x['Price_new'] 
                    else np.nan,
        axis=1)
    
    print('df[df["VIN"] == "1FATP8LH6R5147468"]:')
    print(df[df['VIN'] == "1FATP8LH6R5147468"])

    print('merged_df[merged_df["VIN"] == "1FATP8LH6R5147468"]:')
    print(merged_df[merged_df['VIN'] == "1FATP8LH6R5147468"])

    # Coalesce cols and remove suffix
    base_cols = [c for c in df.columns if c != 'VIN']

    for col in base_cols:
        merged_df[col] = (
            merged_df[f'{col}_new']
            .combine_first(merged_df[f'{col}_old'])
        )

    # merged_df will contain the 'Removed' records too
    merged_df = merged_df[base_cols + ['VIN', 'Status']]

    print('Changes:')
    print(merged_df.groupby('Status')['VIN'].count())


    print(f"merged df shape: {merged_df.shape}")

    # Today's records
    df = merged_df[merged_df['Status'] != 'Removed']
    print(f'df shape: {df.shape}')

    # Records changed - to be added to history later
    changed_df = merged_df[pd.notna(merged_df['Status'])]
    print(f'changed_df shape: {changed_df.shape}')

    # Records removed today
    removed_df = merged_df[merged_df['Status'] == 'Removed']
    print(f'removed_df shape: {removed_df.shape}')

    return df, changed_df, removed_df

def check_history_changes(df):
    print('Running check_history_changes')
    print(f'df shape: {df.shape}')

    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('change_history.json')

    if blob.exists():
        content = blob.download_as_text()
        change_history = json.loadx(content)
    else:
        change_history = []

    change_history_df = pd.DataFrame(change_history, columns=['VIN', 'Date', 'Status'])
    print(f"change_history_df shape: {change_history_df.shape}")

    all_data = pd.concat([df, change_history_df], axis=0, ignore_index=True)

    last_changes = all_data[pd.notna(all_data['Status'])]

    # Find the latest change for all VINs - including today
    if not last_changes.empty:
        idx = last_changes.groupby('VIN')['Date'].idxmax()
        last_changes = last_changes.loc[idx, ['VIN', 'Date', 'Status']]
        last_changes = last_changes.rename(columns={
            'Date': 'Last Change Date',
            'Status': 'Last Change'
        })
    else:
        last_changes = pd.DataFrame([], columns=['VIN', 'Last Change Date', 'Last Change'])

    print(f'last_changes shape: {last_changes.shape}')

    print(f'df shape before merge: {df.shape}')
    df = df.merge(last_changes, on='VIN', how='left')
    print(f'df shape after merge: {df.shape}')

    return df

def summarise_data(df):
    summary_df = df.groupby(['Make', 'Model', 'Year']).agg(
        count=('VIN', 'nunique'),
        avg_price=('Price', 'mean'),
        max_price=('Price', 'max'),
        min_price=('Price', 'min'),
        median_price=('Price', 'median')
    ).reset_index()

    return summary_df

def main():
    df = get_payload()

    df, changed_df, removed_df = change_detection(df)

    df = check_history_changes(df)

    summary_df = summarise_data(df)

    save_current(df)
    save_history(df)
    if removed_df:
        save_removed(removed_df)
    if changed_df:
        save_changes(changed_df)
    save_summary(summary_df)

if __name__ == '__main__':
    main()