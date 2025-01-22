from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
import numpy as np
class RSI_crossover(Strategy):
    overbought = 85  # Overbought 
    oversold = 35    # Oversold 
    rsi_window = 6
    sl_ratio = 15  
    tp_ratio = 65  

    def init(self):
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)
    
    def next(self):
        
        #current price

        sl_val = self.sl_ratio / 100
        tp_val = self.tp_ratio / 100
        price = self.data.Close[-1]


        if self.rsi[-1] < self.oversold:
            self.buy(sl =price*(1-sl_val), tp =price*(1+tp_val))
        elif self.rsi[-1] > self.overbought:
            self.sell(sl =price*(1+sl_val), tp =price*(1-tp_val))

# Backtest with GOOG sample data
bt = Backtest(GOOG, RSI_crossover, cash=10_000)


# stats = bt.optimize(
#     sl_ratio=range(5, 20,5),  
#     tp_ratio=range(5, 70,5),  
#     oversold = range(5,45,5),
#     overbought = range(45,95,5),
 
#     maximize='Return [%]'
# )
# print(stats)


# stats = bt.optimize(

#     rsi_window = range(1,50,1),
#     maximize='Return [%]'
# )
# print(stats)


stats =bt.run()
print(stats)

bt.plot()
