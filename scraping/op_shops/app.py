import streamlit as st
import pandas as pd
from web_scraping import get_store_data

DF_COLUMNS = [
    'Store', 
    'Suburb', 
    'Address', 
    'Latitude', 
    'Longitude', 
    'Hours',
    'Columns Changed'
]

def highlight_changes(row):
    color = ''
    if row['data_changed']:
        color = 'background-color: yellow'
    return [color] * len(row)

st.title("Op-Shop and Charity Stores Australia")

st.markdown("### List of Stores")

store_df = get_store_data()

st.markdown(f"**Total stores:** {len(store_df)}")
st.markdown(f"**Stores with recent changes:** {store_df['data_changed'].sum()}")

with st.sidebar:

    show_changes = st.checkbox("Show only stores with recent changes")

    # --- Add Suburb filter ---
    suburbs = store_df['Suburb'].dropna().unique()
    selected_suburb = st.multiselect("Filter by Suburb", options=sorted(suburbs), default=sorted(suburbs))
    if st.button('All Suburbs'):
        selected_suburb = sorted(suburbs)

    # --- Add Store filter ---
    stores = store_df['Store'].dropna().unique()
    selected_store = st.multiselect('Filter by Store', options=sorted(stores), default=sorted(stores))
    if st.button('All Stores'):
        selected_store = sorted(stores)

filtered_df = store_df[store_df['Suburb'].isin(selected_suburb) & store_df['Store'].isin(selected_store)]
if show_changes:
    filtered_df = filtered_df[filtered_df["data_changed"] == True]

st.dataframe(filtered_df.style.apply(highlight_changes, axis=1))
