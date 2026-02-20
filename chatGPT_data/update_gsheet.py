# Get output.json (the cleaned and formatted conversations) and put into GSHEET with tab for each month

import json
import gspread
from gspread_dataframe import set_with_dataframe
from google.auth import default
import pandas as pd

print('starting...')

gsheet = 'ChatGPT data'
sheet_name = 'data'

# Scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]


with open('output.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)

year_month_list = ['2025-02', '2025-03', '2025-04', '2025-05', '2025-06', '2025-07', '2025-08']

creds, _ = default(scope)

client = gspread.authorize(creds)

spreadsheet = client.open(gsheet)

for year_month in year_month_list:
    print(f'adding tab for {year_month}')
    try:
        sheet = spreadsheet.worksheet(year_month)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(
            year_month,
            cols=20,
            rows=1000)
        
    df_month = df[df['Year Month'] == year_month].sort_values("Create time")

    set_with_dataframe(sheet, df_month)