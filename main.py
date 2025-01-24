

from backtesting.test import GOOG
from backtesting import Backtest, Strategy
import pandas as pd
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import pytz
import pandas_ta as ta
from time import sleep
from binance.client import Client
import pprint
load_dotenv()
from Bollinger_EMA import Bollinger_EMA, optimize_plot_BolEMA

session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)


def get_account_balance(ticker):
    # Retrieve account balance from Bybit
    try:
        response = session.get_wallet_balance(accountType="UNIFIED",coin=ticker)  
        balance = float(response['result']['list'][0]['coin'][0]['walletBalance'])
        avail_balance = balance -float(response['result']['list'][0]['coin'][0]['totalPositionIM'])

        return balance, avail_balance
    except Exception as err:
        print(err)

def get_tickers():
    try:
        resp = session.get_tickers(category="linear")['result']['list']
        symbols = []
        for elem in resp:
            if 'USDT' in elem['symbol'] and not 'USDC' in elem['symbol']:
                symbols.append(elem['symbol'])
        return symbols
    except Exception as err:
        print(err)
    

def get_klines(symbol, interval, category, limit=200,  start = None):
    try:
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

        df['RSI'] = ta.rsi(df['Close'].astype(float), length = 14)
        df['Fast_EMA'] = ta.ema(df['Close'].astype(float), length=30)
        df['Slow_EMA'] = ta.ema(df['Close'].astype(float), length=50)

        df['ATR'] = ta.atr(df['High'].astype(float), df['Low'].astype(float),df['Close'].astype(float), length=7)

        bbands = ta.bbands(df['Close'].astype(float), length = 20, std = 2)
        df = df.join(bbands)
        return df
    
    except Exception as err:
        print(err)
def get_positions(category):
    try:
        res = session.get_positions(category = category,  settleCoin='USDT')['result']['list']
        

        data = []
        for position in res:
            data.append({
                "Contracts": f"{position['symbol']} ({position['side']})".ljust(5),
                "Qty": position["size"].ljust(5),
                "Value": f"{float(position['positionValue']):,.2f} USDT".ljust(10),
                "Entry Price": f"{float(position['avgPrice']):,.2f}".ljust(15),
                "Mark Price": f"{float(position['markPrice']):,.2f}".ljust(15),
                "Liq. Price": f"{position['liqPrice'] or 'N/A'}".ljust(15),
                "IM": f"{float(position['positionIM']):.2f}".ljust(15),
                "MM": f"{float(position['positionMM']):.2f}".ljust(15),
                "Unrealized P&L": f"{float(position['unrealisedPnl']):,.2f}".ljust(15),
                "Realized P&L": f"{float(position['curRealisedPnl']):,.2f}".ljust(15),
                "TP/SL": f"{position['takeProfit']}/{position['stopLoss']}",
            })
        df = pd.DataFrame(data)
        pd.options.display.colheader_justify = 'left'
        print("\n" + "-" * 80 + "\n")
        print(df.to_string(index=False))
        print("\n" + "-" * 80 + "\n")
        

        pos = []
        for elem in res: 
            pos.append(elem['symbol'])
        return pos
    except Exception as err:
        print(err)

def get_pnl():
    try:
        resp = session.get_closed_pnl(category="linear", limit=50)['result']['list']
        pnl = 0
        for elem in resp:
            pnl += float(elem['closedPnl'])
        return pnl
    except Exception as err:
        print(err)
def set_mode(symbol, category, leverage) :
    try:
        res = session.set_leverage(
        category=category,
        symbol=symbol,
        buyLeverage=str(leverage),
        sellLeverage=str(leverage)
)       
        print(res)
    except Exception as err:
        print(err)


def get_precisions(symbol):
    try:
        resp = session.get_instruments_info(
            category='linear',
            symbol=symbol
        )['result']['list'][0]
        price = resp['priceFilter']['tickSize']
        if '.' in price:
            price = len(price.split('.')[1])
        else:
            price = 0
        qty = resp['lotSizeFilter']['qtyStep']
        if '.' in qty:
            qty = len(qty.split('.')[1])
        else:
            qty = 0

        return price, qty
    except Exception as err:
        print(err)



def place_order(symbol, side, mysize,price, stop_loss=None, take_profit=None, leverage=10):
    price_precision = get_precisions(symbol)[0]
    qty_precision = get_precisions(symbol)[1]
    total_bal = get_account_balance('USDT')
    balance = total_bal[0]

    
    qty_before_lev = (balance*mysize)/float(price)
    qty_final = round(qty_before_lev*leverage,qty_precision)
    if side == 1:
        try:
            session.place_order(
                category = "linear",
                symbol = symbol,
                side = 'Buy',
                orderType = "Limit",
                qty = str(qty_final),
                price=str(price),
                take_profit = str(take_profit),
                stop_loss = str(stop_loss),
   
                tpslMode = 'Full'

            )
        except Exception as err:
            print(err)
    if side == -1:
        try:
            session.place_order(
                category = "linear",
                symbol = symbol,
                side = 'Sell',
                orderType = "Limit",
                qty = str(qty_final),
                price=str(price),
                take_profit = str(take_profit),
                stop_loss = str(stop_loss),

                tpslMode = 'Full'

            )
        except Exception as err:
            print(err)


