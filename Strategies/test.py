from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from backtesting.lib import crossover, TrailingStrategy 

import numpy as np

#class TestStrategy(Strategy):
class TestStrategy(TrailingStrategy):
    rsi_period = 14
    ema_period = 200


    bb_length = 83
    bb_std = 5
    size = 0.1
    stop_range = 2.0
    def init(self):
        super().init()
        super().set_trailing_sl(self.stop_range)
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), self.rsi_period)
        self.ema = self.I(ta.ema, pd.Series(self.data.Close), self.ema_period)
        
        bbands = self.I(ta.bbands, pd.Series(self.data.Close),self.bb_length, self.bb_std )
        self.bbl = bbands[0]  
        self.bbu = bbands[2]  


        
    def next(self):
        super().next()
        price = self.data.Close[-1]
        bb_width = self.bbu[-1] - self.bbl[-1]

        # Skip trades if Bollinger Band width is too narrow
        if bb_width < 0.01 * price:
            return

        # Long Entry
        if self.data.Close[-2] > self.bbl[-2] and self.data.Close[-1] < self.bbl[-1]:
            if not self.position:
                self.buy(size=self.size)
            if self.position.is_short:
                self.position.close()
                self.buy(size=self.size)

        # Short Entry
        if self.data.Close[-2] < self.bbu[-2] and self.data.Close[-1] > self.bbu[-1]:
            if not self.position:
                self.sell(size=self.size)
            if self.position.is_long:
                self.position.close()
                self.sell(size=self.size)
