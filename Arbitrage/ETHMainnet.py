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


# Connect to the Eth network with Alchemy
ALCHEMY_RPC_URL = 'https://eth-mainnet.g.alchemy.com/v2/UOBeAHf4jluntGlzzWNaEi3pWwl7MKBF'
web3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))
# Uniswap V2 Factory Contract
UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
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
# Uniswap V2 Pair Contract ABI
UNISWAP_V2_PAIR_ABI = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
                "internalType": "uint112",
                "name": "reserve0",
                "type": "uint112"
            },
            {
                "internalType": "uint112",
                "name": "reserve1",
                "type": "uint112"
            },
            {
                "internalType": "uint32",
                "name": "blockTimestampLast",
                "type": "uint32"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''



#Token Addresses (USDC & WETH)
USDT_ADDRESS = Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")  #USDT
USDC_ADDRESS = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")  # USDC
WETH_ADDRESS = Web3.to_checksum_address("0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2")  # Wrapped Ether

#init uniswap factory contract
factory_contract = web3.eth.contract(address=UNISWAP_V2_FACTORY, abi=UNISWAP_V2_FACTORY_ABI)

def get_uniswap_price(TOKEN_A, TOKEN_B):
     
    # Get Pair Address
    pair_address = factory_contract.functions.getPair(TOKEN_A, TOKEN_B).call()

    if pair_address == "0x0000000000000000000000000000000000000000":
        print("Pair does not exist on Uniswap V2.")
        return None

    #init the Pair contract
    pair_contract = web3.eth.contract(address=pair_address, abi=UNISWAP_V2_PAIR_ABI)

    # Get reserves
    reserves = pair_contract.functions.getReserves().call()

    usdt_reserve = reserves[0] / 10**6  # USDC has 6 decimals
    weth_reserve = reserves[1] / 10**18  # WETH has 18 decimals

    # Calculate ETH price in USDC
    eth_price = usdt_reserve / weth_reserve
    print(eth_price)
    #print(f"Current ETH Price on Uniswap V2: {eth_price} USDC")

    return eth_price


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
            print(" Buy on Bybit, Sell on Uniswap!")
    else:
        print("No opportunity found.")

def execute_arbitrage():

    while True:
        uniswap_price = get_uniswap_price(USDC_ADDRESS, WETH_ADDRESS)
        bybit_price = get_bybit_price('ETHUSDT')

        check_arbitrage_opportunity(uniswap_price, bybit_price)


execute_arbitrage()