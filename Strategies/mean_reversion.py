from backtesting.test import GOOG
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy

from backtesting.lib import crossover, TrailingStrategy 

from backtesting.lib import crossover, TrailingStrategy 

import numpy as np

df = GOOG
macd = ta.macd(df['Close'],12, 26,9  )
print(macd)