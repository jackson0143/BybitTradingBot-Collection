from web3 import Web3
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
load_dotenv()

from constants import *
from abis import *
#connect to Bybit
session = HTTP(
            testnet=False,
            demo=True,
            api_key=os.getenv('API_DEMO_KEY'),
            api_secret=os.getenv('API_DEMO_SECRET'),
        )


MODES = {
    "ETH_MAINNET": {
        "rpc_url": RPC_URL_MAINNET,

        "usdc_address": USDC_ADDRESS_MAINNET,
        "weth_address": WETH_ADDRESS_MAINNET,
    },
    "ARBITRUM": {
        "rpc_url": RPC_URL_ARBITRUM,
        "usdc_address": USDC_ADDRESS_ARBITRUM,
        "weth_address": WETH_ADDRESS_ARBITRUM,
    },
}
NETWORK_MODE = "ETH_MAINNET" 

USDC_ADDRESS = Web3.to_checksum_address(MODES[NETWORK_MODE]["usdc_address"])
WETH_ADDRESS = Web3.to_checksum_address(MODES[NETWORK_MODE]["weth_address"])

web3 = Web3(Web3.HTTPProvider(RPC_URL_MAINNET))


#init factory contract
factory_contract = web3.eth.contract(address=UNISWAP_V2_FACTORY, abi=UNISWAP_V2_FACTORY_ABI)



def get_uniswap_price_factory(TOKEN_A, TOKEN_B):
    try: 
        # Get Pair Address on Arbitrum
        pair_address = factory_contract.functions.getPair(TOKEN_A, TOKEN_B).call()
        
        if pair_address == "0x0000000000000000000000000000000000000000":
            print("Pair does not exist on Uniswap (Arbitrum)")
            return None

        #init the Pair contract
        pair_contract = web3.eth.contract(address=pair_address, abi=UNISWAP_V2_PAIR_ABI)

        # Get reserves
        reserves = pair_contract.functions.getReserves().call()
        token0 = pair_contract.functions.token0().call()
        token1 = pair_contract.functions.token1().call()

        if token0 == WETH_ADDRESS:
            weth_reserve = reserves[0] / 10**18
            usdc_reserve = reserves[1] / 10**6
        else:
            usdc_reserve = reserves[0] / 10**6
            weth_reserve = reserves[1] / 10**18
        # Calculate ETH price in USDC
    
        eth_price = usdc_reserve / weth_reserve

        return eth_price
    
    except Exception as e:
        print(f"Error fetching Uniswap price: {e}")
        return None


def get_bybit_price(ticker):
    try:
        response = session.get_tickers(category="linear",symbol=ticker)   
        
        return float(response["result"]['list'][0]['lastPrice'])
    except Exception as e:
        print(f"Error fetching price from Bybit: {e}")
        return None
    


def check_arbitrage_opportunity(uniswap_price, bybit_price, threshold=0.5):
    """
    threshold: Minimum % difference to consider arbitrage profitable.
    """
    if not uniswap_price or not bybit_price:
        print("Error could not fetch prices")
        return
    price_difference = abs(uniswap_price - bybit_price)
    price_difference_percentage = (price_difference / bybit_price) * 100

    print(f"Price Difference: {price_difference:.2f} USDT ({price_difference_percentage:.2f}%)")

    if price_difference_percentage > threshold:
        if uniswap_price < bybit_price:
            print("Buy on Uniswap, Sell on Bybit!")
        else:
            print("Buy on Bybit, Sell on Uniswap!")
    else:
        print("No opportunity found.")

def execute_arbitrage():

    while True:
        uniswap_price = get_uniswap_price_factory(USDC_ADDRESS, WETH_ADDRESS)
        bybit_price = get_bybit_price('ETHUSDT')
        print(f"({NETWORK_MODE}) Price: {uniswap_price}, Bybit Price: {bybit_price}")
        check_arbitrage_opportunity(uniswap_price, bybit_price)


execute_arbitrage()