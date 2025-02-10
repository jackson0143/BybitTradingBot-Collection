
import pandas as pd
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import pytz
import pandas_ta as ta
from time import sleep

from StrategiesBot.bollinger_ema import BollingerEMAStrategy


load_dotenv()




class TradingBot:
    def __init__(self, api_key, api_secret, strategy, allowed_positions,mysize,indicators=None, leverage =10 ,interval='5', category='linear'):

        """
        Initialize the trading bot with key configurations and session setup.
        """

        #Bybit connection setup
        self.session = HTTP(
            testnet=False,
            demo=True,
            api_key=api_key,
            api_secret=api_secret,
        )
        self.strategy = strategy  #strategy instance
        self.allowed_positions = allowed_positions  #list of symbols to be trading
        self.leverage = leverage    #set leverage
        self.interval = interval    #time interval for klines
        self.category = category    #which category to trade
        self.mysize = mysize        #each trade position size
        self.indicators = indicators #a list of params for the indicator (in case for each strategy we require different parameters)
    def get_time(self):
        """
        Fetch current server time
        """
        return pd.to_numeric(self.session.get_server_time()['result']['timeSecond'])


    def get_account_balance(self, ticker='USDT'):
        """
        Retrieve the current account balance and available balance
        """
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED",coin=ticker)  
            balance = float(response['result']['list'][0]['coin'][0]['walletBalance'])
            avail_balance = balance -float(response['result']['list'][0]['coin'][0]['totalPositionIM'])

            return balance, avail_balance
        except Exception as err:
            print(err)
            return 0,0

    def get_tickers(self):
        """
        Retrieve a list of symbols available for trading in the 'linear' category.
        Filters out symbols ending in USDC.
        """
        try:
            resp = self.session.get_tickers(category="linear")['result']['list']
            symbols = []
            for elem in resp:
                if 'USDT' in elem['symbol'] and not 'USDC' in elem['symbol']:
                    symbols.append(elem['symbol'])
            return symbols
        except Exception as err:
            print(err)
        

    def get_klines(self, symbol,  limit=200,  start = None):
        """
        Fetch candlestick data for a given symbol
        Adds all technical indicators that may be required, which reduces computation time in signal calculations

        returns a dataframe
        """
        try:
            data = self.session.get_kline(
                symbol=symbol,
                interval=self.interval,
                category=self.category,
                limit=limit,
                start= start
            )
            df = pd.DataFrame(data['result']['list'])
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']

            df['Date'] = pd.to_datetime(pd.to_numeric(df['Date']), unit='ms')
            df.set_index('Date', inplace=True)
            melbourne_tz = pytz.timezone('Australia/Melbourne')
            df.index = df.index.tz_localize('UTC').tz_convert(melbourne_tz).tz_localize(None)
            
            df = df[::-1].astype(float)
            if self.indicators is None:
                print(f"No indicators provided for {symbol}, returning raw DF.")
                return df

            for indicator in self.indicators:
                 self.apply_indicator(df, indicator)

            return df
        
        except Exception as err:
            print(f"Failed to fetch klines: {err}")

    def apply_indicator(self, df, indicator):
        """
        Apply a technical indicator to the DataFrame based on its type and parameters.
        """
        indicator_type = indicator['type']
        params = indicator['params']

        # apply the indicator based on its type dynamically
        if indicator_type == 'ema':
            col_name = params.get('col_name', f"EMA_{params['length']}")
            df[col_name] = ta.ema(df['Close'], length=params['length'])
        
        elif indicator_type == 'sma':
            col_name = params.get('col_name', f"SMA_{params['length']}")
            df[col_name] = ta.sma(df['Close'], length=params['length'])
        
        elif indicator_type == 'atr':
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=params['length'])
        
        elif indicator_type == 'bbands':
            bbands = ta.bbands(df['Close'], length=params['length'], std=params['std'])
            bbands.columns = ['BB_Lower', 'BB_Middle', 'BB_Upper', 'BB_BandWidth', 'BB_Percent']
            for col in bbands.columns:
                df[col] = bbands[col]

        elif indicator_type == 'rsi':
            df['RSI'] = ta.rsi(df['Close'], length=params['length'])

        else:
            print(f"Unknown indicator type: {indicator_type}")

    def get_positions(self):
        """
        Retrieve the current open positions 
        """
        try:
            res = self.session.get_positions(category = self.category,  settleCoin='USDT')['result']['list']
            if not res:
                print("\n" + "-" * 80 + "\n")
                print("No positions found.")
                print("\n" + "-" * 80 + "\n")
                return []
            positions = {}
            data = []
            for position in res:
                positions[position['symbol']] = position['side']  # 'Buy' or 'Sell''
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
        
            return positions
        except Exception as err:
            print(err)

    def get_pnl(self):
        try:
            resp = self.session.get_closed_pnl(category="linear", limit=50)['result']['list']
            pnl = 0
            for elem in resp:
                pnl += float(elem['closedPnl'])
            return pnl
        except Exception as err:
            print(err)
    def set_mode(self,symbol) :
        """
        set the leverage for the symbol
        """
        try:
            res = self.session.set_leverage(
            category=self.category,
            symbol=symbol,
            buyLeverage=str(self.leverage),
            sellLeverage=str(self.leverage)
    )       

            print('Successfully set leverage.')
        except Exception as err:
            print('Did not set leverage')
    def set_position_mode(self,symbol, mode):
        """
        set the mode to hedge mode
        """
        try:
            res = self.session.switch_position_mode(
                category = self.category,
                symbol = symbol,
                mode = mode
            )
            print('Switched to Hedge mode')
        except Exception as err:
            print('Already hedge mode')
    def get_precisions(self,symbol):
        """
        Retrieve the price and quantity precision
        """
        try:
            resp = self.session.get_instruments_info(
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



    # def place_order(self, symbol, side, mysize, stop_loss=None, take_profit=None, leverage=10):
    #     price_precision, qty_precision, max_qty = self.get_precisions(symbol)
    #     total_bal = self.get_account_balance('USDT')
    #     balance = total_bal[0]

    #     mark_price = float(self.session.get_tickers(
    #         category='linear',
    #         symbol=symbol
    #     )['result']['list'][0]['markPrice'])

        
    #     qty_before_lev = (balance*mysize)/float(mark_price)

    #     qty_final = round(qty_before_lev*leverage,qty_precision)
    
    #     if side == 1:
    #         try:
    #             self.session.place_order(
    #                 category = "linear",
    #                 symbol = symbol,
    #                 side = 'Buy',
    #                 orderType = "Market",
    #                 qty = str(qty_final),
    #             #price=str(price),
    #                 take_profit = str(take_profit),
    #                 stop_loss = str(stop_loss),
    
    #                 tpslMode = 'Full'

    #             )
    #             print(f"Placed a LONG order at ${mark_price}, SL = {take_profit} TP = {stop_loss}")
    #         except Exception as err:
    #             print(err)
    #     if side == -1:
    #         try:
    #             self.session.place_order(
    #                 category = "linear",
    #                 symbol = symbol,
    #                 side = 'Sell',
    #                 orderType = "Market",
    #                 qty = str(qty_final),
    #                 #price=str(price),
    #                 take_profit = str(take_profit),
    #                 stop_loss = str(stop_loss),

    #                 tpslMode = 'Full'

    #             )
    #             print(f"Placed a SHORT order at ${mark_price}, SL = {take_profit} TP = {stop_loss}")
    #         except Exception as err:
    #             print(err)

    #symbol to check what precisions we will need
    #balance to check how much of a position we can have
    #mysize to see what size of position (%) we will allocate to each trade
    def calculate_position_size(self, symbol,mysize):
        """
        Calculate the position size to trade based on account balance
        """
        # Calculate position size based on balance and price
        price_precision, qty_precision, max_qty = self.get_precisions(symbol)
        total_bal = self.get_account_balance('USDT')
        balance = total_bal[0]

        mark_price = float(self.session.get_tickers(
            category='linear',
            symbol=symbol
        )['result']['list'][0]['markPrice'])
        qty_before_lev = (balance*mysize)/float(mark_price)
        qty_final = min(round(qty_before_lev*self.leverage,qty_precision), float(max_qty))

        return qty_final, mark_price

    
    
    def place_order_trailstop(self, symbol, side, mysize,trailing_stop_distance):
        """
        Place a market order and set a trailing stop-loss order based on ATR
        """
        price_precision, qty_precision, max_qty = self.get_precisions(symbol)
        total_bal = self.get_account_balance('USDT')
        balance = total_bal[0]


        trailing_stop_distance_final = round(trailing_stop_distance,price_precision)
        qty_final, mark_price = self.calculate_position_size(symbol, mysize)
        try:
                self.session.place_order(
                    category = self.category,
                    symbol = symbol,
                    side = 'Buy' if side == 1 else 'Sell',
                    orderType = "Market",
                    qty = str(qty_final),
                    #price=str(price),

                    positionIdx=1 if side == 1 else 2,
                    tpslMode = 'Full'

                )
                print(f"Placed a {'LONG' if side == 1 else 'SHORT'} order at ${mark_price}")


                res = self.session.set_trading_stop(
                    category=self.category,
                    symbol=symbol,
                    trailingStop=str(trailing_stop_distance_final),
                    tpslMode="Full",
                    positionIdx=1 if side == 1 else 2
                )
                print(f"Trailing stop set for {symbol} at distance {trailing_stop_distance_final}. Response: {res}")
        except Exception as err:
                print(f"Failed to place order: {err}")
    def setup_trade(self, symbol):
        """
        helper method to setup the modes before placing trade
        """
        self.set_position_mode(symbol, self.category, 3)
        self.set_mode(symbol, self.category, self.leverage)


    def attempt_order(self, symbol,signal, mysize, trailing_stop_distance):
        """
        Attempt to place an order based on the given signal
        """
        order_type = "LONG" if signal == 1 else "SHORT"
        print(f"Attempting to place {order_type} order for {symbol}. Signal: {signal}")
        try:
            self.setup_trade(symbol)
            sleep(2)

            # Place the order
            self.place_order_trailstop(symbol, signal, mysize, trailing_stop_distance)
        except Exception as e:
            print(f"Failed to place {order_type} order for {symbol}. Error: {e}")

    def run(self):


        n_atr = 1.7
    
        print("Starting the program...")
        while True:
            sleep(2)
            balance, avail_balance = self.get_account_balance()
            print('\n')
            timestamp = pd.to_datetime(self.get_time(), unit='s')
            melbourne_tz = pytz.timezone('Australia/Melbourne')
            melbourne_time = timestamp.tz_localize('UTC').tz_convert(melbourne_tz)
            melbourne_time_final = melbourne_time.tz_localize(None)
            print(f'Current time: {melbourne_time_final}')
            print(f'Margin balance: {balance}')
            print(f'Available balance: {avail_balance}')
            positions = self.get_positions()

            #for every element in our allowed position list
            for symbol in self.allowed_positions:
                df = self.get_klines(symbol)

                if df is None or df.empty:
                    print(f"Failed to fetch data for {symbol}. Skipping...")
                    continue
                last_row = df.iloc[-1]

                signal = self.strategy.generate_signal(df, len(df) - 1)
                print( f"{symbol} {signal} || Date: {df.index[-1]} Open: {last_row['Open']} High: {last_row['High']}  Low: {last_row['Low']} Close: {last_row['Close']} ")


                if symbol in positions:
                    current_position = positions[symbol]
                    if (signal == 1 and current_position == 'Buy') or (signal == -1 and current_position == 'Sell'):
                        print(f"Skipping {symbol} - a position in the same direction already exists !")
                        continue  # Skip to the next symbol

                trailing_stop_distance = n_atr* df['ATR'].iloc[-1]# Trailing stop in absolute terms
                if signal != 0:
                    self.attempt_order(symbol, signal, self.mysize, trailing_stop_distance)

                
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

if __name__ == "__main__":
    allowed_positions = ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', '1000PEPEUSDT', 'XRPUSDT', 'ENAUSDT','DOGEUSDT','LTCUSDT', 'LINKUSDT', 'HIVEUSDT', 'SHIB1000USDT', 'RUNEUSDT', 'AVAXUSDT', 'POPCATUSDT', 'ONDOUSDT', 'PNUTUSDT', 'MEUSDT', 'SWARMSUSDT']
    custom_indicators = [
    {'type': 'ema', 'params': {'length': 7, 'col_name': 'Fast_EMA'}},
    {'type': 'ema', 'params': {'length': 15, 'col_name': 'Slow_EMA'}},
    {'type': 'rsi', 'params': {'length': 14}},
    {'type': 'atr', 'params': {'length': 7}},
    {'type': 'bbands', 'params': {'length': 20, 'std': 2.5}}
]
    
    
    
    bot1 = TradingBot(
        api_key=os.getenv('API_DEMO_KEY'),
        api_secret=os.getenv('API_DEMO_SECRET'),
        strategy=BollingerEMAStrategy(),
        allowed_positions=allowed_positions,
        leverage=20,
        interval = '5',
        category = 'linear',
        mysize = 0.05,
        indicators=custom_indicators
    )
  

    bot1.run()