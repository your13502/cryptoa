import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="CryptoA", layout="wide")
st.title("CryptoA - Asset Analytics")

# 語言與主題
lang = st.sidebar.selectbox('Language 語言', ['English', '繁體中文'])
dark_mode = st.sidebar.checkbox('🌙 Dark Mode')

# 資產選擇與Session State控制
all_assets = ['BTC-USD', 'GLD', 'COIN', 'ETH-USD', 'TSLA', 'SPY', 'MSTR']
default_assets = ['BTC-USD', 'GLD', 'COIN']

# Reset 所有 Session State
if st.sidebar.button('🗑️ Reset All'):
    st.session_state.clear()
    st.experimental_rerun()

# 初始化 Session State
if 'assets' not in st.session_state:
    st.session_state['assets'] = default_assets

# Multiselect
selected_assets = st.sidebar.multiselect(
    'Select Assets 選擇資產',
    options=all_assets,
    default=st.session_state['assets']
)

# 寫入 session_state
st.session_state['assets'] = selected_assets

# 時間範圍
period = st.selectbox('Time Range 時間範圍', ['7d', '30d', '180d', '365d'], index=3)

# 自動資料抓取
if selected_assets:
    with st.spinner('Downloading data...'):
        raw_data = yf.download(selected_assets, period=period, group_by='ticker', auto_adjust=True)

        if isinstance(raw_data.columns, pd.MultiIndex):
            data = pd.DataFrame()
            for ticker in selected_assets:
                try:
                    data[ticker] = raw_data[ticker]['Close']
                except:
                    st.warning(f"⚠️ No data for {ticker}")
        else:
            data = raw_data[['Close']]
            data.columns = selected_assets

        # 填補缺失值
        data = data.fillna(method='ffill')

        # 正規化
        norm_data = data / data.iloc[0] * 100

    st.subheader('📈 Normalized Price Trend 正規化價格趨勢')
    norm_df = norm_data.reset_index().melt(id_vars='Date', var_name='Asset', value_name='Normalized Price')
    fig = px.line(norm_df, x='Date', y='Normalized Price', color='Asset',
                  title='Normalized Price Trend')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('🔥 Correlation Heatmap 資產相關性')
    corr = norm_data.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    st.pyplot(plt)

    st.subheader('🛠️ Data Quality Check 資料品質檢查')
    missing = data.isna().sum().to_frame('Missing Values')
    st.dataframe(missing)

    st.caption(
        f"Last Updated 最後更新時間: {pd.Timestamp.now(tz='Asia/Taipei').strftime('%Y-%m-%d %H:%M:%S')}"
    )

else:
    st.warning('⚠️ Please select at least one asset. 請至少選擇一個資產。')