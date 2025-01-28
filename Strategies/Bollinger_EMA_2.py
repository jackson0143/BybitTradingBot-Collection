from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

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
    mysize = 0.1
    slcoef = 1.9
    TPSLRatio = 1.7

    #slcoef = 1.9
    #TPSLRatio = 1.7
    #rsi_length = 16
    #backcandles= 6



    mysize = 0.1
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




