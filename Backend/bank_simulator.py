"""
============================================================
  Block-Relief : Dummy Banking Simulator
============================================================
  কাজ:
   - Smart contract থেকে কোনো victim-কে ETH পাঠানো হলে,
     এই module সেই ETH-কে BDT-তে convert করে bank account-এ
     যোগ করে (CSV-based simulation)।
   - bKash/Nagad-এর real API call করা hardware/license ছাড়া
     সম্ভব নয়, তাই thesis-এর জন্য এটা realistic simulation।

  তোমার bank_accounts.csv structure:
    NID, Account_Number, Account_Holder, Current_Balance, MFS_Linked
============================================================
"""

import pandas as pd
from datetime import datetime

import config


# ---- Cache victim_id -> NID lookup (one-time load) ----
_victim_nid_map = None
_victim_phone_map = None


def _load_victim_lookup():
    """fund_allocation.csv থেকে Victim_ID → (NID, Phone) mapping তৈরি করো"""
    global _victim_nid_map, _victim_phone_map
    if _victim_nid_map is not None:
        return

    df = pd.read_csv(config.ALLOCATION_CSV)
    _victim_nid_map   = dict(zip(df[config.COL_VICTIM_ID].astype(int),
                                 df[config.COL_NID].astype(str)))
    _victim_phone_map = dict(zip(df[config.COL_VICTIM_ID].astype(int),
                                 df[config.COL_PHONE]))


def ensure_bank_accounts_exist() -> pd.DataFrame:
    """
    যদি bank_accounts.csv থাকে → load করো।
    না থাকলে → fund_allocation থেকে তৈরি করো।
    """
    if config.BANK_ACCOUNTS_CSV.exists():
        return pd.read_csv(config.BANK_ACCOUNTS_CSV)

    print(f"⚠️  {config.BANK_ACCOUNTS_CSV.name} not found. Creating from allocation data...")
    alloc = pd.read_csv(config.ALLOCATION_CSV)
    rows = []
    for _, r in alloc.iterrows():
        nid = str(r[config.COL_NID])
        vid = int(r[config.COL_VICTIM_ID])
        rows.append({
            "NID":              nid,
            "Account_Number":   f"ACC{vid:05d}",
            "Account_Holder":   r.get(config.COL_NAME, "Unknown"),
            "Current_Balance":  0.0,
            "MFS_Linked":       f"bKash-{nid[-5:]}",
        })
    df = pd.DataFrame(rows)
    df.to_csv(config.BANK_ACCOUNTS_CSV, index=False)
    print(f"✅ Created {len(df)} bank accounts")
    return df


def credit_victim(victim_id: int, eth_amount_wei: int) -> dict:
    """
    একজন victim-এর bank account-এ টাকা যোগ করো (NID via lookup)।

    Parameters
    ----------
    victim_id      : Smart contract victim ID (1..100)
    eth_amount_wei : Smart contract-এ পাঠানো wei amount

    Returns
    -------
    dict : {account_number, victim_id, nid, name, previous_balance,
            new_balance, bdt_amount, eth_amount, mobile}
    """
    _load_victim_lookup()
    df = ensure_bank_accounts_exist()

    # Lookup NID from victim_id
    nid = _victim_nid_map.get(victim_id)
    if nid is None:
        raise ValueError(f"Victim_ID {victim_id} not found in fund_allocation.csv")

    # Wei → ETH → BDT
    eth_amount = eth_amount_wei / 10**18
    bdt_amount = round(eth_amount * config.ETH_TO_BDT_RATE, 2)

    mask = df["NID"].astype(str) == str(nid)
    if not mask.any():
        raise ValueError(f"NID {nid} not found in bank_accounts.csv")

    prev = float(df.loc[mask, config.COL_BALANCE].values[0])
    new  = round(prev + bdt_amount, 2)

    df.loc[mask, config.COL_BALANCE] = new
    # Add timestamp column if missing
    if "Last_Updated" not in df.columns:
        df["Last_Updated"] = ""
    df.loc[mask, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(config.BANK_ACCOUNTS_CSV, index=False)

    return {
        "victim_id":         victim_id,
        "nid":               nid,
        "account_number":    df.loc[mask, config.COL_ACC_NUM].values[0],
        "account_holder":    df.loc[mask, config.COL_ACC_HOLDER].values[0],
        "mfs_linked":        df.loc[mask, config.COL_MFS].values[0],
        "previous_balance":  prev,
        "new_balance":       new,
        "bdt_amount":        bdt_amount,
        "eth_amount":        eth_amount,
        "mobile":            config.normalize_phone(_victim_phone_map.get(victim_id, "")),
    }


# ---- CLI Self-Test ----
if __name__ == "__main__":
    print("🏦 Bank Simulator — Self Test")
    print("=" * 60)
    ensure_bank_accounts_exist()

    # Simulate VictimID=1 receiving 0.01682 ETH
    result = credit_victim(victim_id=1, eth_amount_wei=int(0.01682 * 10**18))
    print(f"\n✅ Credited Victim_ID {result['victim_id']} ({result['nid']})")
    print(f"   Account Holder  : {result['account_holder']}")
    print(f"   Account Number  : {result['account_number']}")
    print(f"   MFS Linked      : {result['mfs_linked']}")
    print(f"   Mobile          : {result['mobile']}")
    print(f"   Amount Credited : {result['bdt_amount']} BDT  ({result['eth_amount']:.6f} ETH)")
    print(f"   Old Balance     : {result['previous_balance']} BDT")
    print(f"   New Balance     : {result['new_balance']} BDT")
