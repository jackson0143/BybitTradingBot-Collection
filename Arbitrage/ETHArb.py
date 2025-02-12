from web3 import Web3
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
load_dotenv()


#connect to Bybit
session = HTTP(
            testnet=False,
            demo=True,
            api_key=os.getenv('API_DEMO_KEY'),
            api_secret=os.getenv('API_DEMO_SECRET'),
        )


MODES = {
    "ETH_MAINNET": {
        "rpc_url": "https://eth-mainnet.g.alchemy.com/v2/UOBeAHf4jluntGlzzWNaEi3pWwl7MKBF",
        "uniswap_v2_factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "usdc_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "weth_address": "0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
    "ARBITRUM": {
        "rpc_url": "https://arb-mainnet.g.alchemy.com/v2/UOBeAHf4jluntGlzzWNaEi3pWwl7MKBF",
        "uniswap_v2_factory": "0xf1D7CC64Fb4452F05c498126312eBE29f30Fbcf9",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "weth_address": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
    },
}
NETWORK_MODE = "ARBITRUM" 
ALCHEMY_RPC_URL = MODES[NETWORK_MODE]["rpc_url"]
UNISWAP_V2_FACTORY = MODES[NETWORK_MODE]["uniswap_v2_factory"]

USDC_ADDRESS = Web3.to_checksum_address(MODES[NETWORK_MODE]["usdc_address"])
WETH_ADDRESS = Web3.to_checksum_address(MODES[NETWORK_MODE]["weth_address"])

web3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))


UNISWAP_V2_FACTORY_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenA",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "tokenB",
                "type": "address"
            }
        ],
        "name": "getPair",
        "outputs": [
            {
                "internalType": "address",
                "name": "pair",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''
UNISWAP_V2_PAIR_ABI = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"}
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''
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
            print("📈 Arbitrage Opportunity: Buy on Uniswap, Sell on Bybit!")
        else:
            print("📉 Arbitrage Opportunity: Buy on Bybit, Sell on Uniswap!")
    else:
        print("No profitable arbitrage opportunity found.")

def execute_arbitrage():
    """Fetch prices and check for arbitrage opportunities."""
    while True:
        uniswap_price = get_uniswap_price_factory(USDC_ADDRESS, WETH_ADDRESS)
        bybit_price = get_bybit_price('ETHUSDT')
        print(f"📊 Uniswap ({NETWORK_MODE}) Price: {uniswap_price}, Bybit Price: {bybit_price}")
        check_arbitrage_opportunity(uniswap_price, bybit_price)


execute_arbitrage()