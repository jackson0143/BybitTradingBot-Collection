from .base_strategy import Strategy

class SMACrossoverStrategy(Strategy):
    def generate_signal(self, df, current_candle, backcandles):
        if df['Fast_EMA'].iloc[current_candle] > df['Slow_EMA'].iloc[current_candle]:
            return 1  # Buy signal
        elif df['Fast_EMA'].iloc[current_candle] < df['Slow_EMA'].iloc[current_candle]:
            return -1  # Sell signal
        return 0