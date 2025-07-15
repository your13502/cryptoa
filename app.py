import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pytz
import numpy as np
import time
import requests

st.set_page_config(page_title="CryptoA ETH Debug", layout="wide")
st.title("CryptoA Debug Mode: ETH via CoinGecko")

asset_options = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "GLD": "Gold ETF",
    "COIN": "Coinbase",
}

selected_assets = st.sidebar.multiselect(
    "Select Assets",
    options=list(asset_options.keys()),
    default=["BTC-USD", "GLD", "COIN", "ETH-USD"],
    format_func=lambda x: asset_options[x]
)

if not selected_assets:
    st.warning("⚠️ Please select at least one asset.")
    st.stop()

time_range = st.sidebar.selectbox(
    "Select Time Range",
    options=["7 Days", "30 Days", "180 Days", "365 Days"],
    index=3
)
days = {"7 Days": 7, "30 Days": 30, "180 Days": 180, "365 Days": 365}[time_range]

end_date = datetime.today()
start_date = end_date - timedelta(days=days)
local_timezone = pytz.timezone("Asia/Taipei")
fetch_time_local = datetime.utcnow().astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")

data = {}

# ETH from CoinGecko (with normalized index)
def fetch_eth_from_coingecko(start_date, end_date):
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
    days = (end_date - start_date).days + 1
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    prices = r.json()["prices"]
    df = pd.DataFrame(prices, columns=["ts", "price"])
    df["Date"] = pd.to_datetime(df["ts"], unit="ms").dt.normalize()
    df = df.set_index("Date")
    df = df[~df.index.duplicated(keep="first")]
    return df["price"]

for symbol in selected_assets:
    if symbol == "ETH-USD":
        eth_series = fetch_eth_from_coingecko(start_date, end_date)
        if eth_series is not None:
            data["ETH-USD"] = eth_series
    else:
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                if not hist.empty:
                    hist.index = hist.index.normalize()
                    data[symbol] = hist["Close"]
                break
            except:
                time.sleep(5)
        else:
            st.error(f"❌ Failed to fetch data for {symbol}.")

# DEBUG OUTPUTS
if "ETH-USD" in data:
    st.subheader("🔍 ETH Data Preview (from CoinGecko)")
    st.write("📆 ETH index dtype:", data["ETH-USD"].index.dtype)
    st.write("📈 ETH sample data (tail):")
    st.dataframe(data["ETH-USD"].tail(10))
else:
    st.warning("⚠️ ETH-USD not in data — CoinGecko fetch may have failed.")

# 合併並印出整體結構
if not data:
    st.error("❌ No data could be loaded.")
    st.stop()

price_df = pd.DataFrame(data).sort_index().ffill().bfill()
returns = price_df.pct_change()

st.subheader("🧪 Price DF Preview")
st.write("📆 Price DF Index dtype:", price_df.index.dtype)
st.dataframe(price_df.tail())

st.subheader("🧪 Correlation Heatmap")
def pairwise_corr(df):
    assets = df.columns
    corr_matrix = pd.DataFrame(index=assets, columns=assets, dtype=float)
    for a in assets:
        for b in assets:
            pair = df[[a, b]].dropna()
            if len(pair) >= 2:
                corr_matrix.loc[a, b] = pair.corr().iloc[0, 1]
            else:
                corr_matrix.loc[a, b] = np.nan
    return corr_matrix

corr = pairwise_corr(returns)
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
st.pyplot(fig)