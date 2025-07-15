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

st.set_page_config(page_title="CryptoA - ETH via Alpha Vantage", layout="wide")
st.title("CryptoA Dashboard (ETH via Alpha Vantage)")

asset_options = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "GLD": "Gold ETF",
    "COIN": "Coinbase"
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

# ETH from Alpha Vantage
def fetch_eth_from_alpha_vantage():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "DIGITAL_CURRENCY_DAILY",
        "symbol": "ETH",
        "market": "USD",
        "apikey": "XR75NDTSCL5M3GST"
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    raw = r.json()
    if "Time Series (Digital Currency Daily)" not in raw:
        return None
    df = pd.DataFrame.from_dict(raw["Time Series (Digital Currency Daily)"], orient="index")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df["4a. close (USD)"].astype(float)

# 抓資料
for symbol in selected_assets:
    if symbol == "ETH-USD":
        eth_series = fetch_eth_from_alpha_vantage()
        if eth_series is not None:
            eth_series = eth_series[eth_series.index >= start_date]
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

if not data:
    st.error("❌ No data could be loaded.")
    st.stop()

price_df = pd.DataFrame(data).sort_index().ffill().bfill()
returns = price_df.pct_change()

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

st.subheader("Normalized Price Trend")
fig, ax = plt.subplots(figsize=(12, 5))
for symbol in price_df.columns:
    norm = price_df[symbol] / price_df[symbol].iloc[0]
    ax.plot(norm.index, norm, label=asset_options.get(symbol, symbol))
ax.set_title(f"Normalized Price Trend (Past {time_range})")
ax.set_xlabel("Date")
ax.set_ylabel("Normalized Price")
ax.legend(loc="upper left")
ax.grid(True)
st.pyplot(fig)

st.subheader("Correlation Heatmap")
corr = pairwise_corr(returns)
fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax2)
st.pyplot(fig2)