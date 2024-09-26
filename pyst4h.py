import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.title('Crypto Market Overview')

# Function to fetch data with error handling
def fetch_data_continuously(url, params):
    while True:
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"API error: Status {response.status_code}. Retrying...")
        except requests.exceptions.RequestException:
            st.warning("Connection issue. Retrying in 10 seconds...")
        time.sleep(10)

# Function to fetch top 500 pairs by volume
def get_top_500_pairs_by_volume():
    all_data = []
    for page in range(1, 6):  # Fetch 500 coins across 5 pages
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': 'usd',
            'order': 'volume_desc',
            'per_page': 100,
            'page': page
        }
        coins = fetch_data_continuously(url, params)
        if coins:
            all_data.extend(coins)

    df = pd.DataFrame(all_data)
    df.loc[:, 'symbol'] = df['symbol'].str.upper()  # Capitalize symbols
    df.rename(columns={'total_volume': 'Total Volume in USD'}, inplace=True)

    return df

# Cache the data to avoid refetching it unnecessarily
@st.cache_data(ttl=86400)  # Cache for 24 hours
def fetch_and_display_data():
    return get_top_500_pairs_by_volume()

# Fetch the data with a loading spinner
with st.spinner('Fetching data...'):
    pairs_df = fetch_and_display_data()

# Get the list of available columns in the DataFrame
available_columns = list(pairs_df.columns)

# Columns to display, including additional columns
columns_to_display = [
    'symbol', 'current_price', 'market_cap', 'market_cap_rank', 'fully_diluted_valuation',
    'Total Volume in USD', 'high_24h', 'low_24h', 'price_change_24h', 
    'price_change_percentage_24h', 'market_cap_change_24h', 'market_cap_change_percentage_24h',
    'circulating_supply', 'total_supply', 'max_supply', 'ath', 'ath_change_percentage', 'ath_date',
    'atl', 'atl_change_percentage', 'atl_date'
]

# Filter based on available columns in the data
columns_to_display = [col for col in columns_to_display if col in available_columns]

# Set default columns dynamically based on what is available
default_columns = ['symbol', 'current_price', 'market_cap']
default_columns = [col for col in default_columns if col in columns_to_display]

# Sidebar for column selection
st.sidebar.subheader("Select columns to display")
selected_columns = st.sidebar.multiselect('Choose columns:', columns_to_display, default=default_columns)

# Display the last updated date in the top-right corner or before the data table
st.markdown(f"#### Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", unsafe_allow_html=True)

# Convert date columns to datetime format
pairs_df['ath_date'] = pd.to_datetime(pairs_df['ath_date'], errors='coerce')
pairs_df['atl_date'] = pd.to_datetime(pairs_df['atl_date'], errors='coerce')

# Custom formatting function
def price_format(val):
    if val > 0.1:
        return '{:,.2f}'.format(val)  # Show 2 decimals if price is above 1
    elif val > 0.01:
        return '{:,.4f}'.format(val)
    elif val > 0.0001:
        return '{:,.6f}'.format(val)
    elif val > 0.000001:
        return '{:,.8f}'.format(val)
    elif val > 0.00000001:
        return '{:,.10f}'.format(val)
    elif val > 0.0000000001:
        return '{:,.12f}'.format(val)
    else:
        return '{:,.15f}'.format(val)  # Remove decimal stops if price is less than or equal to 1

# Conditional formatting for price change
if not pairs_df.empty:
    if selected_columns:
        pairs_df = pairs_df[selected_columns]

    # Apply the custom formatting for specific columns
    styled_df = pairs_df.style.format({
        'current_price': price_format,
        'high_24h': price_format,
        'low_24h': price_format,
        'ath': price_format,
        'atl': price_format,
        'market_cap': '{:,.2f}',  # Standard formatting for market_cap
        'fully_diluted_valuation': '{:,.2f}',  # Standard formatting for fully diluted valuation
        'Total Volume in USD': '{:,.2f}',  # Standard formatting for volume
        'price_change_24h': '{:,.2f}',  # Standard formatting for price change
        'price_change_percentage_24h': '{:,.2f}%',  # Standard percentage formatting
        'market_cap_change_24h': '{:,.2f}',  # Standard formatting for market cap change
        'market_cap_change_percentage_24h': '{:,.2f}%',  # Standard percentage formatting
        'ath_change_percentage': '{:,.2f}%',  # Standard percentage formatting for ATH change
        'atl_change_percentage': '{:,.2f}%',  # Standard percentage formatting for ATL change
        'circulating_supply': '{:,.2f}',  # Standard formatting for circulating supply
        'total_supply': '{:,.2f}',  # Standard formatting for total supply
        'max_supply': '{:,.2f}',  # Standard formatting for max supply
        'ath_date': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '-',  # Date formatting
        'atl_date': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '-'  # Date formatting
    }).set_properties(**{'text-align': 'center'}).set_table_styles([{
        'selector': 'th', 'props': [('text-align', 'center')]
    }])

    # Display the styled DataFrame
    st.dataframe(styled_df)
    
    # Enable data download
    csv = pairs_df.to_csv(index=False)
    st.download_button(label="Download data as CSV", data=csv, file_name='crypto_data.csv', mime='text/csv')
    
else:
    st.error("No data available to display.")

