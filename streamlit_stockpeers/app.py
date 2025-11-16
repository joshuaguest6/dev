import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

st.set_page_config(
    page_title='Stock peer analysis dashboard',
    page_icon=':chart_with_upwards_trend:',
    layout='wide'
)

"""
# :material/query_stats: Stock peer analysis

Easily compare stocks against others in their peer group.
"""

""  # Add some space.

cols = st.columns([1,3])
STOCKS = [
    "AAPL",
    "ABBV",
    "ACN",
    "ADBE",
    "ADP",
    "AMD",
    "AMGN",
    "AMT",
    "AMZN",
    "APD",
    "AVGO",
    "AXP",
    "BA",
    "BK",
    "BKNG",
    "BMY",
    "BRK.B",
    "BSX",
    "C",
    "CAT",
    "CI",
    "CL",
    "CMCSA",
    "COST",
    "CRM",
    "CSCO",
    "CVX",
    "DE",
    "DHR",
    "DIS",
    "DUK",
    "ELV",
    "EOG",
    "EQR",
    "FDX",
    "GD",
    "GE",
    "GILD",
    "GOOG",
    "GOOGL",
    "HD",
    "HON",
    "HUM",
    "IBM",
    "ICE",
    "INTC",
    "ISRG",
    "JNJ",
    "JPM",
    "KO",
    "LIN",
    "LLY",
    "LMT",
    "LOW",
    "MA",
    "MCD",
    "MDLZ",
    "META",
    "MMC",
    "MO",
    "MRK",
    "MSFT",
    "NEE",
    "NFLX",
    "NKE",
    "NOW",
    "NVDA",
    "ORCL",
    "PEP",
    "PFE",
    "PG",
    "PLD",
    "PM",
    "PSA",
    "REGN",
    "RTX",
    "SBUX",
    "SCHW",
    "SLB",
    "SO",
    "SPGI",
    "T",
    "TJX",
    "TMO",
    "TSLA",
    "TXN",
    "UNH",
    "UNP",
    "UPS",
    "V",
    "VZ",
    "WFC",
    "WM",
    "WMT",
    "XOM",
]

DEFAULT_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META"]

# turn a list of stocks into a string
def stocks_to_str(stocks):
    return ','.join(stocks)

# Instantiate ticker_input
if 'ticker_input' not in st.session_state:
    st.session_state.ticker_input = st.query_params.get(
        'stocks', stocks_to_str(DEFAULT_STOCKS)
    ).split(',')


top_left_cell = cols[0].container(border=True, height='stretch', vertical_alignment='center')

# Create stock multiselect, with list of all unique stocks, and allow new options
with top_left_cell:
    tickers = st.multiselect(
        'Stock tickers',
        options=sorted(set(STOCKS) | set(st.session_state.ticker_input)),
        default=st.session_state.ticker_input,
        placeholder='Choose stocks to compare. Eg: NVDA',
        accept_new_options=True
    )

# Time horizon selector
horizon_map = {
    "1 Months": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
    "20 Years": "20y",
}

with top_left_cell:
    horizon = st.pills(
        'Time horizon',
        options=list(horizon_map.keys()),
        default='6 Months',
    )

tickers = [t.upper() for t in tickers]

if tickers:
    st.query_params['stocks'] = stocks_to_str(tickers)
else:
    st.query_params.pop('stocks', None)

if not tickers:
    top_left_cell.info('Pick some stocks to compare', icon=':material/info:')
    st.stop()

right_cell = cols[1].container(border=True, height='stretch', vertical_alignment='center')

@st.cache_resource(show_spinner=False, ttl='6hr')
def load_data(tickers, period):
    tickers_obj = yf.Tickers(tickers)
    data = tickers_obj.history(period)
    if data is None:
        raise('YFinance returned no data')
    return data['Close']

try:
    data = load_data(tickers, horizon_map[horizon])
except yf.exceptions.YFRateLimitError as e:
    st.warning('YFinance is rate limiting us :(\nTry again later')
    load_data.clear()
    st.stop()

empty_columns = data.columns[data.isna().all()].tolist()

if empty_columns:
    st.error(f'Error loading data for the tickers {", ".join(empty_columns)}')
    st.stop()

normalised = data.div(data.iloc[0])

latest_norm_values = {normalised[ticker].iat[-1]: ticker for ticker in tickers}
max_norm_value = max(latest_norm_values.items())
min_norm_value = min(latest_norm_values.items())

bottom_left_cell = cols[0].container(border=True, height='stretch', vertical_alignment='center')

with bottom_left_cell:
    cols = st.columns(2)
    cols[0].metric(
        'Best stock',
        max_norm_value[1],
        delta=f'{round((max_norm_value[0]-1) * 100)}%',
        width='content'
    )

    cols[1].metric(
        'Worst stock',
        min_norm_value[1],
        delta=f'{round((min_norm_value[0]-1) * 100)}%',
        width='content'
    )

with right_cell:
    st.altair_chart(
        alt.Chart(
            normalised.reset_index().melt(
                id_vars=['Date'], var_name='Stock', value_name='Normalised price'
            )
        )
        .mark_line()
        .encode(
            alt.X('Date:T'),
            alt.Y('Normalised price:Q').scale(zero=False),
            alt.Color('Stock:N')
        )
        .properties(height=400)
    )
# add two lines of white space
""
""

"""
## Individual stocks vs peer average

For the analysis below, the 'peer average' when analysing stock X always excludes X itself.

"""

if len(tickers) <= 1:
    st.warning('Pick two or more tickers to compare them')
    st.stop()

NUM_COLS = 4
cols = st.columns(NUM_COLS)

for i, ticker in enumerate(tickers):
    peers = normalised.drop(columns=[ticker])
    peer_average = peers.mean(axis=1)

    plot_data = pd.DataFrame(
        {
            'Date': normalised.index,
            ticker: normalised[ticker],
            'Peer average': peer_average
        }
    ).melt(id_vars=['Date'], var_name='Series', value_name='Price')

    chart = (
        alt.Chart(plot_data)
        .mark_line()
        .encode(
            alt.X('Date:T'),
            alt.Y('Price:Q').scale(zero=False),
            alt.Color(
                'Series:N',
                scale=alt.Scale(domain=[ticker, 'Peer average'], range=['red','gray']),
                legend=alt.Legend(orient='bottom')
            ),
            alt.Tooltip(['Date', 'Series','Price'])
        )
        .properties(title=f'{ticker} vs peer average', height = 300)
        )
    
    cell = cols[(i*2) % NUM_COLS].container(border=True)
    cell.write("")
    cell.altair_chart(chart, use_container_width=True)

    # Create delta chart
    plot_data = pd.DataFrame(
        {
            'Date': normalised.index,
            'Delta': normalised[ticker] - peer_average
        }
    )

    chart = (
        alt.Chart(plot_data)
        .mark_area()
        .encode(
            alt.X('Date:T'),
            alt.Y('Delta:Q').scale(zero=False)
        )
        .properties(title=f'{ticker} - peer average', height=300)
    )

    cell = cols[(i*2 + 1) % NUM_COLS].container(border=True)
    cell.write("")
    cell.altair_chart(chart, use_container_width=True)

    ""
""

"""
## Raw data
"""

data