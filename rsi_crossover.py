from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
import seaborn as sns
import matplotlib.pyplot as plt
class RSI_crossover(Strategy):
    overbought = 85  # Overbought 
    oversold = 20   # Oversold 
    rsi_window = 6
    sl_ratio = 0.1
    tp_ratio = 0.1

    def init(self):
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_window)
    
    def next(self):
        
        #current price
        sl_val = self.sl_ratio 
        tp_val = self.tp_ratio 
        price = self.data.Close[-1]


        if self.rsi[-1] < self.oversold:
            self.buy(sl =price*(1-sl_val), tp =price*(1+tp_val))
        elif self.rsi[-1] > self.overbought:
            self.sell(sl =price*(1+sl_val), tp =price*(1-tp_val))



def optimize_plot_rsi_cross(bt,  showhm = False):

    stats, heatmap = bt.optimize(
    sl_ratio=[i/10 for i in range(1,11)],  
    tp_ratio=[i/10 for i in range(1,11)],  
    oversold = range(5,45,5),
    overbought = range(45,95,5),
    #maximize='Return [%]',
    maximize='Return [%]',
    return_heatmap = True
    
)   
    
    print(stats['_strategy'])
    print(stats)
    if showhm:
        heatmap_df = heatmap.unstack()
        plt.figure(figsize = (10,8))
        sns.heatmap(heatmap_df, annot = True, cmap = 'viridis', fmt='.0f')
        plt.show()

if __name__ == "__main__":
    # bt = Backtest(GOOG, RSI_crossover, cash=10_000)
    # optimize_plot(bt)
    pass