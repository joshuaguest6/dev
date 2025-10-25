# Charity & Op-Shop Store Locator

A Streamlit app that pulls data from a list of charity and op-shop stores and presents it in an interactive table.

## Features

- Pulls store data including:
  - Store name
  - Suburb
  - Address
  - Latitude & Longitude
  - Recent changes in store data
- Highlights changed rows in Streamlit.
- Caches latitude and longitude for addresses to reduce geocoding time.
- Uses Selenium to fetch dynamic data from websites and stores it locally in a JSON file.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/joshuaguest6/dev.git
cd scraping\op_shops
```
2. Create a virutal environment and activate it
```bash
python -m venv .venv
# Command prompt
.venv\Scripts\activate.bat
```
3. Install dependencies
```bash
pip install -r requirements.txt
```

## Running the app
```bash
streamlit run app.py
```