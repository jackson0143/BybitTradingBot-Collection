
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from backtesting.lib import crossover, TrailingStrategy 


#This is a combination of indicators such as the RSI (oversold and overbought lines), MACD crossing signal lines, and price is above or below Bollinger bands (possible reversal)


class MACD_RSI_BB(Strategy):
    # Parameters
    rsi_period = 14
    macd_fast = 14
    macd_slow = 29
    macd_signal = 9

    ema_len = 200


    bb_period = 20
    bb_std = 2
    mysize = 0.95
 
    def init(self):
       
        # MACD
        macd = self.I(ta.macd, pd.Series(self.data.Close), fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        self.macd_line = macd[0]
        self.macd_signal = macd[2]

        # RSI
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_period)

        # Bollinger Bands
        bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_period, self.bb_std )
        self.bb_lower = bbands[0]  
        self.bb_upper = bbands[2]  

        self.ema = self.I(ta.ema, pd.Series(self.data.Close), self.ema_len)
#self.I(ta.ema, pd.Series(self.data.Close), self.slow_ema_len)
    def next(self):
        # Buy Signal
        if (crossover(self.macd_line, self.macd_signal) and  # MACD Line crosses above Signal Line
            self.rsi[-1] < 30 and  # RSI is oversold
            self.data.Close[-1] < self.bb_lower[-1]):  # Price is below lower Bollinger Band
            self.buy(size = self.mysize)

        # Sell Signal
        elif (crossover(self.macd_signal, self.macd_line) and  # MACD Line crosses below Signal Line
              self.rsi[-1] > 70 and  # RSI is overbought
              self.data.Close[-1] > self.bb_upper[-1]):  # Price is above upper Bollinger Band
            self.sell(size = self.mysize)   

class MACD_RSI_BB_Trailing(TrailingStrategy):
    # Parameters
    rsi_period = 14
    macd_fast = 14
    macd_slow = 27
    macd_signal = 9
    ema_len = 200

    bb_period = 20
    bb_std = 2
    mysize = 0.05
    stop_range =2.7

    def init(self):
        super().init()
        super().set_trailing_sl(self.stop_range)    
        # MACD
        macd = self.I(ta.macd, pd.Series(self.data.Close), fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        self.macd_line = macd[0]
        self.macd_signal = macd[2]

        # RSI
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_period)

        # Bollinger Bands
        bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_period, self.bb_std )
        self.bb_lower = bbands[0]  
        self.bb_upper = bbands[2]  
        
        #ema
        self.ema = self.I(ta.ema, pd.Series(self.data.Close), self.ema_len)
    def next(self):
        super().next()
        # Buy Signal
        #if macd cross upwards, BELOW 0 line, and above the 200-EMA
        #if (crossover(self.macd_line, self.macd_signal) and self.macd_line[-1]<0 and self.data.Close[-1]>self.ema[-1] ):
        if (crossover(self.macd_line, self.macd_signal) and self.macd_line[-1]<0 and self.rsi[-1]<30 ):
            
            self.buy(size=self.mysize)
        elif (crossover(self.macd_signal, self.macd_line)and self.macd_line[-1]>0 and self.rsi[-1]>70):
            
            self.sell(size=self.mysize)

    
#df = GOOG
#macd = ta.macd(df['Close'], 12, 26, 9)
#print(macd[0:])
# and  # RSI is oversold
#             self.data.Close[-1] < self.bb_lower[-1]