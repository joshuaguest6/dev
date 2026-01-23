import streamlit as st
import pandas as pd
from google.cloud import storage
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Inventory and Change Detection - Metro Ford", layout='wide')

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
    cutoff_date = (datetime.now() - timedelta(days=7)).date()
    if row['Last Change Date'] is not None and pd.to_datetime(row['Last Change Date']).date() > cutoff_date:
        color = 'background-color: yellow'
    return [color] * len(row)

def highlight_removed(row):
    color = ''
    cutoff_date = datetime.now().date()
    if pd.to_datetime(row['Date']).date() == cutoff_date:
        color = 'background-color: yellow'
    return [color] * len(row)

st.title('Inventory and Change Detection - Metro Ford')

st.markdown("### Summary")
st.dataframe(summary_df)

st.markdown("### Inventory")
st.dataframe(df.style.apply(highlight_changes, axis=1))

st.markdown("### Removed")
st.dataframe(removed_df.apply(highlight_removed, axis=1))