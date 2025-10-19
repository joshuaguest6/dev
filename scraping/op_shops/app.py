import streamlit as st
import pandas as pd
from web_scraping import get_store_data

def highlight_changes(row):
    color = ''
    if row['recent_changes']:
        color = 'background-color: yellow'
    return [color] * len(row)

st.title("Salvos Stores Australia")

st.markdown("### List of Stores")

store_df = get_store_data()

show_changes = st.checkbox("Show only stores with recent changes")

if show_changes:
    present_df = store_df[store_df["recent_changes"] == True]
else:
    present_df = store_df

st.dataframe(present_df.style.apply(highlight_changes, axis=1))