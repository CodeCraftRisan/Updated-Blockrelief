"""
============================================================
  Block-Relief : Receipt Manager (Proof-of-Delivery)
============================================================
  প্রতিটা successful payment-এর জন্য:
   1. একটা unique receipt ID তৈরি করো (FRD-YYYY-XXXX)
   2. Receipt-এর SHA-256 hash তৈরি করো (tamper-proof)
   3. CSV-এ log করো (receipts.csv)
   4. প্রতিটা receipt-এর জন্য একটা text ফাইলও বানাও (proof file)
============================================================
"""

import hashlib
import json
from datetime import datetime
import pandas as pd

import config


def _next_receipt_id() -> str:
    """Sequential receipt ID: FRD-2026-0001, FRD-2026-0002 ..."""
    year = datetime.now().year
    if config.RECEIPTS_CSV.exists():
        df = pd.read_csv(config.RECEIPTS_CSV)
        if len(df) > 0:
            try:
                last_id = df.iloc[-1]["ReceiptID"]
                num = int(str(last_id).split("-")[-1]) + 1
            except Exception:
                num = len(df) + 1
        else:
            num = 1
    else:
        num = 1
    return f"FRD-{year}-{num:04d}"


def _receipt_hash(payload: dict) -> str:
    """SHA-256 hash of receipt payload — tamper detect করতে কাজে লাগবে।"""
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "0x" + hashlib.sha256(canonical).hexdigest()


def generate_receipt(bank_result: dict, tx_hash: str) -> dict:
    """
    Bank credit successful হলে একটা tamper-proof receipt তৈরি করো।

    Parameters
    ----------
    bank_result : bank_simulator.credit_victim() এর return
    tx_hash     : Blockchain transaction hash

    Returns
    -------
    dict : full receipt record
    """
    receipt_id = _next_receipt_id()
    timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "ReceiptID":      receipt_id,
        "Victim_ID":      int(bank_result["victim_id"]),
        "NID":            str(bank_result["nid"]),
        "Account_Holder": str(bank_result["account_holder"]),
        "Account_Number": str(bank_result["account_number"]),
        "MFS_Linked":     str(bank_result["mfs_linked"]),
        "Mobile":         str(bank_result["mobile"]),
        "Amount_BDT":     float(bank_result["bdt_amount"]),
        "Amount_ETH":     float(bank_result["eth_amount"]),
        "TxHash":         str(tx_hash),
        "Timestamp":      timestamp,
    }
    payload["ReceiptHash"] = _receipt_hash(payload)

    # ---- Append to CSV ----
    df_new = pd.DataFrame([payload])
    if config.RECEIPTS_CSV.exists():
        df_old = pd.read_csv(config.RECEIPTS_CSV)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(config.RECEIPTS_CSV, index=False)

    # ---- Save individual receipt text file ----
    txt_path = config.RECEIPT_DIR / f"{receipt_id}.txt"
    txt_path.write_text(
        f"""
==============================================
       BLOCK-RELIEF PAYMENT RECEIPT
==============================================

  Receipt ID      : {payload['ReceiptID']}
  Victim ID       : {payload['Victim_ID']}
  NID             : {payload['NID']}
  Account Holder  : {payload['Account_Holder']}
  Account Number  : {payload['Account_Number']}
  MFS Linked      : {payload['MFS_Linked']}
  Mobile          : {payload['Mobile']}

  Amount Paid     : {payload['Amount_BDT']:,.2f} BDT
                    ({payload['Amount_ETH']:.6f} ETH)

  TX Hash         : {payload['TxHash']}
  Timestamp       : {payload['Timestamp']}

  ----------------------------------------------
  Receipt Hash (SHA-256):
  {payload['ReceiptHash']}
  ----------------------------------------------

  This receipt is cryptographically signed and
  cannot be altered without detection.
==============================================
""",
        encoding="utf-8",
    )

    print(f"   📄 Receipt {receipt_id} generated → {payload['Account_Holder']} ({payload['NID']})")
    return payload


# ---- CLI Self-Test ----
if __name__ == "__main__":
    print("📄 Receipt Manager — Self Test")
    print("=" * 60)
    dummy_bank = {
        "victim_id":        1,
        "nid":              "NID00091",
        "account_holder":   "Babul Khatun",
        "account_number":   "ACC00091",
        "mfs_linked":       "bKash-00091",
        "mobile":           "+8801517136029",
        "bdt_amount":       1682.50,
        "eth_amount":       0.016825,
    }
    r = generate_receipt(dummy_bank, tx_hash="0xabc123def456")
    print(json.dumps({k: v for k, v in r.items() if k != "ReceiptHash"}, indent=2))
    print(f"Hash: {r['ReceiptHash']}")
