import streamlit as st
import pandas as pd
from google.cloud import storage
import json
from datetime import datetime, timedelta
import pytz

tz = pytz.timezone('Australia/Sydney')
today = datetime.now(tz)

st.set_page_config(page_title="Inventory Tracking and Change Detection - Metro Ford", layout='wide')

@st.cache_data(ttl=3600*6)
def get_data():
    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('inventory_current.json')

    if blob.exists():
        records = json.loads(blob.download_as_text())
    else:
        records = []
    
    df = pd.DataFrame(records)

    return df

@st.cache_data(ttl=3600*6)
def get_summary_data():
    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('summary_data.json')

    if blob.exists():
        records = json.loads(blob.download_as_text())
    else:
        records = []
    
    df = pd.DataFrame(records)

    return df

@st.cache_data(ttl=3600*6)
def get_removed_data():
    client = storage.Client()
    bucket = client.bucket('metroford')
    blob = bucket.blob('inventory_removed.json')

    if blob.exists():
        records = json.loads(blob.download_as_text())
    else:
        records = []
    
    df = pd.DataFrame(records)

    return df

df = get_data()
summary_df = get_summary_data()
removed_df = get_removed_data()

def highlight_changes(row):
    color = ''
    cutoff_date = (today - timedelta(days=7)).date()
    if row['Last Change Date'] is not None and pd.to_datetime(row['Last Change Date']).date() > cutoff_date:
        color = 'background-color: #615fff33'
    return [color] * len(row)

def highlight_removed(row):
    color = ''
    cutoff_date = today.date()
    if row['Removed Date'] == cutoff_date:
        color = 'background-color: #615fff33'
    return [color] * len(row)

st.title('Inventory Tracking and Change Detection - Metro Ford')

st.markdown("### Inventory")

df['Vehicle'] = df.apply(
    lambda x: ' '.join(
        [str(c) for c in [x['Year'], x['Make'], x['Model'], x['Trim']] if pd.notna(c)]
    ),
    axis=1
)
df['Price'] = df['Price'].map('${:,.0f}'.format)


removed_df['Date'] = pd.to_datetime(removed_df['Date']).dt.date

cols = st.columns([1,3])
with cols[0]:
    st.metric('Today', today.strftime('%Y-%m-%d') )
    st.metric('\\# Vehicles', len(df))
    st.metric('\\# Changes Today', df['Status'].notna().sum())
    st.metric('\\# Removed Today', len(removed_df[removed_df['Date']==today.date()]))

with cols[1]:
    st.markdown('Highlights indicate changes in the past 7 days')
    st.dataframe(df[['Vehicle', 'Condition', 'Price', 'Status', 'Last Change','Last Change Date', 'VIN']].sort_values(by='Last Change Date', ascending=False).style.apply(highlight_changes, axis=1))

st.markdown("### Removed")
removed_df['Vehicle'] = removed_df.apply(
    lambda x: ' '.join(
        [str(c) for c in [x['Year'], x['Make'], x['Model'], x['Trim']] if pd.notna(c)]
    ),
    axis=1
)
removed_df['Price'] = removed_df['Price'].map('${:,.0f}'.format)
removed_df = removed_df.rename(columns={'Date': 'Removed Date'})

st.markdown('Highlights indicate vehicles removed today')
st.dataframe(removed_df[['Removed Date', 'Vehicle', 'Condition', 'Price', 'VIN']].sort_values(by='Removed Date', ascending=False).style.apply(highlight_removed, axis=1))

st.markdown("### Summary")

summary_df['Vehicle'] = summary_df.apply(
    lambda x: ' '.join(
        [str(c) for c in [x['Year'], x['Make'], x['Model']] if pd.notna(c)]
    ),
    axis=1
)

# Format price nicely
summary_df['avg_price'] = summary_df['avg_price'].map('${:,.0f}'.format)
summary_df['max_price'] = summary_df['max_price'].map('${:,.0f}'.format)
summary_df['min_price'] = summary_df['min_price'].map('${:,.0f}'.format)

summary_df = summary_df.rename(columns={
    'count': 'Count',
    'avg_price': 'Average Price',
    'max_price': 'Max Price',
    'min_price': 'Min Price'
})

#sort
summary_df_sorted = summary_df[['Vehicle', 'Count', 'Average Price', 'Max Price', 'Min Price']].sort_values(by='Count', ascending=False).reset_index(drop=True)
st.dataframe(summary_df_sorted)