import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="CryptoA", layout="wide")
st.title("CryptoA - Asset Analytics")

lang = st.sidebar.selectbox('Language 語言', ['English', '繁體中文'])
dark_mode = st.sidebar.checkbox('🌙 Dark Mode')

assets = st.multiselect(
    'Select Assets 選擇資產',
    ['BTC-USD', 'ETH-USD', 'TSLA', 'SPY', 'GLD', 'MSTR', 'COIN'],
    ['BTC-USD', 'GLD', 'COIN']
)

period = st.selectbox('Time Range 時間範圍', ['7d', '30d', '180d', '365d'], index=3)

if assets:
    with st.spinner('Downloading data...'):
        raw_data = yf.download(assets, period=period, group_by='ticker', auto_adjust=True)

        if isinstance(raw_data.columns, pd.MultiIndex):
            data = pd.DataFrame()
            for ticker in assets:
                try:
                    data[ticker] = raw_data[ticker]['Close']
                except:
                    st.warning(f"⚠️ No data for {ticker}")
        else:
            data = raw_data[['Close']]
            data.columns = assets

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