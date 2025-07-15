diff --git a/app.py b/app.py
index 80687f8cae4a66520e5c81600473782aad5b33b8..987baae9f7db959b29963334de617c322ad56fc5 100644
--- a/app.py
+++ b/app.py
@@ -31,70 +31,83 @@ if not selected_assets:
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
-    r = requests.get(url, params=params)
+    try:
+        r = requests.get(url, params=params, timeout=10)
+    except Exception as e:
+        st.error(f"Failed to connect to Alpha Vantage: {e}")
+        return None
     if r.status_code != 200:
+        st.error(f"Alpha Vantage returned status {r.status_code}")
         return None
     raw = r.json()
+    if "Error Message" in raw:
+        st.error(f"Alpha Vantage error: {raw['Error Message']}")
+        return None
+    if "Note" in raw:
+        st.error(raw["Note"])
+        return None
     if "Time Series (Digital Currency Daily)" not in raw:
+        st.error("Time series data not found in response")
         return None
     df = pd.DataFrame.from_dict(
         raw["Time Series (Digital Currency Daily)"], orient="index"
     )
     df.index = pd.to_datetime(df.index)
     df.sort_index(inplace=True)
     close_col = next(
         (
             c
             for c in df.columns
             if "close" in c.lower() and "usd" in c.lower()
         ),
         None,
     )
     if close_col is None:
+        st.error("No USD close price column found in Alpha Vantage data")
         return None
     return df[close_col].astype(float)
 
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
