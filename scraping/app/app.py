import streamlit as st
import pandas as pd
from google.cloud import storage
import json

st.set_page_config(page_title="Op Shop Monitor")

@st.cache_data(ttl=3600*6)
def get_store_data():
    client = storage.Client()
    bucket = client.bucket('op-shop-data')
    blob = bucket.blob('stores_current.json')

    if blob.exists():
        records = json.loads(blob.download_as_text())
    else:
        records = []
    
    df = pd.DataFrame(records, columns=["Date", "Store", "StoreID", "Suburb", "Address", "Latitude", "Longitude", "Hours", "change_flag", "columns_changed"])

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
    'change_flag',
    'columns_changed'
]



def highlight_changes(row):
    color = ''
    if row['change_flag']:
        color = 'background-color: yellow'
    return [color] * len(row)

st.title("Op-Shop and Charity Stores Australia")

st.markdown("### List of Stores")


cols = st.columns(2)
with cols[0]:
    st.metric("**Total stores:**",len(store_df))
    st.metric("**Stores with changes (7d):**", store_df['change_flag'].sum())
    st.metric("**% of stores changed (7d): **", f"{round(store_df['change_flag'].sum()/len(store_df)*100, 1)}%")    

with st.sidebar:

    show_changes = st.checkbox("Show only stores with recent changes")

    # --- All Suburbs button ---
    if st.button("All Suburbs", key="all_suburbs_btn"):
        st.session_state.selected_suburbs = sorted(suburbs)
        st.session_state.suburb_key = str(sorted(suburbs))
        st.rerun()

    # --- Suburb filter ---
    selected_suburbs = st.multiselect(
        "Filter by Suburb",
        options=sorted(suburbs),
        default=st.session_state.selected_suburbs,
        key=st.session_state.suburb_key
    )
    st.session_state.selected_suburbs = selected_suburbs

    
    # --- Add Store filter ---
    selected_stores = st.multiselect('Filter by Store', options=sorted(stores), default=st.session_state.selected_stores)
    
    if set(selected_stores) != set(st.session_state.selected_stores):
        st.session_state.selected_stores = selected_stores
    
    if st.button('All Stores'):
        st.session_state.selected_stores = sorted(stores)

filtered_df = store_df[store_df['Suburb'].isin(st.session_state.selected_suburbs) & store_df['Store'].isin(st.session_state.selected_stores)]
if show_changes:
    filtered_df = filtered_df[filtered_df["change_flag"] == True]

with cols[1]:
    st.dataframe(filtered_df.style.apply(highlight_changes, axis=1))

st.markdown("### Map of Stores")

map_colours = {
    'Salvos': [255, 0, 0],         # red
    'Save The Children': [0, 0, 255]  # blue
}
map_df = filtered_df[['Latitude', 'Longitude', 'Store']].copy()
map_df = map_df[~map_df['Latitude'].isin(['None']) & ~map_df['Longitude'].isin(['None'])]
map_df['colour'] = map_df['Store'].apply(lambda x: map_colours[x])
map_df = map_df.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'})
map_df['lat'] = map_df['lat'].astype(float)
map_df['lon'] = map_df['lon'].astype(float)
st.map(map_df, color='colour')
