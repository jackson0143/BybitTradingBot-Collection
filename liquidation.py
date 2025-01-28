import websocket
import json
import pandas as pd
from datetime import timedelta


'''
A liquidation stream tracker to track the coins that have been liquidated, giving the time and also the amount.
'''

from numerize import numerize 

cols = ["Symbol", "Side", "Time", "Total"]
liq_data = pd.DataFrame(columns=cols)

def on_message(ws, message):
    global liq_data
    data = json.loads(message)

    
    if data["e"] == "forceOrder":
        liq_info = data["o"]
        symbol = liq_info["s"]
        side = liq_info["S"]  #buy/sell 
        #time = liq_info["T"] #time
        utc_time = pd.to_datetime(liq_info["T"], unit='ms')


        melbourne_time = utc_time + timedelta(hours=11) 

        formatted_time = melbourne_time.strftime('%Y-%m-%d %H:%M:%S')
        total = round(float(liq_info["q"])*float(liq_info["p"]))

        total_str = numerize.numerize(total)
        if side == "BUY":
            side_desc = "Long position liquidated (BUY)"
        elif side == "SELL":
            side_desc = "Short position liquidated (SELL)"
        else:
            side_desc = side  
        new_entry = pd.DataFrame([[symbol, side_desc, formatted_time, total]], columns=cols)


        if (list_tickers == None or not list_tickers or symbol in list_tickers) and (min_price is None or total>=min_price):
            liq_data = pd.concat([liq_data, new_entry], ignore_index=True)
            print(f"{symbol.ljust(symbol_width)} {side_desc.ljust(side_width)} {str(formatted_time).ljust(time_width)} {str(total_str).ljust(total_width)}")
     

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("Connection closed")

def on_open(ws):
    print("Connected")
    print("If a ticker has the side BUY, that means the price went down too much and liquidated a long position")
    print("If a ticker has the side SHORT, that means the price went up too much and liquidated a short position")
    print(f"{'Symbol'.ljust(symbol_width)} {'Side'.ljust(side_width)} {'Time'.ljust(time_width)} {'Total'.ljust(total_width)}")


url = "wss://fstream.binance.com/ws/!forceOrder@arr"

#list_tickers = ['BTCUSDT', 'ETHUSDT','SOLUSDT', 'TRUMPUSDT' 'SUIUSDT', 'DOGEUSDT',] 
list_tickers = None
min_price = 5000

symbol_width = 15
side_width = 38
time_width = 20
total_width = 12


ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
ws.on_open = on_open

try:
    
    ws.run_forever()
except KeyboardInterrupt:
    print("Terminating the WebSocket connection.")
input("Press Enter to exit...")
