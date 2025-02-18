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

from Strategies.Bollinger_EMA import total_signal

from binance.client import Client
load_dotenv()


from Strategies.Bollinger_EMA import Bollinger_EMA

from Strategies.rsi_crossover import RSI_crossover
from Strategies.test import TestStrategy
from Strategies.MACD_RSI_BOL import MACD_RSI_BB_Trailing
from Strategies.Bollinger_RSIonly import Bollinger_RSIonly
from Strategies.Bollinger_VWAP import Bollinger_VWAP
session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)


def apply_indicator( df, indicator):
        """
        Apply a technical indicator to the DataFrame based on its type and parameters.
        """
        indicator_type = indicator['type']
        params = indicator['params']

        # apply the indicator based on its type dynamically
        if indicator_type == 'ema':
            col_name = params.get('col_name', f"EMA_{params['length']}")
            df[col_name] = ta.ema(df['Close'], length=params['length'])
        
        elif indicator_type == 'sma':
            col_name = params.get('col_name', f"SMA_{params['length']}")
            df[col_name] = ta.sma(df['Close'], length=params['length'])
        
        elif indicator_type == 'atr':
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=params['length'])
        
        elif indicator_type == 'bbands':
            bbands = ta.bbands(df['Close'], length=params['length'], std=params['std'])
            bbands.columns = ['BB_Lower', 'BB_Middle', 'BB_Upper', 'BB_BandWidth', 'BB_Percent']
            for col in bbands.columns:
                df[col] = bbands[col]

        elif indicator_type == 'rsi':
            df['RSI'] = ta.rsi(df['Close'], length=params['length'])


        elif indicator_type == 'total_signal':
            # Apply the total_signal function and store the result in the specified column
            df[params.get('col_name', 'TOTAL_SIGNAL')] = total_signal(
                fast_ema=df[params['fast_ema']].values,
                slow_ema=df[params['slow_ema']].values,
                close=df['Close'].values,
                bbl=df['BB_Lower'].values,
                bbu=df['BB_Upper'].values,
                backcandles=params['backcandles']
            )
        else:
            print(f"Unknown indicator type: {indicator_type}")

def apply_all_indicators(df, indicators):
    for indicator in indicators:
        apply_indicator(df, indicator)  # Apply each indicator
    return df 
