from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from backtesting.lib import crossover, TrailingStrategy 


import numpy as np


class Mean_Reversion(Strategy):


    def init(self):
        super().init()
        self.moving_avg = self.I(ta.ema,pd.Series(self.data.Close),7)


    def next(self):
        super().next()

    

          

