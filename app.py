import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pytz
import numpy as np

# 頁面設定
st.set_page_config(page_title="Asset Analysis Dashboard", layout="wide")

# 語言選擇
language = st.sidebar.selectbox(
    "Language / 語言 / 言語",
    options=["English", "中文 (繁體)", "中文 (简体)", "日本語"],
    index=0
)

# 文字對應
text = {
    "title": {
        "English": "Asset Analysis Dashboard",
        "中文 (繁體)": "資產分析儀表板",
        "中文 (简体)": "资产分析仪表板",
        "日本語": "資産分析ダッシュボード"
    },
    "select_assets": {
        "English": "Select Assets",
        "中文 (繁體)": "選擇資產",
        "中文 (简体)": "选择资产",
        "日本語": "資産を選択"
    },
    "time_range": {
        "English": "Select Time Range",
        "中文 (繁體)": "選擇時間範圍",
        "中文 (简体)": "选择时间范围",
        "日本語": "期間を選択"
    },
    "theme": {
        "English": "Theme Mode",
        "中文 (繁體)": "主題模式",
        "中文 (简体)": "主题模式",
        "日本語": "テーマモード"
    },
    "last_updated": {
        "English": "Last Updated",
        "中文 (繁體)": "最後更新",
        "中文 (简体)": "最后更新",
        "日本語": "最終更新"
    },
    "no_data": {
        "English": "⚠️ No data available for selected assets and time range.",
        "中文 (繁體)": "⚠️ 選擇的資產或時間範圍沒有數據。",
        "中文 (简体)": "⚠️ 选择的资产或时间范围没有数据。",
        "日本語": "⚠️ 選択された資産または期間にデータがありません。"
    }
}

st.title(text["title"][language])

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
    text["select_assets"][language],
    options=list(asset_options.keys()),
    default=["BTC-USD", "GLD", "COIN"],
    format_func=lambda x: asset_options[x]
)

if not selected_assets:
    st.warning(text["no_data"][language])
    st.stop()

time_range = st.sidebar.selectbox(
    text["time_range"][language],
    options=["7 Days", "30 Days", "180 Days", "365 Days"],
    index=3
)
time_map = {"7 Days": 7, "30 Days": 30, "180 Days": 180, "365 Days": 365}
days = time_map[time_range]

theme = st.sidebar.radio(text["theme"][language], ["Light", "Dark"], index=0)
if theme == "Dark":
    plt.style.use('dark_background')
    background_color = '#0e1117'
    grid_color = 'gray'
    text_color = 'white'
else:
    plt.style.use('default')
    background_color = 'white'
    grid_color = 'lightgray'
    text_color = 'black'

end_date = datetime.today()
start_date = end_date - timedelta(days=days)
fetch_time_utc = datetime.utcnow()
local_timezone = pytz.timezone("Asia/Taipei")
fetch_time_local = fetch_time_utc.astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")

data = {}
for symbol in selected_assets:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    if not hist.empty:
        data[symbol] = hist["Close"]

if not data:
    st.warning(text["no_data"][language])
    st.stop()

price_df = pd.DataFrame(data).ffill().bfill()
if price_df.empty:
    st.warning(text["no_data"][language])
    st.stop()

returns = price_df.pct_change().dropna()

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
ax.text(1.0, 1.02, f"{text['last_updated'][language]}: {fetch_time_local}",
        transform=ax.transAxes, ha='right', va='bottom', fontsize=6, color=text_color)
st.pyplot(fig)

st.subheader("Correlation Heatmap")
corr = returns.corr()
fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax2)
st.pyplot(fig2)