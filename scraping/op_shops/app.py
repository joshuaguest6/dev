import streamlit as st
import pandas as pd
from web_scraping import get_store_data


store_df = get_store_data()
suburbs = store_df['Suburb'].dropna().unique()
stores = store_df['Store'].dropna().unique()

if 'allSuburbs' not in st.session_state:
    st.session_state.allSuburbs = True

if 'selected_suburbs' not in st.session_state:
    st.session_state.selected_suburbs = sorted(suburbs)

if 'selected_stores' not in st.session_state:
    st.session_state.selected_stores = sorted(stores)

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



st.markdown(f"**Total stores:** {len(store_df)}")
st.markdown(f"**Stores with recent changes:** {store_df['data_changed'].sum()}")

with st.sidebar:

    show_changes = st.checkbox("Show only stores with recent changes")

    # --- Add Suburb filter ---
    if st.checkbox('All Suburbs', key='allSuburbs'):
        selected_suburbs = st.multiselect("Filter by Suburb", options=sorted(suburbs), default=sorted(suburbs))
    else:
        selected_suburbs = st.multiselect("Filter by Suburb", options=sorted(suburbs), default=st.session_state.selected_suburbs)

    if set(selected_suburbs) != set(st.session_state.selected_suburbs):
            st.session_state.selected_suburbs = selected_suburbs

    if set(st.session_state.selected_suburbs) != set(suburbs):
        st.session_state.allSuburbs = False
        st.rerun()

    
    # --- Add Store filter ---
    selected_stores = st.multiselect('Filter by Store', options=sorted(stores), default=st.session_state.selected_stores)
    
    if set(selected_stores) != set(st.session_state.selected_stores):
        st.session_state.selected_stores = selected_stores
    
    if st.button('All Stores'):
        st.session_state.selected_stores = sorted(stores)

filtered_df = store_df[store_df['Suburb'].isin(st.session_state.selected_suburbs) & store_df['Store'].isin(st.session_state.selected_stores)]
if show_changes:
    filtered_df = filtered_df[filtered_df["data_changed"] == True]

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
