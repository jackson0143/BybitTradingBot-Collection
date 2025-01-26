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

from binance.client import Client
load_dotenv()


from Strategies.Bollinger_EMA import Bollinger_EMA, optimize_plot_BolEMA
from Strategies.Bollinger_EMA_2 import Bollinger_EMA2, ema_signal, total_signal, optimize_plot_BolEMA2
from Strategies.rsi_crossover import RSI_crossover, optimize_plot_rsi_cross
from Strategies.test import TestStrategy, optimize_plot_test

session = HTTP(
    testnet=False,
    demo=True,
    api_key=os.getenv('API_DEMO_KEY'),
    api_secret=os.getenv('API_DEMO_SECRET'),
)


'''
def fetch_market_data(symbol, interval, category, limit=200, start = None):

    data = session.get_kline(symbol=symbol, interval=interval, category = category, limit=limit, start = start
    )
    df = pd.DataFrame(data['result']['list'])
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']

    df['Date'] = pd.to_datetime(pd.to_numeric(df['Date']), unit='ms')
    df.set_index('Date', inplace=True)
    melbourne_tz = pytz.timezone('Australia/Melbourne')
    df.index = df.index.tz_localize('UTC').tz_convert(melbourne_tz)
    df.index = df.index.tz_localize(None)

    df = df[::-1]

    df = df.astype(float)
    return df
'''


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
            stats = strategy_call(symbol, interval, category, df)
        

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

    bt = Backtest(df, Bollinger_EMA, cash=10000, commission=0.0006, margin = 1/20, hedging=True)
    stats = bt.run()
    print(stats)
    return(stats)

def run_bt_bolEMA2(symbol, interval, category, df_old):
    df=df_old.copy()
    symbol = symbol
    interval = interval
    category = category

    backcandles= 6
    df['Fast_EMA'] = ta.ema(df['Close'], length=7)
    df['Slow_EMA'] = ta.ema(df['Close'], length=15)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['ATR'] = ta.atr(df['High'], df['Low'],df['Close'], length=7)
    bbands = ta.bbands(df['Close'], length = 20, std = 2.5 )
    df = df.join(bbands)
    df['EMA_SIGNAL'] = [ema_signal(df, i,backcandles) if i >= backcandles - 1 else 0 for i in range(len(df))]
    df['TOTAL_SIGNAL'] = [total_signal(df, i,backcandles) if i >= backcandles-1 else 0 for i in range(len(df))]

    bt = Backtest(df, Bollinger_EMA2, cash=100000, commission=0.0006, margin = 1/20, hedging=True)
    stats = bt.run()

    print(stats)    
    print(df[df['TOTAL_SIGNAL']!= 0].head(20))
    print(stats['_trades'])

    plot_graph(df)
    sleep(5)

    bt.plot()
    '''
    '''
    
    return stats

def run_bt_rsi_crossover(symbol, interval, category, df):

    symbol = symbol
    interval = interval
    category = category
    
    bt = Backtest(df, RSI_crossover, cash=100000, commission=0.0006, margin = 1/20, hedging=True)
    stats = bt.run()
    #optimize_plot_rsi_cross(bt, True)
    return stats

def run_test_strategy(symbol, interval, category, df):
    symbol = symbol
    interval = interval
    category = category
    bt = Backtest(df, TestStrategy, cash=100000, commission=0.0006)
    #stats = optimize_plot_test(bt, True)
    stats = bt.run()
    #print_stats(stats)

    #bt.plot()
    return stats

if __name__ == "__main__":

    symbol='HIVEUSDT'
    interval = Client.KLINE_INTERVAL_5MINUTE
    category = 'linear'
    start_date = '1 December 2024'
    df = fetch_market_data_binance(symbol,interval, start_date)
    #,  'XRPUSDT', 'ENAUSDT','DOGEUSDT','LTCUSDT', 'LINKUSDT', 'HIVEUSDT
    symbols =  ['BTCUSDT', 'SOLUSDT', 'SUIUSDT', 'ETHUSDT', 'XRPUSDT', 'ENAUSDT','DOGEUSDT','LTCUSDT', 'LINKUSDT', 'HIVEUSDT']
    #results_df = mass_run_symbols(symbols, interval, category, start_date, run_test_strategy)
    
    #run_bt_bolEMA(symbol, interval, category, df)
    #run_bt_bolEMA2(symbol, interval, category, df)
    run_test_strategy(symbol, interval, category, df)
