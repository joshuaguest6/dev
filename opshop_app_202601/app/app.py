import streamlit as st
import pandas as pd
from google.cloud import storage
import json

st.set_page_config(page_title="Op Shop Monitor", layout='wide')

@st.cache_data(ttl=3600*6)
def get_store_data():
    client = storage.Client()
    bucket = client.bucket('op-shop-data')
    blob = bucket.blob('stores_current.json')

    if blob.exists():
        records = json.loads(blob.download_as_text())
    else:
        records = []
    
    df = pd.DataFrame(records, columns=["Date", "Store", "StoreID", "Suburb", "Address", "Latitude", "Longitude", "Hours", 'change_in_last_7_days', 'Last Change Date', 'Last Columns Changed'])

    return df

store_df = get_store_data()

suburbs = store_df['Suburb'].dropna().unique()
stores = store_df['Store'].dropna().unique()

if 'selected_suburbs' not in st.session_state:
    st.session_state.selected_suburbs = sorted(suburbs)

if 'selected_stores' not in st.session_state:
    st.session_state.selected_stores = sorted(stores)

if 'suburb_key' not in st.session_state:
    st.session_state.suburb_key = 'default'

DF_COLUMNS = [
    'Store', 
    'Suburb', 
    'Address', 
    'Latitude', 
    'Longitude', 
    'Hours',
    'change_in_last_7_days',
    'Last Change Date',
    'Last Columns Changed'
]



def highlight_changes(row):
    color = ''
    if row['change_in_last_7_days']:
        color = 'background-color: yellow'
    return [color] * len(row)

st.title("Op-Shop and Charity Stores Australia")

st.markdown("### List of Stores")


cols = st.columns([1,3])
with cols[0]:
    st.metric("Total stores:",len(store_df))
    st.metric("Stores with changes (7d):", store_df['change_in_last_7_days'].sum())
    st.metric("% of stores changed (7d):", f"{round(store_df['change_in_last_7_days'].sum()/len(store_df)*100, 1)}%")    
with cols[1]:
    show_changes = st.checkbox("Show only stores with recent changes")

if show_changes:
    store_df = store_df[store_df["change_in_last_7_days"] == True]

with cols[1]:
    st.dataframe(store_df.style.apply(highlight_changes, axis=1))

st.markdown("### Map of Stores")

map_colours = {
    'Salvos': [255, 0, 0],         # red
    'Save The Children': [0, 0, 255]  # blue
}
map_df = store_df[['Latitude', 'Longitude', 'Store']].copy()
map_df = map_df[~map_df['Latitude'].isin(['None']) & ~map_df['Longitude'].isin(['None'])]
map_df['colour'] = map_df['Store'].apply(lambda x: map_colours[x])
map_df = map_df.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'})
map_df['lat'] = map_df['lat'].astype(float)
map_df['lon'] = map_df['lon'].astype(float)
st.map(map_df, color='colour')
