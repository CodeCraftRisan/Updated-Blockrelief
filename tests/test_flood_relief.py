import pytest
from web3 import Web3
from eth_tester import EthereumTester, PyEVMBackend
from web3.providers.eth_tester import EthereumTesterProvider
import json
from pathlib import Path

# Simple test suite for FloodRelief contract using Web3.py and eth-tester

@pytest.fixture
def w3():
    return Web3(EthereumTesterProvider(EthereumTester(PyEVMBackend())))

@pytest.fixture
def contract_interface():
    # We need to compile the contract or have the ABI and Bytecode
    # Since we have solc installed via solc-select, let's use it
    import subprocess
    result = subprocess.run(
        ['solc', '--combined-json', 'abi,bin', 'contracts/FloodRelief.sol'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"Compilation failed: {result.stderr}")

    compiled = json.loads(result.stdout)
    contract_id = "contracts/FloodRelief.sol:FloodRelief"
    return compiled['contracts'][contract_id]

@pytest.fixture
def flood_relief(w3, contract_interface):
    admin = w3.eth.accounts[0]
    FloodRelief = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    tx_hash = FloodRelief.constructor(w3.to_wei(1, 'ether')).transact({'from': admin})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return w3.eth.contract(address=tx_receipt.contractAddress, abi=contract_interface['abi'])

def test_initial_state(flood_relief):
    assert flood_relief.functions.targetFund().call() == Web3.to_wei(1, 'ether')
    assert flood_relief.functions.totalDonated().call() == 0

def test_donation(w3, flood_relief):
    donor = w3.eth.accounts[1]
    tx_hash = flood_relief.functions.donate().transact({'from': donor, 'value': w3.to_wei(0.1, 'ether')})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    assert flood_relief.functions.totalDonated().call() == w3.to_wei(0.1, 'ether')

def test_victim_registration(w3, flood_relief):
    admin = w3.eth.accounts[0]
    victim_wallet = w3.eth.accounts[2]
    identity_hash = Web3.keccak(text="victim1")

    tx_hash = flood_relief.functions.registerVictim(
        identity_hash,
        8000, # score
        w3.to_wei(0.5, 'ether'), # allocatedAmount
        victim_wallet
    ).transact({'from': admin})
    w3.eth.wait_for_transaction_receipt(tx_hash)

    assert flood_relief.functions.victimCount().call() == 1
    v = flood_relief.functions.getVictim(1).call()
    assert v[1] == identity_hash
    assert v[2] == 8000

def test_duplicate_registration_fails(w3, flood_relief):
    admin = w3.eth.accounts[0]
    victim_wallet = w3.eth.accounts[2]
    identity_hash = Web3.keccak(text="victim1")

    flood_relief.functions.registerVictim(identity_hash, 8000, w3.to_wei(0.5, 'ether'), victim_wallet).transact({'from': admin})

    with pytest.raises(Exception): # Web3.py raises Exception for revert
        flood_relief.functions.registerVictim(identity_hash, 9000, w3.to_wei(0.6, 'ether'), victim_wallet).transact({'from': admin})

def test_only_admin_can_register(w3, flood_relief):
    non_admin = w3.eth.accounts[1]
    identity_hash = Web3.keccak(text="victim2")
    with pytest.raises(Exception):
        flood_relief.functions.registerVictim(identity_hash, 8000, w3.to_wei(0.5, 'ether'), w3.eth.accounts[3]).transact({'from': non_admin})