def plot_graph(df_main, indicators):
    df = df_main.copy()

    # Determine entry/exit points based on signals
    df['pointpos'] = [
        float(row['Low']) - (float(row['High']) - float(row['Low'])) * 0.5 if 'TOTAL_SIGNAL' in row and row['TOTAL_SIGNAL'] == 1 else  # LONG
        float(row['High']) + (float(row['High']) - float(row['Low'])) * 0.5 if 'TOTAL_SIGNAL' in row and row['TOTAL_SIGNAL'] == -1 else  # SHORT
        None
        for _, row in df.iterrows()
    ]


    # Initialize candlestick chart
    fig = go.Figure(data=go.Candlestick(x=df.index,
                                        open=df['Open'],
                                        high=df['High'],
                                        low=df['Low'],
                                        close=df['Close']))

    # Add traces for custom indicators
    for indicator in indicators:
        indicator_type = indicator['type']
        params = indicator['params']
        if 'length' in params:
            col_name = params.get('col_name', f"{indicator_type.upper()}_{params['length']}")

        if col_name == 'Fast_EMA':
            color = 'blue'
        elif col_name == 'Slow_EMA':
            color = 'red'

        # Special handling for Bollinger Bands
        if indicator_type == 'bbands':
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='orange', width=1), name='BB Lower'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='green', width=1), name='BB Upper'))


        if col_name == 'TOTAL_SIGNAL':
            continue
        else:
            if col_name in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[col_name], line=dict(width=1.5, color=color), name=col_name))

    # Add signal markers
    fig.add_scatter(
        x=df.index,
        y=df['pointpos'],
        mode='markers',
        marker=dict(size=10, color="MediumPurple", symbol="circle"),
        name=(f"Entry")
    )

    # Final layout configuration
    fig.update_layout(
        title="Candlestick Chart with Custom Indicators",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=True,
        yaxis=dict(
            autorange=True,
            fixedrange=False  
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

def mass_run_symbols(symbols, interval, start_date, strategy_name,cash=100000, commission=0.0006, margin=1/20, hedging=True):

    print( "-" * 40 + "\n")
    print(f"Running backtest for Strategy:")


    results = []
    for symbol in symbols:
        print(f"Running backtest for {symbol}")
        try:
            df = fetch_market_data_binance(symbol, interval, start_date)
            bt, stats = run_single_strategy(df, strategy_name, cash, commission, margin, hedging)

            # Append to the results
            results.append({
                'Symbol': symbol,
                'Final Equity ($)': stats['Equity Final [$]'],
                'Total Return (%)': stats['Return [%]'],
                'Max drawdown': stats['Max. Drawdown [%]']
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
        


    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

    # Print the final results DataFrame
    print(results_df)
    total_return_sum = results_df['Total Return (%)'].sum()
    print(f"\nSum of Total Return (%): {total_return_sum}")
    return results_df
'''
def mass_optimize_symbols(symbols, interval, category, starting_date, strategy_call, param, optimization_rounds=50):
    best_params = None
    best_avg_sharpe = -float('inf')  # Track the best average Sharpe ratio
    all_results = []

    print("-" * 40 + "\nRunning optimization for Strategy across symbols:\n")

    # Loop through symbols and run optimization using Backtest.optimize()
    for symbol in symbols:
        print(f"\nOptimizing for {symbol}...\n")
        
        try:
       
            df = fetch_market_data_binance(symbol, interval, starting_date)

       
            bt = strategy_call(symbol, interval, category, df)
            stats = optimize_strategy(bt, params, maximize, show_heatmap=False)

            # Collect the optimized parameter set and its Sharpe ratio
    
            sharpe_ratio = stats['Sharpe Ratio']

            print(f"Optimized Parameters for {symbol}: {optimized_params} with Sharpe Ratio: {sharpe_ratio}")

            all_results.append({
                'Symbol': symbol,
                'Optimized Parameters': optimized_params,
                'Sharpe Ratio': sharpe_ratio
            })

            # Update the best overall params if this Sharpe ratio is better
            if sharpe_ratio > best_avg_sharpe:
                best_avg_sharpe = sharpe_ratio
                best_params = optimized_params

        except Exception as e:
            print(f"Error optimizing for {symbol}: {e}")
            all_results.append({
                'Symbol': symbol,
                'Error': str(e)
            })

        sleep(0.5)  # Optional: To avoid rate limits

    print(f"\nBest Overall Parameters Across Symbols: {best_params} with Average Sharpe Ratio: {best_avg_sharpe:.2f}")
    return best_params, all_results
'''
#######################

 

def run_single_strategy(df, strategy_name, cash=100000, commission = 0.0006, margin = 1/20, hedging =True):
    '''
    Runs a single strategy and Backtests it
    '''
    

    strategy_class = strategies.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Strategy {strategy_name} not found")
    

    bt = Backtest(df, strategy_class, cash = cash, commission=commission, margin = margin, hedging = hedging)
    stats=bt.run()

    #bt.plot()
    return bt, stats

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

    strategies = {
    'Bollinger_EMA': Bollinger_EMA,
    'RSI_Crossover': RSI_crossover,
    'TestStrategy': TestStrategy,
    'MACD_RSI_BB_Trailing': MACD_RSI_BB_Trailing,
    'Bollinger_VWAP':Bollinger_VWAP,#incomplete
    'Bollinger_RSIonly': Bollinger_RSIonly
}
    symbol='ETHUSDT'
    interval = Client.KLINE_INTERVAL_5MINUTE
    #category = 'linear'
    start_date = '1 december 2024'
    df = fetch_market_data_binance(symbol,interval, start_date)

    symbols =  ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', 'XRPUSDT', 'ENAUSDT','DOGEUSDT','LTCUSDT', 'LINKUSDT', 'HIVEUSDT',  'RUNEUSDT', 'AVAXUSDT', 'POPCATUSDT', 'ONDOUSDT', 'PNUTUSDT', 'MEUSDT', 'SWARMSUSDT']
 
    custom_indicators = [
    {'type': 'ema', 'params': {'length': 7, 'col_name': 'Fast_EMA'}},
    {'type': 'ema', 'params': {'length': 15, 'col_name': 'Slow_EMA'}},
    {'type': 'rsi', 'params': {'length': 14}},
    {'type': 'atr', 'params': {'length': 7}},
    {'type': 'bbands', 'params': {'length': 20, 'std': 2.5}},
    {'type': 'total_signal', 'params': {
        'fast_ema': 'Fast_EMA',
        'slow_ema': 'Slow_EMA',
        'backcandles': 6,
        'col_name': 'TOTAL_SIGNAL'
    }},
   # {'type': 'vwap', 'params': {'length': 7}},
]

    params = {
        #'rsi_period': range(7, 25, 2),
        #'macd_fast': range(5, 15, 1),
        #'macd_slow': range(15, 30, 2),
        #'fast_ema_len': range(1,10,1),
        #'slow_ema_len':range(10,20,1),
        #'macd_signal':  range(5, 10, 1),
        #'mysize': [i / 100 for i in range(5, 100,5)],
        #'stop_range':[i / 10 for i in range(11, 51,2)],
        #'bb_len': range(2, 40, 2),
        'tpperc': [i / 100 for i in range(1, 15,1)],
        'slperc': [i / 100 for i in range(1, 15,1)],
        #'bb_std': [i / 10 for i in range(15, 31)],
        #'slcoef':[i/10 for i in range(10, 41)],
        #'TPcoef': [i/10 for i in range(10, 41)]
    }


    df = apply_all_indicators(df, custom_indicators)

    # sleep(2)
    # fig = plot_graph(df, custom_indicators)  
    # sleep(2)
    #bt, stats = run_single_strategy(df, 'Bollinger_EMA', cash = 1000000, commission=0.0006, margin = 1/10, hedging = True)


    #stats = optimize_strategy(backtest=bt, params=params, maximize='Return [%]', show_heatmap=True )
    #print(stats)
    #bt.plot()
    stats = mass_run_symbols(symbols, interval, start_date, 'Bollinger_EMA',cash=1000000, commission=0.0006, margin=1/10, hedging=True)
