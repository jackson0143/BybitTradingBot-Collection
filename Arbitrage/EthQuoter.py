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





web3 = Web3(Web3.HTTPProvider(RPC_URL_MAINNET))



quoter_contract = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V3_QUOTER), abi=UNISWAP_V3_QUOTER_ABI)
def get_usdc_for_weth(amount_in_eth, fee_tier=3000):
    """
    Gets a Uniswap V3 quote for swapping WETH → USDC.
    
    :param amount_in_eth: Amount of WETH to swap.
    :param fee_tier: Uniswap V3 pool fee (default: 3000 = 0.3%).
    :return: Expected USDC output amount.
    """
    try:
        # Convert ETH amount to Wei
        amount_in_wei = int(amount_in_eth * 10**18)

        # Call the Uniswap V3 Quoter contract to get an exact quote
        quoted_amount_out = quoter_contract.functions.quoteExactInputSingle(
            Web3.to_checksum_address(WETH_ADDRESS_MAINNET),  # Token in (WETH)
            Web3.to_checksum_address(USDC_ADDRESS_MAINNET),  # Token out (USDC)
            fee_tier,      # Fee tier (500 = 0.05%, 3000 = 0.3%, 10000 = 1%)
            amount_in_wei, # Amount of WETH to swap
            0              # SqrtPriceLimitX96 (set to 0 for no limit)
        ).call()

        # Convert output from raw units (USDC has 6 decimals)
        usdc_output = quoted_amount_out / 10**6
        return usdc_output

    except Exception as e:
        print(f"Error fetching Uniswap V3 quote: {e}")
        return None
    



def get_usdc_needed_for_weth(amount_out_weth, fee_tier=3000):
    """
    Get the exact USDC needed to buy 1 WETH from Uniswap V3.
    Gets a Uniswap V3 quote for swapping USDC → WETH.
    :param amount_out_weth: Amount of WETH to buy (e.g., 1 WETH).
    :param fee_tier: Uniswap V3 pool fee (default: 0.3%).
    :return: USDC amount needed.
    """
    try:
        amount_out_wei = int(amount_out_weth * 10**18) 
        
        usdc_needed = quoter_contract.functions.quoteExactOutputSingle(
            Web3.to_checksum_address(USDC_ADDRESS_MAINNET),  # Buying with USDC
            Web3.to_checksum_address(WETH_ADDRESS_MAINNET),  # Receiving WETH
            fee_tier, 
            amount_out_wei, 
            0  
        ).call()

        return usdc_needed / 10**6  # Convert to USDC format

    except Exception as e:
        print(f"Error fetching required USDC for WETH purchase: {e}")
        return None

usdc_needed = get_usdc_needed_for_weth(1)
print(f"USDC needed to buy 1 WETH: {usdc_needed} USDC")

usdc_received = get_usdc_for_weth(1)
print(f"1 WETH -> USDC: {usdc_received} USDC")

