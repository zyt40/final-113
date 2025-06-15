import streamlit as st
import pandas as pd
import numpy as np
import pandas_ta as ta
from order_Lo8 import Record
from indicator import KBar
from chart import ChartOrder_MA, ChartOrder_RSI_1, ChartOrder_RSI_2, ChartOrder_BBANDS
import plotly.graph_objects as go
import itertools

st.set_page_config(layout="wide")
st.title("📈 技術指標策略回測與最佳化平台")

st.sidebar.header("資料設定")
df = pd.read_excel("kbars_2330_2022-01-01-2024-04-09.xlsx")
df['time'] = pd.to_datetime(df['time'])
min_date = df['time'].min().date()
max_date = df['time'].max().date()
start_date = st.sidebar.date_input("選擇開始日期", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("選擇結束日期", value=max_date, min_value=min_date, max_value=max_date)

df.set_index('time', inplace=True)
df.sort_index(inplace=True)
df = df.loc[start_date:end_date]

if df.empty:
    st.error("⚠️ 資料篩選結果為空，請重新選擇日期範圍。")
    st.stop()

KBar_dic = df.to_dict(orient="list")
for k in KBar_dic:
    KBar_dic[k] = np.array(KBar_dic[k])
KBar_dic['product'] = np.repeat('demo', len(df))

Date = df.index[0].strftime("%Y%m%d")
kbar = KBar(Date, 60)
for t, p, v in zip(df.index, df['close'], df['volume']):
    kbar.AddPrice(t, p, v)
KBar_dic = {key: kbar.TAKBar[key] for key in kbar.TAKBar}
KBar_dic['product'] = np.repeat('demo', len(KBar_dic['open']))

df_ind = pd.DataFrame(KBar_dic)

st.sidebar.header("功能選擇")
mode = st.sidebar.radio("選擇功能模式", ["技術指標視覺化", "策略回測", "參數最佳化"])

if mode == "技術指標視覺化":
    st.header("📊 技術指標視覺化")
    indicators = st.multiselect("請選擇要疊加的指標", ["MA", "RSI", "BBANDS", "MACD"])
    if "MA" in indicators:
        df_ind['MA_long'] = ta.sma(df_ind['close'], length=20)
        df_ind['MA_short'] = ta.sma(df_ind['close'], length=5)
    if "RSI" in indicators:
        df_ind['RSI'] = ta.rsi(df_ind['close'], length=14)
        df_ind['Middle'] = 50
    if "BBANDS" in indicators:
        bb = ta.bbands(df_ind['close'], length=20)
        df_ind['Upper'] = bb['BBU_20_2.0']
        df_ind['Middle'] = bb['BBM_20_2.0']
        df_ind['Lower'] = bb['BBL_20_2.0']
    if "MACD" in indicators:
        macd = ta.macd(df_ind['close'], fast=12, slow=26, signal=9)
        df_ind['macd'] = macd['MACD_12_26_9']
        df_ind['macdsignal'] = macd['MACDs_12_26_9']
        df_ind['macdhist'] = macd['MACDh_12_26_9']

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_ind['time'], open=df_ind['open'], high=df_ind['high'], low=df_ind['low'], close=df_ind['close'], name='K線'))
    if 'MA_long' in df_ind:
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['MA_long'], mode='lines', name='MA_long'))
    if 'MA_short' in df_ind:
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['MA_short'], mode='lines', name='MA_short'))
    if 'Upper' in df_ind and 'Lower' in df_ind:
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['Upper'], mode='lines', name='BB_Upper'))
        fig.add_trace(go.Scatter(x=df_ind['time'], y=df_ind['Lower'], mode='lines', name='BB_Lower'))
    st.plotly_chart(fig, use_container_width=True)

