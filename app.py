import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
import matplotlib.font_manager as fm

# -----------------------------
# 🎨 字體設定（支援中文、日文）
# -----------------------------
font_path = "fonts/NotoSansTC-Regular.otf"
font_prop = fm.FontProperties(fname=font_path)
rcParams['font.family'] = font_prop.get_name()

# -----------------------------
# 🌐 多語言設定
# -----------------------------
lang = st.sidebar.selectbox('Language 語言', ['English', '繁體中文'])
dark_mode = st.sidebar.checkbox('🌙 Dark Mode')

# -----------------------------
# 🏗️ 網站標題與配置
# -----------------------------
st.set_page_config(page_title="CryptoA", layout="wide")
st.title("CryptoA - Asset Analytics")

# -----------------------------
# 📦 資產選擇與時間範圍
# -----------------------------
assets = st.multiselect(
    'Select Assets 選擇資產',
    ['BTC-USD', 'ETH-USD', 'TSLA', 'SPY', 'GLD', 'MSTR', 'COIN'],
    ['BTC-USD', 'ETH-USD']
)

time_range_map = {
    '7d': '7 days',
    '30d': '30 days',
    '180d': '180 days',
    '365d': '365 days'
}
period = st.selectbox('Time Range 時間範圍', ['7d', '30d', '180d', '365d'], index=3)

# -----------------------------
# 📈 資料抓取與處理
# -----------------------------
if assets:
    with st.spinner('Downloading data...'):
        data = yf.download(assets, period=period)['Adj Close']
        norm_data = data / data.iloc[0] * 100

    # -----------------------------
    # 📊 Normalized Price Trend
    # -----------------------------
    st.subheader('📈 Normalized Price Trend 正規化價格趨勢')

    plt.figure(figsize=(10, 6))
    for col in norm_data.columns:
        plt.plot(norm_data.index, norm_data[col], label=col)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.title('Normalized Price Trend')
    plt.xlabel('Date')
    plt.ylabel('Normalized Price')
    st.pyplot(plt)

    # -----------------------------
    # 🔥 Correlation Heatmap
    # -----------------------------
    st.subheader('🔥 Correlation Heatmap 資產相關性')

    corr = norm_data.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Heatmap')
    st.pyplot(plt)

    # -----------------------------
    # ⌚ 最後更新時間
    # -----------------------------
    st.caption(
        f"Last Updated 最後更新時間: {pd.Timestamp.now(tz='Asia/Taipei').strftime('%Y-%m-%d %H:%M:%S')}"
    )

else:
    st.warning('⚠️ Please select at least one asset. 請至少選擇一個資產。')
