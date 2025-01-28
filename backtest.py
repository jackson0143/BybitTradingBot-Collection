from backtesting.test import GOOG
from backtesting import Backtest, Strategy
import pandas as pd
import pandas_ta as ta
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import pytz
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from time import sleep
import matplotlib.pyplot as plt
import seaborn as sns

from binance.client import Client
load_dotenv()


from Strategies.Bollinger_EMA import Bollinger_EMA
from Strategies.Bollinger_EMA_2 import Bollinger_EMA2
from Strategies.rsi_crossover import RSI_crossover
from Strategies.test import TestStrategy
from Strategies.MACD_RSI_BOL import MACD_RSI_BB_Trailing

session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)




def plot_graph(df_main):
    df = df_main.copy()
    df['pointpos'] = [
    float(row['Low']) - (float(row['High']) - float(row['Low'])) * 0.5 if row['TOTAL_SIGNAL'] == 1 else  # LONG
    float(row['High']) + (float(row['High']) - float(row['Low'])) * 0.5 if row['TOTAL_SIGNAL'] == -1 else  # SHORT
    None
    for _, row in df.iterrows()
    ]
    fig = go.Figure(data = go.Candlestick(x=df.index,
                                      open = df['Open'],
                                      high = df['High'],
                                      low = df['Low'],
                                      close = df['Close']))
    #fig.update_layout(xaxis_rangeslider_visible=False)
    fig.add_trace(go.Scatter(x=df.index, y=df['Fast_EMA'], line=dict(color='blue'), name='Fast EMA '))
    fig.add_trace(go.Scatter(x=df.index, y=df['Slow_EMA'], line=dict(color='red'), name='Slow EMA '))

    fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.5'], line=dict(color='green', width = 1), name='Upper Band'))
    fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.5'], line=dict(color='orange', width = 1), name='Lower Band'))
    fig.add_scatter(
        x=df.index, 
        y=df['pointpos'], 
        mode='markers', 
        marker=dict(size=10, color="MediumPurple", symbol="circle"),  # Increased size and visibility
        name="Entry"
    )

    fig.update_layout(
        title="Candlestick Chart with Indicators",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=True,
        yaxis=dict(
            autorange=True,  # Allow y-axis to rescale automatically
            fixedrange=False  # Allow manual zooming on the y-axis
        )
    )
    fig.show()

    return fig

def print_stats(results):
    print( "-" * 40 + "\n")
    print(f"Backtest Results for {results['_strategy']} ")
    print('\n')
    print(f"Start: {results['Start']}")
    print(f"End: {results['End']}")
    print(f"Duration: {results['Duration']}")
    print(f"Equity Final: {results['Equity Final [$]']:.2f}")
    print(f"Return %: {results['Return [%]']:.2f}")

    print(f"Buy & Hold Return %: {results['Buy & Hold Return [%]']:.2f}")
    print(f"Max Drawdown %: {results['Max. Drawdown [%]']:.2f}")
    print(f"Avg Drawdown %: {results['Avg. Drawdown [%]']:.2f}")
    print(f"Trades: {results['# Trades']}")
    print(f"Winrate %: {results['Win Rate [%]']:.2f}")
    
def fetch_market_data_binance(symbol, interval,starting_date):
    info=Client().get_historical_klines(symbol=symbol, interval=interval, start_str = starting_date)
    df = pd.DataFrame(info)
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset vol', 'Num trades', 'Taker buy base', 'Taker buy quote', 'Ignore']
    df = df.astype(float)
    
    df['Date'] = pd.to_datetime(pd.to_numeric(df['Date']), unit='ms')
    df.set_index('Date', inplace=True)
    
    melbourne_tz = pytz.timezone('Australia/Melbourne')
    df.index = df.index.tz_localize('UTC').tz_convert(melbourne_tz)
    df.index = df.index.tz_localize(None)
    return df

def mass_run_symbols(symbols, interval, category, starting_date,  strategy_call):
    results = []
    print( "-" * 40 + "\n")
    print(f"Running backtest for Strategy:")
    for symbol in symbols:
        print(f"Running backtest for {symbol}")
        try:
            df = fetch_market_data_binance(symbol, interval, starting_date)
            
            # Call the backtest function for the current symbol
            bt = strategy_call(symbol, interval, category, df)
        
            stats = bt.run()
            # Extract the necessary metrics (e.g., return, Sharpe ratio, etc.)
            final_return = stats['Equity Final [$]']
            total_return = stats['Return [%]']
            max_draw = stats['Max. Drawdown [%]']

            # Append to the results
            results.append({
                'Symbol': symbol,
                'Final Equity ($)': final_return,
                'Total Return (%)': total_return,
                'Max drawdown': max_draw
            })
        except Exception as e:
            print(f"Error running backtest for {symbol}: {e}")
            results.append({
                'Symbol': symbol,
                'Final Equity ($)': None,
                'Total Return (%)': None,
                'Sharpe Ratio': None,
                'Error': str(e)
            })
        
        sleep(1)  # Optional: To avoid hitting rate limits

    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

    # Print the final results DataFrame
    print(results_df)
    total_return_sum = results_df['Total Return (%)'].sum()
    print(f"\nSum of Total Return (%): {total_return_sum}")
    return results_df


