
from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy



def ema_signal(df, current_candle, backcandles=6 ):
    df_copy = df.copy()
    start = max(0, current_candle - backcandles) #starts at 0, or whatever candle we can reach . ADD 1 if we want to include current candle right?
    end = current_candle     #add 1 here too
    df_new = df_copy.iloc[start:end]

    if all(df_new['Fast_EMA'] > df_new['Slow_EMA']):
        return 1  # Uptrend
    elif all(df_new['Fast_EMA'] < df_new['Slow_EMA']):
        return -1  # Downtrend
    else:
        return 0  
    

def total_signal(df, current_candle, backcandles = 6):

    #if EMA signal is uptrend and we close under bollinger band lower, we return a BUY signal
    if (ema_signal(df, current_candle, backcandles)==1 and df['Close'].astype(float).iloc[current_candle]<=df['BBL_20_2.0'].iloc[current_candle]
    ):
        return 1
    
    
    if (ema_signal(df, current_candle, backcandles)==-1 and df['Close'].astype(float).iloc[current_candle]>=df['BBU_20_2.0'].iloc[current_candle]
    ):
        return -1
    return 0

def SIGNAL():
    return df['TOTAL_SIGNAL']

class Bollinger_EMA(Strategy):
    mysize = 0.95
    slcoef = 1.1 # Reduce stop-loss coefficient
    TPSLRatio = 1.5 # Reduce take-profit ratio
    rsi_length = 16
    
 

    def init(self):
        super().init()
    
        self.signal1 = self.I(SIGNAL)
        #df['RSI']=ta.rsi(df.Close, length=self.rsi_length)

    def next(self):
        super().next()
        
        slatr = self.slcoef * self.data.ATR[-1]
        
        TPSLRatio = self.TPSLRatio
  
        if self.signal1[-1]==1 and len(self.trades)==0 :
 
           #long position
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            #print(f"Long SL={sl1}, TP={tp1}, Entry={self.data.Close[-1]} at {self.data.index[-1]}")
            self.buy(sl=sl1, tp=tp1, size = self.mysize )

            
        elif self.signal1[-1]==-1 and len(self.trades)==0:       
            #Short position
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            #print(f"Short SL={sl1}, TP={tp1}, Entry={self.data.Close[-1]}")
            self.sell(sl=sl1, tp=tp1, size = self.mysize)



df = GOOG
backcandles= 6
df['Fast_EMA'] = ta.ema(df['Close'].astype(float), length=30)
df['Slow_EMA'] = ta.ema(df['Close'].astype(float), length=50)
df['ATR'] = ta.atr(df['High'].astype(float), df['Low'].astype(float),df['Close'].astype(float), length=7)
bbands = ta.bbands(df['Close'].astype(float), length = 20, std = 2)
df = df.join(bbands)
df['EMA_SIGNAL'] = [ema_signal(df, i,backcandles) if i >= backcandles - 1 else 0 for i in range(len(df))]
df['TOTAL_SIGNAL'] = [total_signal(df, i,backcandles) if i >= backcandles-1 else 0 for i in range(len(df))]

bt = Backtest(df, Bollinger_EMA,  cash=1000)

stats = bt.run()
print(stats)