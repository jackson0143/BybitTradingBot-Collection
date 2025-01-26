
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy
import seaborn as sns
import matplotlib.pyplot as plt
from backtesting.lib import crossover, TrailingStrategy


def ema_signal(df, current_candle, backcandles ):
    start = max(0, current_candle - backcandles)
    df_new = df.iloc[start:current_candle ]

    if all(df_new['Fast_EMA'] > df_new['Slow_EMA']):
        return 1  # Uptrend
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

def SIGNAL(df):
    return df['TOTAL_SIGNAL']
#class Bollinger_EMA2(Strategy):
class Bollinger_EMA2(TrailingStrategy):
    mysize = 0.05
    slcoef = 1.9
    TPSLRatio = 1.7

    #slcoef = 1.9
    #TPSLRatio = 1.7
    #rsi_length = 16
    #backcandles= 6
 
    stop_range =1.7
    def init(self):
        super().init()
        super().set_trailing_sl(self.stop_range)
        self.signal1 = self.I(SIGNAL, self.data.df)


    def next(self):
        super().next()
        slatr = self.slcoef * self.data.ATR[-1]
        
        TPSLRatio = self.TPSLRatio

        if self.signal1[-1]==1 :
       
           #long position
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            #self.buy(sl=sl1, tp=tp1, size = self.mysize )
            self.buy( size = self.mysize )

            
        if self.signal1[-1]==-1 :       
            #Short position
        
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            #self.sell(sl=sl1, tp=tp1, size = self.mysize)
            self.sell( size = self.mysize)

def optimize_plot_BolEMA2(bt, showhm = False):
    
        #overbought = range(50,95,5),
        #oversold = range(5,50,5),
        #rsi_window = range(2,20,2),

        #fast_ema_len=range(1,15,1),
        #slow_ema_len=range(15,35,1),
    stats, heatmap = bt.optimize(
        #slcoef=[i / 10 for i in range(10, 21)],  # Range: 1.0 to 2.0
        #TPSLRatio=[i / 10 for i in range(10, 21)],  # Range: 1.0 to 2.0
        #slcoef=[i / 10 for i in range(15, 31)],  # Range: 1.5 to 3.0
        TPSLRatio=[i / 10 for i in range(15, 31)],  # Range: 1.5 to 3.0
        #fast_ema_len=range(1,15,1),
        #slow_ema_len=range(15,35,1),
        stop_range= [i / 10 for i in range(1, 31)],

        maximize='Return [%]',
        #maximize = 'Max. Drawdown [%]',
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
    return stats
# df = GOOG
# backcandles = 6
# df['Fast_EMA'] = ta.ema(df['Close'], length=30)
# df['Slow_EMA'] = ta.ema(df['Close'], length=50)
# df['ATR'] = ta.atr(df['High'], df['Low'],df['Close'], length=7)
# bbands = ta.bbands(df['Close'], length = 20, std = 2)
# df = df.join(bbands)
# df['EMA_SIGNAL'] = [ema_signal(df, i,backcandles) if i >= backcandles - 1 else 0 for i in range(len(df))]
# df['TOTAL_SIGNAL'] = [total_signal(df, i,backcandles) if i >= backcandles-1 else 0 for i in range(len(df))]


# bt = Backtest(df, Bollinger_EMA2, cash=10000, commission=0.0006, margin = 1/5)
# print(bt.run())
