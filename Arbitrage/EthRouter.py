from web3 import Web3
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
load_dotenv()
from constants import *


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
ALCHEMY_RPC_URL = MODES[NETWORK_MODE]["rpc_url"]
USDC_ADDRESS = Web3.to_checksum_address(MODES[NETWORK_MODE]["usdc_address"])
WETH_ADDRESS = Web3.to_checksum_address(MODES[NETWORK_MODE]["weth_address"])
web3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))

UNISWAP_V2_ROUTER_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsIn",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''


router_contract = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_ROUTER),abi=UNISWAP_V2_ROUTER_ABI)





def router_usdc_to_weth(amount_usdc):
    """Fetch how much WETH you get for amount_usdc (Uniswap)."""
    try:
        amount_in_wei = int(amount_usdc * 10**6)  # Convert USDC (6 decimals) to smallest unit
        path = [USDC_ADDRESS, WETH_ADDRESS]  # USDC → WETH

        amounts_out = router_contract.functions.getAmountsOut(amount_in_wei, path).call()
        weth_received = Web3.from_wei(amounts_out[1], 'ether')  # Convert WETH back to 18 decimals

        print(f"{amount_usdc} USDC buys = {weth_received:.6f} WETH on Uniswap")
        return weth_received
    except Exception as e:
        print(f"Error fetching Uniswap price: {e}")
        return None
def router_weth_to_usdc(amount_weth):
    """Fetch how much USDC you get for amount_weth (Uniswap)."""
    try:
        amount_in_wei = Web3.to_wei(amount_weth, 'ether') 
        path = [WETH_ADDRESS, USDC_ADDRESS]  # WETH → USDC

        amounts_out = router_contract.functions.getAmountsOut(amount_in_wei, path).call()
        usdc_received = amounts_out[1] / 10**6  # Convert USDC back to 6 decimals

        print(f"{amount_weth} WETH sells for = {usdc_received:.2f} USDC on Uniswap")
        return usdc_received
    except Exception as e:
        print(f"Error fetching Uniswap price: {e}")
        return None


def get_bybit_price(ticker):
    try:
        response = session.get_tickers(category="spot",symbol=ticker)   
        
        return float(response["result"]['list'][0]['lastPrice'])
    except Exception as e:
        print(f"Error fetching price from Bybit: {e}")
        return None
    



def execute_arbitrage():
    """Fetch prices from Uniswap (Factory & Router) and Bybit, then compare them."""

    #How much WETH can i buy with 1000 USDC
   
    usdc_to_weth = router_usdc_to_weth(2696)


    usdc_amount = router_weth_to_usdc(1)

 
    # Get price from Bybit
    bybit_price = get_bybit_price('ETHUSDT')
    print(bybit_price)



    #check_arbitrage_opportunity(uniswap_price_router, bybit_price)

#router for mainnet quite accurate
execute_arbitrage()