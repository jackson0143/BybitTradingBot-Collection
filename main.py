

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
from Strategies.Bollinger_EMA import Bollinger_EMA, optimize_plot_BolEMA

session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)
def get_time():
    return pd.to_numeric(session.get_server_time()['result']['timeSecond'])


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

        #df['RSI'] = ta.rsi(df['Close'].astype(float), length = 14)
        df['Fast_EMA'] = ta.ema(df['Close'], length=7)
        df['Slow_EMA'] = ta.ema(df['Close'], length=15)
        df['ATR'] = ta.atr(df['High'], df['Low'],df['Close'], length=7)
        bbands = ta.bbands(df['Close'], length = 20, std = 2.5)
        df = df.join(bbands)
        return df
    
    except Exception as err:
        print(err)
def get_positions(category):
    try:
        res = session.get_positions(category = category,  settleCoin='USDT')['result']['list']
        if not res:
            print("\n" + "-" * 80 + "\n")
            print("No positions found.")
            print("\n" + "-" * 80 + "\n")
            return []

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
        

        pos = pos = [elem['symbol'] for elem in res]
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

        print('Successfully set leverage.')
    except Exception as err:
        print('Did not set leverage')
def set_position_mode(symbol, category, mode):
    try:
        res = session.switch_position_mode(
            category = category,
            symbol = symbol,
            mode = mode
        )
        print('Switched to Hedge mode')
    except Exception as err:
        print('Already hedge mode')
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


        max_qty = resp['lotSizeFilter']['maxMktOrderQty']

        return price, qty, max_qty
    except Exception as err:
        print(err)



def place_order(symbol, side, mysize,price, stop_loss=None, take_profit=None, leverage=10):
    price_precision = get_precisions(symbol)[0]
    qty_precision = get_precisions(symbol)[1]
    #max_qty = get_precisions(symbol)[2]
    total_bal = get_account_balance('USDT')
    balance = total_bal[0]

    mark_price = float(session.get_tickers(
        category='linear',
        symbol=symbol
    )['result']['list'][0]['markPrice'])

    
    qty_before_lev = (balance*mysize)/float(mark_price)

    qty_final = round(qty_before_lev*leverage,qty_precision)
   
    if side == 1:
        try:
            session.place_order(
                category = "linear",
                symbol = symbol,
                side = 'Buy',
                orderType = "Market",
                qty = str(qty_final),
               #price=str(price),
                take_profit = str(take_profit),
                stop_loss = str(stop_loss),
   
                tpslMode = 'Full'

            )
            print(f"Placed a LONG order at ${mark_price}, SL = {take_profit} TP = {stop_loss}")
        except Exception as err:
            print(err)
    if side == -1:
        try:
            session.place_order(
                category = "linear",
                symbol = symbol,
                side = 'Sell',
                orderType = "Market",
                qty = str(qty_final),
                #price=str(price),
                take_profit = str(take_profit),
                stop_loss = str(stop_loss),

                tpslMode = 'Full'

            )
            print(f"Placed a SHORT order at ${mark_price}, SL = {take_profit} TP = {stop_loss}")
        except Exception as err:
            print(err)


###############
#STRATEGY TIME


def ema_signal(df, current_candle, backcandles ):
    start = max(0, current_candle - backcandles)
    df_new = df.iloc[start:current_candle ]

    #if fast above slow, uptrend
    if all(df_new['Fast_EMA'] > df_new['Slow_EMA']):
        return 1  # Uptrend
    
    #if slow above fast, downtrend
    elif all(df_new['Fast_EMA'] < df_new['Slow_EMA']):
        return -1  # Downtrend
    else:
        return 0  
    

def total_signal(df, current_candle, backcandles):

    ema_sig = ema_signal(df, current_candle, backcandles)
    #if EMA signal is uptrend and we close under bollinger band lower, we return a BUY signal
    if (ema_sig==1 and df['Close'].iloc[current_candle]<=df['BBL_20_2.5'].iloc[current_candle]
    ):
        return 1
    
    
    elif (ema_sig==-1 and df['Close'].iloc[current_candle]>=df['BBU_20_2.5'].iloc[current_candle]
    ):
        return -1
    return 0
def place_order_trailstop(symbol, side, mysize,price,trailing_stop_distance, leverage=10):
    price_precision, qty_precision, max_qty = get_precisions(symbol)
    total_bal = get_account_balance('USDT')
    balance = total_bal[0]

    mark_price = float(session.get_tickers(
        category='linear',
        symbol=symbol
    )['result']['list'][0]['markPrice'])

    trailing_stop_distance_final = round(trailing_stop_distance,price_precision)
    qty_before_lev = (balance*mysize)/float(mark_price)
    qty_final = min(round(qty_before_lev*leverage,qty_precision), float(max_qty))

    
    if side == 1:
        try:
            session.place_order(
                category = "linear",
                symbol = symbol,
                side = 'Buy',
                orderType = "Market",
                qty = str(qty_final),
                #price=str(price),

                positionIdx=1,
                tpslMode = 'Full'

            )
            print(f"Placed a LONG order at ${mark_price}")
            res = session.set_trading_stop(
                category="linear",
                symbol=symbol,
                trailingStop=str(trailing_stop_distance_final),
                tpslMode="Full",
                positionIdx=1
            )
            print(f"Trailing stop set for {symbol} at distance {trailing_stop_distance_final}. Response: {res}")
        except Exception as err:
            print(err)
    if side == -1:
        try:
            session.place_order(
                category = "linear",
                symbol = symbol,
                side = 'Sell',
                orderType = "Market",
                qty = str(qty_final),
                #price=str(price),
                tpslMode = 'Full',
                positionIdx=2

            )
  
            print(f"Placed a SHORT order at ${mark_price}")
            res = session.set_trading_stop(
                category="linear",
                symbol=symbol,
                trailingStop=str(trailing_stop_distance_final),
                tpslMode="Full",
                positionIdx=2
            )
            print(f"Trailing stop set for {symbol} at distance {trailing_stop_distance_final}. Response: {res}")
        except Exception as err:
            print(err)


