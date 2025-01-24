
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy
import seaborn as sns
import matplotlib.pyplot as plt

import numpy as np

def ema_signal(fast_ema, slow_ema,  backcandles=6 ):
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
        

        if (ema_sig == 1 and close[current_candle] <= bbl[current_candle]):
           
            return 1
    
    
        elif (ema_sig == -1 and close[current_candle] >= bbu[current_candle]):
            return -1 #SELL
        else:
            return 0
    return [compute_signal(i) if i >= backcandles-1 else 0 for i in range(len(close))]


class Bollinger_EMA(Strategy):
    #ADJUST THESE PARAMS FOR TPSL
    mysize = 0.95
    slcoef = 2.0
    TPSLRatio = 1.7

    sl_ratio = 0.1
    tp_ratio = 0.1
    #These are indicator params dont change
    fast_ema_len=9
    slow_ema_len=21
    atr_val = 7
    bb_len = 20
    std = 2
    backcandles = 7




    def init(self):
 
        self.slow_ema = self.I(ta.ema, pd.Series(self.data.Close), self.slow_ema_len)
        self.fast_ema = self.I(ta.ema, pd.Series(self.data.Close), self.fast_ema_len)
 
        self.atr = self.I(ta.atr,pd.Series(self.data.High), pd.Series(self.data.Low), pd.Series(self.data.Close), self.atr_val )
        bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_len, self.std )
        self.bbl = bbands[0]  
        self.bbu = bbands[2]  
        self.signal1 = self.I(total_signal,self.fast_ema, self.slow_ema, self.data.Close,  self.bbl, self.bbu,self.backcandles )

      


    def next(self):
        slatr = self.slcoef * self.atr[-1]
        TPSLRatio = self.TPSLRatio
        sl_val = self.sl_ratio 
        tp_val = self.tp_ratio 
        price = self.data.Close[-1]

        if self.signal1[-1]==1 and len(self.trades)==0 :
 
           #long position
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl = sl1, tp =tp1, size = self.mysize)

            #self.buy(sl = price*(1-sl_val), tp =price*(1+tp_val), size = self.mysize)

            
        elif self.signal1[-1]==-1 and len(self.trades)==0:       
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl = sl1, tp =tp1, size = self.mysize)

            #self.sell(sl =price*(1+sl_val), tp =price*(1-tp_val), size = self.mysize)


def optimize_plot_BolEMA(bt, showhm = False):
    stats, heatmap= bt.optimize(
        slcoef = [i/10 for i in range(10,21)],
        TPSLRatio = [i/10 for i in range(10,21)],
        #fast_ema_len=range(1,35,1),
        #slow_ema_len=range(15,60,1),
        #mysize = [i/100 for i in range(5,100,5)] ,
        # sl_ratio = [i/10 for i in range(1,11)],
        # tp_ratio = [i/10 for i in range(1,11)],
        maximize = 'Return [%]',
        return_heatmap=True
    )
    print(stats['_strategy'])
    print(stats)
    #bt.plot()
    if showhm:
        heatmap_df = heatmap.unstack()
        plt.figure(figsize = (10,8))
        sns.heatmap(heatmap_df, annot = True, cmap = 'viridis', fmt='.0f')
        plt.show()
    

# stats = bt.run()
# print(stats)
# bt.plot()


