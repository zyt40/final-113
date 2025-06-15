import mplfinance as mpf
import pandas as pd
import talib

def ChartOrder_MA(KBar_dic, TradeRecord):
    Kbar_df = pd.DataFrame(KBar_dic)
    if 'time' in Kbar_df.columns:
        Kbar_df['time'] = pd.to_datetime(Kbar_df['time'])
        Kbar_df.set_index('time', inplace=True)

    if 'MA_long' not in Kbar_df.columns:
        if 'close' in Kbar_df.columns:
            Kbar_df['MA_long'] = Kbar_df['close'].rolling(window=20).mean()
        else:
            raise KeyError("Kbar_df 中缺少 'close' 欄位，無法計算 MA_long")

    addp = [mpf.make_addplot(Kbar_df['MA_long'], color='red')]
    mpf.plot(Kbar_df, type='candle', style='charles', addplot=addp, volume=True, title="MA 策略圖")

def ChartOrder_RSI_1(KBar_dic, TradeRecord):
    Kbar_df = pd.DataFrame(KBar_dic)
    if 'time' in Kbar_df.columns:
        Kbar_df['time'] = pd.to_datetime(Kbar_df['time'])
        Kbar_df.set_index('time', inplace=True)

    if 'close' in Kbar_df.columns:
        Kbar_df['RSI'] = talib.RSI(Kbar_df['close'], timeperiod=14)
    else:
        raise KeyError("Kbar_df 中缺少 'close' 欄位，無法計算 RSI")

    addp = [mpf.make_addplot(Kbar_df['RSI'], panel=1, color='blue')]
    mpf.plot(Kbar_df, type='candle', style='charles', addplot=addp, volume=True, title="RSI 策略圖", panel_ratios=(2, 1))

def ChartOrder_RSI_2(KBar_dic, TradeRecord):
    Kbar_df = pd.DataFrame(KBar_dic)
    if 'time' in Kbar_df.columns:
        Kbar_df['time'] = pd.to_datetime(Kbar_df['time'])
        Kbar_df.set_index('time', inplace=True)

    if 'close' in Kbar_df.columns:
        Kbar_df['RSI'] = talib.RSI(Kbar_df['close'], timeperiod=7)
    else:
        raise KeyError("Kbar_df 中缺少 'close' 欄位，無法計算 RSI")

    addp = [mpf.make_addplot(Kbar_df['RSI'], panel=1, color='purple')]
    mpf.plot(Kbar_df, type='candle', style='charles', addplot=addp, volume=True, title="RSI(7) 策略圖", panel_ratios=(2, 1))

def ChartOrder_BBANDS(KBar_dic, TradeRecord):
    Kbar_df = pd.DataFrame(KBar_dic)
    if 'time' in Kbar_df.columns:
        Kbar_df['time'] = pd.to_datetime(Kbar_df['time'])
        Kbar_df.set_index('time', inplace=True)

    if 'close' in Kbar_df.columns:
        upper, middle, lower = talib.BBANDS(Kbar_df['close'], timeperiod=20)
        Kbar_df['Upper'] = upper
        Kbar_df['Middle'] = middle
        Kbar_df['Lower'] = lower
    else:
        raise KeyError("Kbar_df 中缺少 'close' 欄位，無法計算布林通道")

    addp = [
        mpf.make_addplot(Kbar_df['Upper'], color='green'),
        mpf.make_addplot(Kbar_df['Middle'], color='orange'),
        mpf.make_addplot(Kbar_df['Lower'], color='green')
    ]
    mpf.plot(Kbar_df, type='candle', style='charles', addplot=addp, volume=True, title="布林通道策略圖")
