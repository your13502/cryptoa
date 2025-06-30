
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager

# 字體設定
font_manager.fontManager.addfont('fonts/NotoSansTC-Regular.otf')
plt.rc('font', family='Noto Sans TC')

# 語言選擇
lang = st.sidebar.selectbox('Language 語言', ['English', '繁體中文'])
dark_mode = st.sidebar.checkbox('🌙 Dark Mode')

st.set_page_config(page_title="CryptoA", layout="wide")

st.title("CryptoA - Asset Analytics")

# 資產選擇
assets = st.multiselect('Select Assets', ['BTC-USD', 'ETH-USD', 'TSLA', 'SPY', 'GLD', 'MSTR', 'COIN'], ['BTC-USD', 'ETH-USD'])

# 時間範圍
period = st.selectbox('Time Range', ['7d', '30d', '180d', '365d'], index=3)

# 資料抓取
if assets:
    data = yf.download(assets, period=period)['Adj Close']
    norm_data = data / data.iloc[0] * 100

    st.subheader('📈 Normalized Price Trend')
    plt.figure(figsize=(10,6))
    for col in norm_data.columns:
        plt.plot(norm_data.index, norm_data[col], label=col)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.title('Normalized Price Trend')
    st.pyplot(plt)

    st.subheader('🔥 Correlation Heatmap')
    corr = norm_data.corr()
    plt.figure(figsize=(8,6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    st.pyplot(plt)

    st.caption(f"Last Updated: {pd.Timestamp.now(tz='Asia/Taipei').strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning('Please select at least one asset.')
