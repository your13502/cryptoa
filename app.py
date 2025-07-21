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

st.set_page_config(page_title="CryptoA with Correlation Diagnostics", layout="wide")
st.title("CryptoA Dashboard (Correlation Diagnostics Enabled)")

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

# 資料抓取
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
    overlap_matrix = pd.DataFrame(index=assets, columns=assets, dtype=int)
    for a in assets:
        for b in assets:
            pair = df[[a, b]].dropna()
            overlap_matrix.loc[a, b] = len(pair)
            if len(pair) >= 2:
                corr_matrix.loc[a, b] = pair.corr().iloc[0, 1]
            else:
                corr_matrix.loc[a, b] = np.nan
    return corr_matrix, overlap_matrix

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

# 顯示相關係數與重疊天數診斷
st.subheader("Correlation Heatmap + Diagnostics")
corr, overlap = pairwise_corr(returns)
fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax2)
st.pyplot(fig2)

# 顯示重疊天數
st.markdown("### 📊 Overlapping Valid Days (per asset pair)")
st.dataframe(overlap.astype(int))

# 顯示低相關警示
st.markdown("### 🔍 Low Correlation Insight")
for a in corr.columns:
    for b in corr.columns:
        if a != b and pd.notnull(corr.loc[a, b]):
            value = corr.loc[a, b]
            if abs(value) < 0.3:
                st.info(f"💡 **{a}** and **{b}** only have correlation = `{value:.2f}` with `{overlap.loc[a,b]}` overlapping days. Possible reason: market behavior or time mismatch.")