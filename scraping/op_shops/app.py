import streamlit as st
import pandas as pd
from web_scraping import get_store_data

# def highlight_changes(row):
#     color = ''
#     if row['recent_changes']:
#         color = 'background-color: yellow'
#     return [color] * len(row)

st.title("Op-Shop and Charity Stores Australia")

st.markdown("### List of Stores")

store_df = get_store_data()



with st.sidebar:

    show_changes = st.checkbox("Show only stores with recent changes")
    
    # --- Add Suburb filter ---
    suburbs = store_df['Suburb'].dropna().unique()
    selected_suburb = st.selectbox("Filter by Suburb", ["All"] + sorted(suburbs))
    

    # --- Add Store filter ---
    stores = store_df['Store'].dropna().unique()
    selected_store = st.selectbox('Filter by Store', ['All'] + sorted(stores))

filtered_df = store_df.copy()
if selected_suburb != "All":
        filtered_df = filtered_df[filtered_df['Suburb'] == selected_suburb]

if selected_store != "All":
        filtered_df = filtered_df[filtered_df['Store'] == selected_store]
# if show_changes:
#     present_df = store_df[store_df["recent_changes"] == True]
# else:
#     present_df = store_df


st.dataframe(filtered_df[['Store', 'Suburb', 'Address', 'Latitude', 'Longitude', 'Hours']])
# st.dataframe(present_df[['Store', 'name', 'address', 'latitude', 'longitude']].style.apply(highlight_changes, axis=1))