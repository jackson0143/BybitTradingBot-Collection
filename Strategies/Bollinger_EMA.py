from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from backtesting.lib import crossover, TrailingStrategy 


import numpy as np

def ema_signal(fast_ema, slow_ema,  backcandles=6):
    def compute_signal(current_candle):

        start = max(0, current_candle - backcandles) #starts at 0, or whatever candle we can reach . ADD 1 if we want to include current candle right?
        end = current_candle     #add 1 ehre too

        if all(fast_ema[start:end] > slow_ema[start:end]):
                return 1  # Uptrend
        elif all(fast_ema[start:end] < slow_ema[start:end]):
                return -1  # Downtrend
        else:
                return 0
    return [compute_signal(i) if i >= backcandles - 1 else 0 for i in range(len(fast_ema))]

def total_signal(fast_ema, slow_ema, close, bbl, bbu, backcandles):
    ema_signals = ema_signal(fast_ema, slow_ema, backcandles)
    
    def compute_signal(current_candle):
        ema_sig = ema_signals[current_candle]
        #current_rsi = rsi[current_candle]
        if (ema_sig == 1 and close[current_candle] <= bbl[current_candle]):
            return 1
    
        elif (ema_sig == -1 and close[current_candle] >= bbu[current_candle]):
            return -1 #SELL
        else:
            return 0
    return [compute_signal(i) if i >= backcandles-1 else 0 for i in range(len(close))]

#class Bollinger_EMA(Strategy):
class Bollinger_EMA(TrailingStrategy):
    mysize = 0.05
    slcoef = 1.9
    TPSLRatio = 1.7





    #These are indicator params dont change
    fast_ema_len=7
    slow_ema_len=15
    atr_val = 7
    bb_len = 20
    bb_std = 2.5


    backcandles = 6

    stop_range =1.7

    def init(self):
        super().init()
        super().set_trailing_sl(self.stop_range)
        self.slow_ema = self.I(ta.ema, pd.Series(self.data.Close), self.slow_ema_len)
        self.fast_ema = self.I(ta.ema, pd.Series(self.data.Close), self.fast_ema_len)
        #self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)
        self.atr = self.I(ta.atr,pd.Series(self.data.High), pd.Series(self.data.Low), pd.Series(self.data.Close), self.atr_val )
        self.bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_len, self.bb_std )
 
        self.bbl = self.bbands[0]  
        self.bbu = self.bbands[2]  
        self.signal1 = self.I(total_signal, self.fast_ema, self.slow_ema, self.data.Close, self.bbl, self.bbu, self.backcandles)

      


    def next(self):
        super().next()
        slatr = self.slcoef * self.atr[-1]
        TPSLRatio = self.TPSLRatio

        price = self.data.Close[-1]

        if self.signal1[-1]==1 :
 
           #long position
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            #self.buy(sl=sl1, tp=tp1, size = self.mysize )
            self.buy( size = self.mysize )
         

            
        elif self.signal1[-1]==-1:       
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            #self.sell(sl=sl1, tp=tp1, size = self.mysize)
            self.sell( size = self.mysize)

          

