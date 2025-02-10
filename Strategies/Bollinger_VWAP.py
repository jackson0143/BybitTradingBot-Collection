
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from backtesting.lib import crossover, TrailingStrategy 

#buy when candles below vwap, but vwap sloping upwards.
#sell when candles above vwap, but sloping downwardws
class Bollinger_VWAP(Strategy):
    # Parameters
    rsi_period = 14
    macd_fast = 14
    macd_slow = 29
    macd_signal = 9



    bb_period = 20
    bb_std = 2
    mysize = 0.05
 
    def init(self):
        


        # VWAP
        self.vwap = self.I(ta.vwap, pd.Series(self.data.High),pd.Series(self.data.Low), pd.Series(self.data.Close), pd.Series(self.data.Volume) )
        # RSI
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_period)
        # Bollinger Bands
        bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_period, self.bb_std )
        self.bb_lower = bbands[0]  
        self.bb_upper = bbands[2]  

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
