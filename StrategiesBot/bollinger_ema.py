import pandas as pd
from .base_strategy import Strategy

class BollingerEMAStrategy(Strategy):
    def generate_signal(self, df, current_candle, backcandles=6):
        ema_sig = self.ema_signal(df, current_candle, backcandles)
        if ema_sig == 1 and df['Close'].iloc[current_candle] <= df['BB_Lower'].iloc[current_candle]:
            return 1  # Buy signal
        elif ema_sig == -1 and df['Close'].iloc[current_candle] >= df['BB_Upper'].iloc[current_candle]:
            return -1  # Sell signal
        return 0
    

    def ema_signal(self, df, current_candle, backcandles=6):
        start = max(0, current_candle - backcandles)
        subset = df.iloc[start:current_candle]
        if all(subset['Fast_EMA'] > subset['Slow_EMA']):
            return 1  # Uptrend
        elif all(subset['Fast_EMA'] < subset['Slow_EMA']):
            return -1  # Downtrend
        return 0
    