#######################

def run_bt_bolEMA(symbol, interval, category, df):
    symbol = symbol
    interval = interval
    category = category

    bt = Backtest(df, Bollinger_EMA, cash=100000, commission=0.0006, margin = 1/20, hedging=True)
    
    return bt

def run_bt_bolEMA2(symbol, interval, category, df_old):
    df=df_old.copy()
    symbol = symbol
    interval = interval
    category = category

    bt = Backtest(df, Bollinger_EMA2, cash=100000, commission=0.0006, margin = 1/20, hedging=True)
    '''
   
    print(stats)    

    print(df[df['TOTAL_SIGNAL']!= 0].head(20))
    print(stats['_trades'])

    plot_graph(df)
    sleep(5)

    bt.plot()
    '''
    '''
    '''


    # Print rows where TOTAL_SIGNAL != 0
    #print(updated_df[updated_df['TOTAL_SIGNAL'] != 0].head(20))

    return bt

def run_bt_rsi_crossover(symbol, interval, category, df):

    symbol = symbol
    interval = interval
    category = category
    
    bt = Backtest(df, RSI_crossover, cash=100000, commission=0.0006, margin = 1/20, hedging=True)
    return bt

def run_test_strategy(symbol, interval, category, df):
    symbol = symbol
    interval = interval
    category = category
    bt = Backtest(df, TestStrategy, cash=100000, commission=0.0006, margin = 1/20)

  

    return bt

def run_bt_MACDRSIBOL(symbol, interval, category, df):
    symbol = symbol
    interval = interval
    category = category
    bt = Backtest(df, MACD_RSI_BB_Trailing, cash=1000000, commission=0.0006, margin = 1/5, hedging = True)

    return bt
def optimize_strategy(backtest, params, maximize, show_heatmap=False):
    
    if show_heatmap:
        stats, heatmap = backtest.optimize(
            **params,
            maximize=maximize,
            return_heatmap=True
        )

        # Create heatmap
        heatmap_df = heatmap.unstack()
        plt.figure(figsize=(10, 8))
        sns.heatmap(heatmap_df, annot=True, cmap='viridis', fmt='.2f')
        plt.title(f"Optimization Heatmap for {maximize}")
        #plt.xlabel("Parameter 1")
        #plt.ylabel("Parameter 2")
        plt.show()
        print(f"Backtest Results for {stats['_strategy']} ")
        return stats
    else:
        # Optimize without heatmap
        stats = backtest.optimize(
            **params,
            maximize=maximize,
            return_heatmap=False
        )
        print(f"Backtest Results for {stats['_strategy']} ")
        return stats
    
if __name__ == "__main__":


    symbol='SOLUSDT'
    interval = Client.KLINE_INTERVAL_5MINUTE
    category = 'linear'
    start_date = '1 january 2025'
    df = fetch_market_data_binance(symbol,interval, start_date)
   
    symbols =  ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', 'XRPUSDT', 'ENAUSDT','DOGEUSDT','LTCUSDT', 'LINKUSDT', 'HIVEUSDT',  'RUNEUSDT', 'AVAXUSDT', 'POPCATUSDT', 'ONDOUSDT', 'PNUTUSDT', 'MEUSDT', 'SWARMSUSDT']

    bt = run_bt_bolEMA(symbol, interval, category, df)
   
    params = {
        #'rsi_period': range(7, 25, 2),
        #'macd_fast': range(5, 15, 1),
        #'macd_slow': range(15, 30, 2),
        'fast_ema_len': range(1,10,1),
        'slow_ema_len':range(10,20,1),
        #'macd_signal':  range(5, 10, 1),
        #'mysize': [i / 100 for i in range(5, 100,5)],
        #'stop_range':[i / 10 for i in range(11, 51,2)]
        #'bb_period': range(10, 30, 5),
        #'bb_std': [i / 10 for i in range(15, 31)],
    }
    maximize = 'Return [%]'
    stats = optimize_strategy(bt, params, maximize, True )
    #stats = bt.run()
    bt.plot()
    print(stats)


    #results_df = mass_run_symbols(symbols, interval, category, start_date,run_bt_MACDRSIBOL)

    #run_test_strategy(symbol, interval, category, df)
    # symbols =  ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', 'XRPUSDT', 'HIVEUSDT']
    # for symbol in symbols:
    #     print( "-" * 40 + "\n")
    #     print(f"Running strategy for {symbol}...")
        
    #     # Fetch the market data for the symbol
    #     df = fetch_market_data_binance(symbol, interval, start_date)
        
    #     # Run the test strategy for the symbol
    #     run_bt_bolEMA2(symbol, interval, category, df)
        
