import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pytz
import numpy as np
import time
from yfinance.exceptions import YFRateLimitError

st.set_page_config(page_title="Asset Analysis Dashboard", layout="wide")
st.title("Asset Analysis Dashboard (Retry & Fixed Corr)")

asset_options = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "TSLA": "Tesla",
    "SPY": "S&P500 ETF",
    "GLD": "Gold ETF",
    "COIN": "Coinbase",
    "MSTR": "MicroStrategy"
}

selected_assets = st.sidebar.multiselect(
    "Select Assets",
    options=list(asset_options.keys()),
    default=["BTC-USD", "GLD", "COIN"],
    format_func=lambda x: asset_options[x]
)

if not selected_assets:
    st.warning("⚠️ Please select at least one asset.")
    st.stop()

if len(selected_assets) > 5:
    st.warning("⚠️ To avoid rate limits, please select 5 or fewer assets.")
    st.stop()

time_range = st.sidebar.selectbox(
    "Select Time Range",
    options=["7 Days", "30 Days", "180 Days", "365 Days"],
    index=3
)
days = {"7 Days": 7, "30 Days": 30, "180 Days": 180, "365 Days": 365}[time_range]

theme = st.sidebar.radio("Theme Mode", ["Light", "Dark"], index=0)
if theme == "Dark":
    plt.style.use("dark_background")
    background_color = "#0e1117"
    grid_color = "gray"
    text_color = "white"
else:
    plt.style.use("default")
    background_color = "white"
    grid_color = "lightgray"
    text_color = "black"

end_date = datetime.today()
start_date = end_date - timedelta(days=days)
local_timezone = pytz.timezone("Asia/Taipei")
fetch_time_local = datetime.utcnow().astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")

data = {}
for symbol in selected_assets:
    for attempt in range(3):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            if not hist.empty:
                data[symbol] = hist["Close"]
            break
        except YFRateLimitError:
            st.warning(f"⚠️ Rate limit hit while fetching {symbol}. Retrying... (attempt {attempt+1})")
            time.sleep(5)
    else:
        st.error(f"❌ Failed to fetch data for {symbol} after multiple attempts.")

if not data:
    st.error("❌ No data could be loaded due to repeated rate limiting.")
    st.stop()

price_df = pd.DataFrame(data).ffill().bfill()
if price_df.empty:
    st.warning("⚠️ No aligned data.")
    st.stop()

returns = price_df.pct_change()

# 修正的 pairwise correlation 計算函數
def pairwise_corr(df):
    assets = df.columns
    corr_matrix = pd.DataFrame(index=assets, columns=assets, dtype=float)
    for a in assets:
        for b in assets:
            pair = df[[a, b]].dropna()
            if len(pair) >= 2:
                corr_value = pair.corr().iloc[0, 1]
                corr_matrix.loc[a, b] = corr_value
            else:
                corr_matrix.loc[a, b] = np.nan
    return corr_matrix

st.subheader("Normalized Price Trend")
fig, ax = plt.subplots(figsize=(12, 5))
for symbol in price_df.columns:
    norm = price_df[symbol] / price_df[symbol].iloc[0]
    ax.plot(norm.index, norm, label=asset_options[symbol])
ax.set_title(f"Normalized Price Trend (Past {time_range})", fontsize=14, color=text_color)
ax.set_xlabel("Date", color=text_color)
ax.set_ylabel("Normalized Price", color=text_color)
ax.legend(loc="upper left")
ax.grid(True, color=grid_color)
ax.set_facecolor(background_color)
ax.tick_params(colors=text_color)
ax.text(1.0, 1.02, f"Last Updated: {fetch_time_local}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=6, color=text_color)
st.pyplot(fig)

st.subheader("Correlation Heatmap (pairwise valid data)")
corr = pairwise_corr(returns)
fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax2)
st.pyplot(fig2)