###############
#STRATEGY TIME


def ema_signal(df, current_candle, backcandles=7 ):
    df_copy = df.copy()
    start = max(0, current_candle - backcandles) #starts at 0, or whatever candle we can reach . ADD 1 if we want to include current candle right?
    end = current_candle     #add 1 here too
    df_new = df_copy.iloc[start:end]

    if all(df_new['Fast_EMA'] > df_new['Slow_EMA']):
        return 1  # Uptrend
    elif all(df_new['Fast_EMA'] < df_new['Slow_EMA']):
        return -1  # Downtrend
    else:
        return 0  
    

def total_signal(df, current_candle, backcandles = 7):

    #if EMA signal is uptrend and we close under bollinger band lower, we return a BUY signal
    if (ema_signal(df, current_candle, backcandles)==1 and df['Close'].iloc[current_candle]<=df['BBL_20_2.0'].iloc[current_candle]
    ):
        return 1
    
    
    if (ema_signal(df, current_candle, backcandles)==-1 and df['Close'].iloc[current_candle]>=df['BBU_20_2.0'].iloc[current_candle]
    ):
        return -1
    return 0

def run():
#BOLLINGER EMA PARAMS
    slcoef = 2.0
    TPSLRatio = 1.7
    fast_ema_len=9
    slow_ema_len=21
    atr_val = 7
    bb_len = 20
    std = 2
    backcandles = 7

    mysize = 0.05



    
    interval = '5'
    category = 'linear'
    leverage = 5
    #symbols= get_tickers()
    max_pos = 50
    allowed_positions = ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', '1000PEPEUSDT']
    while True:
        sleep(2)
        balance, avail_balance = get_account_balance('USDT')
        print(f'Margin balance: {balance}')
        print(f'Available balance: {avail_balance}')
        pos = get_positions(category)
        
        
        #for every element in our allowed position list
        for elem in allowed_positions:
            if elem in pos:
                print(f'Already have an position for {elem}, skipping it')
                continue

            df = get_klines(elem, interval, category)
            last_row = df.iloc[-1]
           
            current_candle =last_row['Close']
            signal = total_signal(df, len(df)-1, backcandles)
           
            slatr =slcoef * df['ATR'].iloc[-1]
            print( f"{elem} {signal} || Date: {df.index[-1]} Open: {last_row['Open']} High: {last_row['High']}  Low: {last_row['Low']} Close: {last_row['Close']} ")
        


            #long position
            if signal==1 and len(pos)<max_pos:
                set_mode(elem, category, leverage)
                sleep(2)
                sl1 = current_candle - slatr
                tp1 = current_candle + slatr * TPSLRatio
                #print(f"Long SL={sl1}, TP={tp1}, Entry={self.data.Close[-1]} at {self.data.index[-1]}")
                place_order(elem, signal, mysize, current_candle, stop_loss=sl1, take_profit=tp1, leverage=leverage)
                print(f"Placed a LONG order at ${current_candle}, SL = {sl1} TP = {tp1}")
                
            elif signal==-1 and len(pos)<max_pos:      
                set_mode(elem, category, leverage)
                sleep(2)
                #Short position
                sl1 = current_candle + slatr
                tp1 = current_candle - slatr * TPSLRatio
                #print(f"Short SL={sl1}, TP={tp1}, Entry={self.data.Close[-1]}")
                place_order(elem, signal, mysize, current_candle, stop_loss=sl1, take_profit=tp1, leverage=leverage)
                print(f"Placed a LONG order at ${current_candle}, SL = {sl1} TP = {tp1}")
            
        sleep(120)
run()

# mysize = 0.05



# symbol = 'BTCUSDT'
# interval = '5'
# category = 'linear'
# leverage = 5
# symbols= get_tickers()
# max_pos = 50
# df = get_klines(symbol, interval, category)
# last_row = df.iloc[-1]

# current_candle =last_row['Close']

# set_mode(symbol, category, leverage)
# sleep(2)
# slcoef = 2.0
# TPSLRatio = 1.7
# slatr =slcoef * df['ATR'].iloc[-1]
# sl1 = current_candle - slatr
# tp1 = current_candle + slatr * TPSLRatio
# print(tp1, sl1)
# #place_order(symbol, 1, mysize, current_candle, stop_loss=sl1, take_profit=tp1, leverage=leverage)