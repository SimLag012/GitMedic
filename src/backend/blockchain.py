import os
from rich import print as rprint

from web3 import Web3
from backend.config import setup_config

setup_config()

def register_agent_identity():
    """
    Registers the agent identity (ERC-8004) at project startup.
    """
    if os.getenv("SKIP_BLOCKCHAIN", "false").lower() == "true":
        rprint("SKIP_BLOCKCHAIN=true: Skipping on-chain registration for testing.")
        return True

    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("OPERATOR_WALLET_PRIVATE_KEY")
    
    # In a production build, this would contain the registry contract address
    # and the complete transaction setup.
    
    if not private_key or not rpc_url:
        rprint("Blockchain settings not configured (RPC_URL or PRIVATE_KEY missing). \n"
              "The agent will not be registered on-chain.")
        return False
        
    # w3 = Web3(Web3.HTTPProvider(rpc_url))
    # if not w3.is_connected():
    #     rprint("Blockchain connection failed.")
    #     return False
        
    rprint("Starting ERC-8004 registration...")
    # Mock code for smart contract registration:
    # contract = w3.eth.contract(address=REGISTRY_ADDRESS, abi=ABI)
    # tx = contract.functions.registerAgent(agentAddress, metadataURI).buildTransaction({...})
    # signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    # tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    rprint("Agent registered successfully! (Mock)")
    return True