elif mode == "策略回測":
    from 張妍婷.chart import ChartOrder_MA, ChartOrder_RSI_1, ChartOrder_RSI_2, ChartOrder_BBANDS
    st.header("📈 策略模擬回測")
    strategy = st.selectbox("選擇策略", ["MA策略", "RSI順勢", "RSI逆勢", "布林通道", "MACD策略"])
    OrderRecord = Record()
    stoploss = st.slider("移動停損點數", 5, 50, 10)

    if strategy == "MA策略":
        short = st.slider("短期均線週期", 2, 20, 5)
        long = st.slider("長期均線週期", 10, 60, 20)
        df_ind['MA_short'] = ta.sma(df_ind['close'], length=short)
        df_ind['MA_long'] = ta.sma(df_ind['close'], length=long)
        for n in range(1, len(df_ind) - 1):
            if np.isnan(df_ind['MA_short'][n-1]) or np.isnan(df_ind['MA_long'][n-1]): continue
            if OrderRecord.GetOpenInterest() == 0:
                if df_ind['MA_short'][n-1] <= df_ind['MA_long'][n-1] and df_ind['MA_short'][n] > df_ind['MA_long'][n]:
                    OrderRecord.Order('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] - stoploss
                elif df_ind['MA_short'][n-1] >= df_ind['MA_long'][n-1] and df_ind['MA_short'][n] < df_ind['MA_long'][n]:
                    OrderRecord.Order('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] + stoploss
            elif OrderRecord.GetOpenInterest() > 0 and df_ind['close'][n] < stop:
                OrderRecord.Cover('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
            elif OrderRecord.GetOpenInterest() < 0 and df_ind['close'][n] > stop:
                OrderRecord.Cover('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
        ChartOrder_MA(KBar_dic, OrderRecord.GetTradeRecord())

    elif strategy == "RSI順勢":
        long = st.slider("長期RSI", 10, 30, 14)
        short = st.slider("短期RSI", 2, 10, 5)
        df_ind['RSI_long'] = ta.rsi(df_ind['close'], length=long)
        df_ind['RSI_short'] = ta.rsi(df_ind['close'], length=short)
        for n in range(1, len(df_ind) - 1):
            if np.isnan(df_ind['RSI_long'][n-1]): continue
            if OrderRecord.GetOpenInterest() == 0:
                if df_ind['RSI_short'][n-1] <= df_ind['RSI_long'][n-1] and df_ind['RSI_short'][n] > df_ind['RSI_long'][n] and df_ind['RSI_long'][n] > 50:
                    OrderRecord.Order('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] - stoploss
                elif df_ind['RSI_short'][n-1] >= df_ind['RSI_long'][n-1] and df_ind['RSI_short'][n] < df_ind['RSI_long'][n] and df_ind['RSI_long'][n] < 50:
                    OrderRecord.Order('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] + stoploss
            elif OrderRecord.GetOpenInterest() > 0 and df_ind['close'][n] < stop:
                OrderRecord.Cover('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
            elif OrderRecord.GetOpenInterest() < 0 and df_ind['close'][n] > stop:
                OrderRecord.Cover('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
        ChartOrder_RSI_1(KBar_dic, OrderRecord.GetTradeRecord())

    elif strategy == "RSI逆勢":
        period = st.slider("RSI期數", 5, 30, 14)
        ceil = st.slider("超買界線", 70, 90, 80)
        floor = st.slider("超賣界線", 10, 30, 20)
        df_ind['RSI'] = ta.rsi(df_ind['close'], length=period)
        for n in range(1, len(df_ind) - 1):
            if np.isnan(df_ind['RSI'][n-1]): continue
            if OrderRecord.GetOpenInterest() == 0:
                if df_ind['RSI'][n-1] <= floor and df_ind['RSI'][n] > floor:
                    OrderRecord.Order('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] - stoploss
                elif df_ind['RSI'][n-1] >= ceil and df_ind['RSI'][n] < ceil:
                    OrderRecord.Order('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] + stoploss
            elif OrderRecord.GetOpenInterest() > 0 and (df_ind['close'][n] < stop or df_ind['RSI'][n] > ceil):
                OrderRecord.Cover('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
            elif OrderRecord.GetOpenInterest() < 0 and (df_ind['close'][n] > stop or df_ind['RSI'][n] < floor):
                OrderRecord.Cover('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
        ChartOrder_RSI_2(KBar_dic, OrderRecord.GetTradeRecord())

    elif strategy == "布林通道":
        period = st.slider("BBANDS期數", 10, 60, 20)
        bb = ta.bbands(df_ind['close'], length=period)
        df_ind['Upper'] = bb[f'BBU_{period}_2.0']
        df_ind['Middle'] = bb[f'BBM_{period}_2.0']
        df_ind['Lower'] = bb[f'BBL_{period}_2.0']
        for n in range(1, len(df_ind) - 1):
            if np.isnan(df_ind['Middle'][n-1]): continue
            if OrderRecord.GetOpenInterest() == 0:
                if df_ind['close'][n-1] <= df_ind['Lower'][n-1] and df_ind['close'][n] > df_ind['Lower'][n]:
                    OrderRecord.Order('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] - stoploss
                elif df_ind['close'][n-1] >= df_ind['Upper'][n-1] and df_ind['close'][n] < df_ind['Upper'][n]:
                    OrderRecord.Order('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
                    stop = df_ind['open'][n+1] + stoploss
            elif OrderRecord.GetOpenInterest() > 0 and df_ind['close'][n] < stop:
                OrderRecord.Cover('Sell', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
            elif OrderRecord.GetOpenInterest() < 0 and df_ind['close'][n] > stop:
                OrderRecord.Cover('Buy', 'demo', df_ind['time'][n+1], df_ind['open'][n+1], 1)
        ChartOrder_BBANDS(KBar_dic, OrderRecord.GetTradeRecord())

    st.subheader("📊 策略績效")
    st.metric("總淨利潤", f"{OrderRecord.GetTotalProfit():.2f}")
    st.metric("勝率", f"{OrderRecord.GetWinRate()*100:.2f}%")
    st.metric("最大回落 MDD", f"{OrderRecord.GetMDD():.2f}")
