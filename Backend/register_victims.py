from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Backend import config
from Backend.utils.hashing import generate_identity_hash_bytes32
from Backend.utils.logging_utils import get_logger
from Backend.utils.validation import ensure_no_duplicates, load_csv_safely

logger = get_logger("register_victims")

try:
    from web3 import Web3
except ImportError as exc:
    Web3 = None
    _WEB3_IMPORT_ERROR = exc
else:
    _WEB3_IMPORT_ERROR = None

def _require_web3():
    if Web3 is None:
        raise ImportError(
            "web3 is not installed. Install dependencies with 'pip install -r requirements.txt' first."
        ) from _WEB3_IMPORT_ERROR

def _load_contract(w3):
    with open(config.ABI_PATH, "r", encoding="utf-8") as f:
        abi_data = json.load(f)
    abi = abi_data["abi"] if isinstance(abi_data, dict) and "abi" in abi_data else abi_data
    return w3.eth.contract(address=Web3.to_checksum_address(config.CONTRACT_ADDRESS), abi=abi)

def _extract_allocated_wei(row: pd.Series) -> int:
    if config.COL_ALLOCATED_WEI in row and pd.notna(row[config.COL_ALLOCATED_WEI]):
        return int(row[config.COL_ALLOCATED_WEI])
    if config.COL_ALLOCATED_ETH in row and pd.notna(row[config.COL_ALLOCATED_ETH]):
        return int(round(float(row[config.COL_ALLOCATED_ETH]) * config.WEI_PER_ETH))
    if config.COL_ALLOCATED in row and pd.notna(row[config.COL_ALLOCATED]):
        return int(round(float(row[config.COL_ALLOCATED]) * config.BDT_TO_WEI))
    raise ValueError("No allocation amount column found in fund_allocation.csv")

def main(allocation_csv: str | Path | None = None) -> pd.DataFrame:
    _require_web3()
    config.require_non_empty("CONTRACT_ADDRESS", config.CONTRACT_ADDRESS)
    config.require_non_empty("ADMIN_PRIVATE_KEY", config.ADMIN_PRIVATE_KEY)
    config.require_non_empty("HASH_SECRET", config.HASH_SECRET)

    allocation_csv = Path(allocation_csv or config.ALLOCATION_CSV)
    df = load_csv_safely(
        allocation_csv,
        [config.COL_VICTIM_ID, config.COL_NID, config.COL_NAME, config.COL_SCORE],
    )
    ensure_no_duplicates(df, config.COL_NID, "fund allocation")

    logger.info("Connecting to blockchain node at %s", config.GANACHE_URL)
    w3 = Web3(Web3.HTTPProvider(config.GANACHE_URL))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to blockchain node at {config.GANACHE_URL}")

    contract = _load_contract(w3)
    admin = w3.eth.account.from_key(config.ADMIN_PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(admin.address)
    logs = []
    success_count = 0

    ganache_accounts = w3.eth.accounts
    if len(ganache_accounts) < 2:
        raise ValueError("At least 2 blockchain accounts are required (1 admin + 1 recipient)")

    for idx, row in df.iterrows():
        victim_id = int(row[config.COL_VICTIM_ID])
        nid = str(row[config.COL_NID])
        name = str(row.get(config.COL_NAME, ""))
        score_int = int(round(float(row[config.COL_SCORE]) * 100))
        allocated_wei = _extract_allocated_wei(row)
        identity_hash = generate_identity_hash_bytes32(nid, name, config.HASH_SECRET)
        wallet_idx = (idx % (len(ganache_accounts) - 1)) + 1
        wallet = ganache_accounts[wallet_idx]

        try:
            tx = contract.functions.registerVictim(
                identity_hash,
                score_int,
                allocated_wei,
                wallet,
            ).build_transaction(
                {
                    "from": admin.address,
                    "nonce": nonce,
                    "gas": 400000,
                    "gasPrice": w3.to_wei("20", "gwei"),
                    "chainId": config.CHAIN_ID,
                }
            )
            signed = w3.eth.account.sign_transaction(tx, config.ADMIN_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            ok = receipt.status == 1
            success_count += int(ok)

            logs.append(
                {
                    "Victim_ID": victim_id,
                    "NID": nid,
                    "Score_x100": score_int,
                    "Allocated_Wei": allocated_wei,
                    "Wallet": wallet,
                    "TxHash": tx_hash.hex(),
                    "Block": receipt.blockNumber,
                    "GasUsed": receipt.gasUsed,
                    "Status": "SUCCESS" if ok else "FAILED",
                }
            )
            nonce += 1
            time.sleep(0.05)

        except Exception as exc:
            logger.exception("Victim registration failed | id=%s nid=%s", victim_id, nid)
            logs.append(
                {
                    "Victim_ID": victim_id,
                    "NID": nid,
                    "Score_x100": score_int,
                    "Allocated_Wei": allocated_wei,
                    "Wallet": wallet,
                    "TxHash": "",
                    "Block": 0,
                    "GasUsed": 0,
                    "Status": f"ERROR: {str(exc)[:100]}",
                }
            )

    log_df = pd.DataFrame(logs)
    log_df.to_csv(config.REGISTRATION_CSV, index=False)

    print("=" * 60)
    print("BLOCK-RELIEF : BULK VICTIM REGISTRATION")
    print("=" * 60)
    print(f"Admin:              {admin.address}")
    print(f"Contract:           {config.CONTRACT_ADDRESS}")
    print(f"Registered:         {success_count}/{len(df)}")
    print(f"Registration log:   {config.REGISTRATION_CSV}")
    return log_df

if __name__ == "__main__":
    main()