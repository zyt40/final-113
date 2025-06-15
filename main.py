import streamlit as st
import pandas as pd
import numpy as np
from talib import SMA, RSI, BBANDS
from order_Lo8 import Record
from indicator import KBar
from chart import ChartOrder_MA, ChartOrder_RSI_1, ChartOrder_RSI_2, ChartOrder_BBANDS
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📈 技術指標策略回測平台")

st.sidebar.header("資料設定")
df = pd.read_excel("kbars_2330_2022-01-01-2024-04-09.xlsx")
df['time'] = pd.to_datetime(df['time'])
min_date = df['time'].min().date()
max_date = df['time'].max().date()
start_date = st.sidebar.date_input("選擇開始日期", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("選擇結束日期", value=max_date, min_value=min_date, max_value=max_date)

# 篩選資料
df.set_index('time', inplace=True)
df.sort_index(inplace=True)
df = df.loc[start_date:end_date]
if df.empty:
    st.error("⚠️ 資料篩選結果為空，請重新選擇日期範圍。")
    st.stop()

# 轉為 KBar 結構
Date = df.index[0].strftime("%Y%m%d")
kbar = KBar(Date, 60)
for t, p, v in zip(df.index, df['close'], df['volume']):
    kbar.AddPrice(t, p, v)
KBar_dic = {key: kbar.TAKBar[key] for key in kbar.TAKBar}
KBar_dic['product'] = np.repeat('demo', len(KBar_dic['open']))
df_ind = pd.DataFrame(KBar_dic)

# ✅ 加入這一段：計算 MA_long
df_ind['MA_long'] = df_ind['close'].rolling(window=60).mean()
df_ind['MA_short'] = df_ind['close'].rolling(window=20).mean()


# 顯示技術指標區域
with st.expander("📉 技術指標視覺化", expanded=False):
    indicators = st.multiselect("請選擇技術指標", ["MA", "RSI", "BBANDS"])
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_ind['time'], open=df_ind['open'], high=df_ind['high'],
                                 low=df_ind['low'], close=df_ind['close'], name='K線'))
    if "MA" in indicators:
        df_ind['MA_short'] = SMA(df_ind['close'], timeperiod=5)
        df_ind['MA_long'] = SMA(df_ind['close'], timeperiod=20)
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['MA_short'], mode='lines', name='MA_short'))
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['MA_long'], mode='lines', name='MA_long'))
    if "RSI" in indicators:
        df_ind['RSI'] = RSI(df_ind['close'], timeperiod=14)
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['RSI'], mode='lines', name='RSI'))
    if "BBANDS" in indicators:
        df_ind['Upper'], df_ind['Middle'], df_ind['Lower'] = BBANDS(df_ind['close'], timeperiod=20)
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['Upper'], mode='lines', name='BB Upper'))
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['Lower'], mode='lines', name='BB Lower'))
    fig.update_layout(title='技術指標視覺化', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# 使用者可視選擇回測區塊（新增所有策略）
st.sidebar.header("策略回測")
strategy = st.sidebar.selectbox("選擇策略", ["MA策略", "RSI順勢", "RSI逆勢", "布林通道"])
stoploss = st.sidebar.slider("移動停損點數", 5, 50, 10)
OrderRecord = Record()

if strategy == "MA策略":
    df_ind['MA_short'] = SMA(df_ind['close'], timeperiod=5)
    df_ind['MA_long'] = SMA(df_ind['close'], timeperiod=20)
    for i in range(1, len(df_ind)):
        if np.isnan(df_ind['MA_short'][i-1]) or np.isnan(df_ind['MA_long'][i-1]):
            continue
        if OrderRecord.GetOpenInterest() == 0:
            if df_ind['MA_short'][i-1] < df_ind['MA_long'][i-1] and df_ind['MA_short'][i] > df_ind['MA_long'][i]:
                OrderRecord.Order('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] - stoploss
            elif df_ind['MA_short'][i-1] > df_ind['MA_long'][i-1] and df_ind['MA_short'][i] < df_ind['MA_long'][i]:
                OrderRecord.Order('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] + stoploss
        elif OrderRecord.GetOpenInterest() > 0 and df_ind['close'][i] < stop:
            OrderRecord.Cover('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
        elif OrderRecord.GetOpenInterest() < 0 and df_ind['close'][i] > stop:
            OrderRecord.Cover('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
    ChartOrder_MA(KBar_dic, OrderRecord.GetTradeRecord())

elif strategy == "RSI順勢":
    df_ind['RSI_short'] = RSI(df_ind['close'], timeperiod=5)
    df_ind['RSI_long'] = RSI(df_ind['close'], timeperiod=14)
    for i in range(1, len(df_ind)):
        if np.isnan(df_ind['RSI_short'][i-1]) or np.isnan(df_ind['RSI_long'][i-1]):
            continue
        if OrderRecord.GetOpenInterest() == 0:
            if df_ind['RSI_short'][i-1] < df_ind['RSI_long'][i-1] and df_ind['RSI_short'][i] > df_ind['RSI_long'][i] and df_ind['RSI_long'][i] > 50:
                OrderRecord.Order('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] - stoploss
            elif df_ind['RSI_short'][i-1] > df_ind['RSI_long'][i-1] and df_ind['RSI_short'][i] < df_ind['RSI_long'][i] and df_ind['RSI_long'][i] < 50:
                OrderRecord.Order('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] + stoploss
        elif OrderRecord.GetOpenInterest() > 0 and df_ind['close'][i] < stop:
            OrderRecord.Cover('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
        elif OrderRecord.GetOpenInterest() < 0 and df_ind['close'][i] > stop:
            OrderRecord.Cover('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
    ChartOrder_RSI_1(KBar_dic, OrderRecord.GetTradeRecord())

elif strategy == "RSI逆勢":
    df_ind['RSI'] = RSI(df_ind['close'], timeperiod=14)
    ceil, floor = 80, 20
    for i in range(1, len(df_ind)):
        if np.isnan(df_ind['RSI'][i-1]): continue
        if OrderRecord.GetOpenInterest() == 0:
            if df_ind['RSI'][i-1] <= floor and df_ind['RSI'][i] > floor:
                OrderRecord.Order('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] - stoploss
            elif df_ind['RSI'][i-1] >= ceil and df_ind['RSI'][i] < ceil:
                OrderRecord.Order('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] + stoploss
        elif OrderRecord.GetOpenInterest() > 0 and (df_ind['close'][i] < stop or df_ind['RSI'][i] > ceil):
            OrderRecord.Cover('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
        elif OrderRecord.GetOpenInterest() < 0 and (df_ind['close'][i] > stop or df_ind['RSI'][i] < floor):
            OrderRecord.Cover('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
    ChartOrder_RSI_2(KBar_dic, OrderRecord.GetTradeRecord())

elif strategy == "布林通道":
    df_ind['Upper'], df_ind['Middle'], df_ind['Lower'] = BBANDS(df_ind['close'], timeperiod=20)
    for i in range(1, len(df_ind)):
        if np.isnan(df_ind['Middle'][i-1]): continue
        if OrderRecord.GetOpenInterest() == 0:
            if df_ind['close'][i-1] <= df_ind['Lower'][i-1] and df_ind['close'][i] > df_ind['Lower'][i]:
                OrderRecord.Order('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] - stoploss
            elif df_ind['close'][i-1] >= df_ind['Upper'][i-1] and df_ind['close'][i] < df_ind['Upper'][i]:
                OrderRecord.Order('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
                stop = df_ind['open'][i] + stoploss
        elif OrderRecord.GetOpenInterest() > 0 and df_ind['close'][i] < stop:
            OrderRecord.Cover('Sell', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
        elif OrderRecord.GetOpenInterest() < 0 and df_ind['close'][i] > stop:
            OrderRecord.Cover('Buy', 'demo', df_ind['time'][i], df_ind['open'][i], 1)
    ChartOrder_BBANDS(KBar_dic, OrderRecord.GetTradeRecord())

# 顯示績效指標
st.subheader("📊 策略績效")
st.metric("總淨利潤", f"{OrderRecord.GetTotalProfit():.2f}")
st.metric("勝率", f"{OrderRecord.GetWinRate()*100:.2f}%")
st.metric("最大回落 MDD", f"{OrderRecord.GetMDD():.2f}")
