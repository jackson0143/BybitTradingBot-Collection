
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from backtesting.lib import crossover, TrailingStrategy 

#buy when candles below vwap, but vwap sloping upwards.
#sell when candles above vwap, but sloping downwardws
def total_signal(close, high, low, bbl, bbh, rsi, bb_width, rsi_oversold, rsi_overbought, bb_width_threshold = 0.0015 ):
    total_signal = []
    
    for i in range(1, len(close)):
        prev_candle_closes_below_bb = close[i-1] < bbl[i-1]
        prev_rsi_below_thr = rsi[i-1] < rsi_oversold
        # Current candle conditions
        closes_above_prev_high = close[i] > high[i-1]
        bb_width_greater_threshold = bb_width[i] > bb_width_threshold

    #prev candle 


        if (prev_candle_closes_below_bb and
            prev_rsi_below_thr and
            closes_above_prev_high and
            bb_width_greater_threshold):
            total_signal.append(1)  # Set the buy signal for the current candle
            continue
    

        prev_candle_closes_above_bb = close[i-1] > bbh[i-1]
        prev_rsi_above_thr = rsi[i-1] > rsi_overbought
        # Current candle conditions
        closes_below_prev_low = close[i] < low[i-1]
        bb_width_greater_threshold = bb_width[i] > bb_width_threshold

            # Combine conditions
        if (prev_candle_closes_above_bb and
            prev_rsi_above_thr and
            closes_below_prev_low and
            bb_width_greater_threshold):
            total_signal.append(-1)  # Set the sell signal for the current candle
            continue

        total_signal.append(0)
    total_signal = [0] + total_signal
    return pd.Series(total_signal)

class Bollinger_RSIonly(Strategy):
    # Parameters
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    bb_width_threshold = 0.001 

    atr_len = 14
    bb_period = 30
    bb_std = 2



    mysize = 0.1
    slcoef = 2.7
    TPcoef = 2.0
    
    def init(self):
        super().init()

        self.atr = self.I(ta.atr,pd.Series(self.data.High), pd.Series(self.data.Low), pd.Series(self.data.Close), self.atr_len)
 
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_period)

  
        bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_period, self.bb_std )
        self.bb_lower = bbands[0]  
        self.bb_upper = bbands[2]  

        self.bb_width = (bbands[2]-bbands[0])/bbands[1]
        self.total_signal = self.I(total_signal, pd.Series(self.data.Close), pd.Series(self.data.High), pd.Series(self.data.Low), self.bb_lower, self.bb_upper, self.rsi, self.bb_width, self.rsi_oversold, self.rsi_overbought, self.bb_width_threshold )


    def next(self):
        super().next()
        slatr = self.slcoef*self.atr[-1]
        tpatr = self.TPcoef*self.atr[-1]
    
        if self.total_signal[-1]==1 and len(self.trades)==0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + tpatr
            self.buy(sl=sl1, tp=tp1, size=self.mysize)

        if self.total_signal[-1]==-1 and len(self.trades)==0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - tpatr
            self.sell(sl=sl1, tp=tp1, size=self.mysize)