def run():
    #BOLLINGER EMA PARAMS
    '''
        # fast_ema_len=7
        # slow_ema_len=15
        # atr_val = 7
        # bb_len = 20
        # std = 2.5
    '''
    slcoef = 1.9
    TPSLRatio = 1.7
    backcandles = 6




    mysize = 0.05
    interval = '5'
    category = 'linear'
    leverage = 20
    n_atr = 1.7
    max_pos = 19
    allowed_positions = ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', '1000PEPEUSDT', 'XRPUSDT', 'ENAUSDT','DOGEUSDT','LTCUSDT', 'LINKUSDT', 'HIVEUSDT', 'SHIB1000USDT', 'RUNEUSDT', 'AVAXUSDT', 'POPCATUSDT', 'ONDOUSDT', 'PNUTUSDT', 'MEUSDT', 'SWARMSUSDT']
   
    print("Starting the program...")
    
    while True:
        sleep(2)
        balance, avail_balance = get_account_balance('USDT')
        print('\n')
        timestamp = pd.to_datetime(get_time(), unit='s')
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        melbourne_time = timestamp.tz_localize('UTC').tz_convert(melbourne_tz)
        melbourne_time_final = melbourne_time.tz_localize(None)
        print(f'Current time: {melbourne_time_final}')

        print(f'Margin balance: {balance}')
        print(f'Available balance: {avail_balance}')

        pos = get_positions(category)
        
        
        #for every element in our allowed position list
        for elem in allowed_positions:
            '''
            if elem in pos:
                print(f'Position for {elem} already exists, skipping...')
                continue
            '''
            df = get_klines(elem, interval, category)
            if df is None or df.empty:
                print(f"Failed to fetch data for {elem}. Skipping...")
                continue
            last_row = df.iloc[-1]
         
            current_candle =last_row['Close']
            signal = total_signal(df, len(df)-1, backcandles)

           
            trailing_stop_distance = n_atr* df['ATR'].iloc[-1]# Trailing stop in absolute terms
           
            slatr =slcoef * df['ATR'].iloc[-1]
            print( f"{elem} {signal} || Date: {df.index[-1]} Open: {last_row['Open']} High: {last_row['High']}  Low: {last_row['Low']} Close: {last_row['Close']} ")

            
            if signal==1 and len(pos)<max_pos:
                print(f"Attempting to place LONG order for {elem}. Signal: {signal}")
                try:
                    set_position_mode(elem, category, 3)
                    set_mode(elem, category, leverage)

                    sleep(2)
                    sl1 = current_candle - slatr
                    tp1 = current_candle + slatr * TPSLRatio
                    place_order_trailstop(elem, signal, mysize, current_candle,  leverage=leverage, trailing_stop_distance=trailing_stop_distance)
                    
                except Exception as e:
                    print(f"Failed to place LONG order for {elem}. Error: {e}")
            elif signal==-1 and len(pos)<max_pos:      
                print(f"Attempting to place SHORT order for {elem}. Signal: {signal}")
                try:
                    set_position_mode(elem, category, 3)
                    set_mode(elem, category, leverage)
                    sleep(2)
                    #Short position
                    sl1 = current_candle + slatr
                    tp1 = current_candle - slatr * TPSLRatio
                    place_order_trailstop(elem, signal, mysize, current_candle, leverage=leverage, trailing_stop_distance=trailing_stop_distance)
                except Exception as e:
                    print(f"Failed to place SHORT order for {elem}. Error: {e}")        
            '''

            #long position
            if signal==1 and len(pos)<max_pos:
                set_mode(elem, category, leverage)
                set_position_mode(elem, category, 3)
                sleep(2)
                sl1 = current_candle - slatr
                tp1 = current_candle + slatr * TPSLRatio
                place_order(elem, signal, mysize, current_candle, stop_loss=sl1, take_profit=tp1, leverage=leverage)
                
                
            elif signal==-1 and len(pos)<max_pos:      
                set_mode(elem, category, leverage)
                sleep(2)
                #Short position
                sl1 = current_candle + slatr
                tp1 = current_candle - slatr * TPSLRatio
                place_order(elem, signal, mysize, current_candle, stop_loss=sl1, take_profit=tp1, leverage=leverage)
            '''

        sleep(30)
run()
#set_position_mode(symbol='ENAUSDT', category='linear', mode=3)  # Hedge Mode

#place_order_trailstop('ENAUSDT', -1, 0.05,0.8745,0.0102, leverage=1)
    
#print(set_position_mode('ENAUSDT', 'linear',3 ))
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
# slcoef = 1.9
# TPSLRatio = 1.7
# slatr =slcoef * df['ATR'].iloc[-1]
# sl1 = current_candle - slatr
# tp1 = current_candle + slatr * TPSLRatio
# print(tp1, sl1)
# #place_order(symbol, 1, mysize, current_candle, stop_loss=sl1, take_profit=tp1, leverage=leverage)