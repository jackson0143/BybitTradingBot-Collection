from backtesting.test import GOOG
from backtesting import Backtest, Strategy
import pandas as pd
import pandas_ta as ta
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import pytz
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from time import sleep

from binance.client import Client
load_dotenv()


from Bollinger_EMA import Bollinger_EMA, optimize_plot_BolEMA
from Bollinger_EMA_2 import Bollinger_EMA2, ema_signal, total_signal, optimize_plot_BolEMA2
from rsi_crossover import RSI_crossover, optimize_plot_rsi_cross

session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)


'''
def fetch_market_data(symbol, interval, category, limit=200, start = None):

    data = session.get_kline(symbol=symbol, interval=interval, category = category, limit=limit, start = start
    )
    df = pd.DataFrame(data['result']['list'])
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']

    df['Date'] = pd.to_datetime(pd.to_numeric(df['Date']), unit='ms')
    df.set_index('Date', inplace=True)
    melbourne_tz = pytz.timezone('Australia/Melbourne')
    df.index = df.index.tz_localize('UTC').tz_convert(melbourne_tz)
    df.index = df.index.tz_localize(None)

    df = df[::-1]

    df = df.astype(float)
    return df
'''
def plot_graph(df_main):
    df = df_main.copy()
    df['pointpos'] = [
    float(row['Low']) - (float(row['High']) - float(row['Low'])) * 0.5 if row['TOTAL_SIGNAL'] == 1 else  # LONG
    float(row['High']) + (float(row['High']) - float(row['Low'])) * 0.5 if row['TOTAL_SIGNAL'] == -1 else  # SHORT
    None
    for _, row in df.iterrows()
    ]
    fig = go.Figure(data = go.Candlestick(x=df.index,
                                      open = df['Open'],
                                      high = df['High'],
                                      low = df['Low'],
                                      close = df['Close']))
    #fig.update_layout(xaxis_rangeslider_visible=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['Fast_EMA'], line=dict(color='blue'), name='Fast EMA (9)'))
    fig.add_trace(go.Scatter(x=df.index, y=df['Slow_EMA'], line=dict(color='red'), name='Slow EMA (21)'))

    fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='green', width = 1), name='Upper Band'))
    fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='orange', width = 1), name='Lower Band'))
    fig.add_scatter(x= df.index, y=df['pointpos'], mode='markers', marker=dict(size=5, color = "MediumPurple"), name = "entry")
    fig.update_layout(
        width=1200,  
        height=800  
    )

    fig.show()

    return fig


    
def fetch_market_data_binance(symbol, interval,starting_date):
    info=Client().get_historical_klines(symbol=symbol, interval=interval, start_str = starting_date)
    df = pd.DataFrame(info)
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset vol', 'Num trades', 'Taker buy base', 'Taker buy quote', 'Ignore']
    df = df.astype(float)
    
    df['Date'] = pd.to_datetime(pd.to_numeric(df['Date']), unit='ms')
    df.set_index('Date', inplace=True)
    
    melbourne_tz = pytz.timezone('Australia/Melbourne')
    df.index = df.index.tz_localize('UTC').tz_convert(melbourne_tz)
    df.index = df.index.tz_localize(None)
    return df

def run_bt_bolEMA():

    symbol = 'HIVEUSDT'
    interval = Client.KLINE_INTERVAL_5MINUTE
    category = 'linear'
    df = fetch_market_data_binance(symbol,interval, '24 january 2025')

    bt = Backtest(df, Bollinger_EMA, cash=10000, commission=0.0006, margin = 1/20, hedging=True)
    stats = bt.run()
    print(stats)
    
    
   
    #plot_graph(df)
    #sleep(2)
    #bt.plot()
    #optimize_plot_BolEMA(bt, True)


def run_bt_bolEMA2():

    symbol = 'HIVEUSDT'
    interval = Client.KLINE_INTERVAL_5MINUTE
    category = 'linear'
    backcandles= 6
    df = fetch_market_data_binance(symbol,interval, '25 january 2025')
  
    df['Fast_EMA'] = ta.ema(df['Close'], length=7)
    df['Slow_EMA'] = ta.ema(df['Close'], length=15)
    df['ATR'] = ta.atr(df['High'], df['Low'],df['Close'], length=7)
    bbands = ta.bbands(df['Close'], length = 20, std = 2)
    df = df.join(bbands)
    df['EMA_SIGNAL'] = [ema_signal(df, i,backcandles) if i >= backcandles - 1 else 0 for i in range(len(df))]
    df['TOTAL_SIGNAL'] = [total_signal(df, i,backcandles) if i >= backcandles-1 else 0 for i in range(len(df))]
    print('applying all signals done')
    

    bt = Backtest(df, Bollinger_EMA2, cash=10000, commission=0.0006, margin = 1/20, hedging=True)
    stats = bt.run()

    #stats = optimize_plot_BolEMA2(bt, True)
    
    print(stats)
    print(df[df['TOTAL_SIGNAL']!= 0].head(20))
    print(stats['_trades'])
    plot_graph(df)
    sleep(2)
    #bt.plot()
'''
def run_bt_rsi_crossover():

    symbol = 'BTCUSDT'
    interval = Client.KLINE_INTERVAL_5MINUTE
    category = 'linear'
    df = fetch_market_data_binance(symbol,interval, '1 december 2024')
    bt = Backtest(df, RSI_crossover, cash=10000)
    print(bt.run())
    
    #optimize_plot_rsi_cross(bt, True)
'''
if __name__ == "__main__":
    #symbol = 'SOLUSDT'
    #interval = Client.KLINE_INTERVAL_5MINUTE
    #category = 'linear'

    #run_bt_bolEMA()
    #run_bt_bolEMA()
    run_bt_bolEMA2()
  