from backtesting.test import GOOG
from backtesting import Backtest, Strategy
import pandas as pd
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import pytz
load_dotenv()


from Bollinger_EMA import Bollinger_EMA, optimize_plot_BolEMA
from rsi_crossover import RSI_crossover, optimize_plot_rsi_cross

session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)



def get_account_balance(ticker):
    # Retrieve account balance from Bybit
    response = session.get_wallet_balance(accountType="UNIFIED",coin=ticker)  

    
    if response['retCode'] == 0:
        balance = response['result']['list'][0]['coin'][0]['walletBalance']

        print(f'The balance of {ticker} is: {balance}')
        return float(balance)
    else:
        print("Failed to retrieve account balance:", response['ret_msg'])
        return None
    

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



def run_bt_bolEMA():

    '''
    slcoef = 2.0
    tpsl = 1.7

    OR

    (good with margins)
    slcoef = 1.5
    tpsl = 1.0

    or sl = 1.0, tp=1.5, 
    but 1.5,1.0 is consistent

   

    '''
    print(get_account_balance('USDT'))
    symbol = 'SOLUSDT'
    interval = '5'
    category = 'linear'
    df = fetch_market_data(symbol,interval, category, 1000, 1732975860000)
    bt = Backtest(df, Bollinger_EMA, cash=10000, margin = 1/30)
    
    optimize_plot_BolEMA(bt, True)

def run_bt_rsi_crossover():

    '''
    sl = 0.1
    tp = 0.1
    oversold = 20
    overbought = 85
    '''
    print(get_account_balance('USDT'))
    symbol = 'SOLUSDT'
    interval = '5'
    category = 'linear'
    df = fetch_market_data(symbol,interval, category, 1000)
    bt = Backtest(df, RSI_crossover, cash=10000)
    optimize_plot_rsi_cross(bt, True)

if __name__ == "__main__":
    run_bt_bolEMA()