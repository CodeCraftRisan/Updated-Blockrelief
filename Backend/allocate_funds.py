"""
============================================================
  Block-Relief : Dynamic Fund Allocation  (Fixed v2)
============================================================

FIX APPLIED [MEDIUM]:
  Old code: uncapped_mask checked `> MIN` AND `< MAX` after clipping.
  Problem:  Victims AT the floor (floor-capped, not uncapped) were
            incorrectly included in redistribution → they got extra money
            even though they should stay at MIN_RELIEF_BDT.

  Fix:      Track who was raw-proportional (between floor and cap)
            using the RAW allocation, not the clipped value.

============================================================
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import config

# --- File Paths ---
SCORED_VICTIMS_PATH  = config.SCORED_CSV
FUND_ALLOCATION_PATH = config.ALLOCATION_CSV

# --- Configuration ---
TOTAL_FUND_POOL_BDT = config.TOTAL_FUND_POOL_BDT
MIN_RELIEF_BDT = config.MIN_RELIEF_BDT
MAX_RELIEF_BDT = config.MAX_RELIEF_BDT


def allocate_proportional_funds():
    """
    Proportional Fund Allocation using Fuzzy AHP vulnerability scores.

    Algorithm:
      1. Raw share = TotalFund * (victim_score / total_score)
      2. Clip to [MIN, MAX]
      3. Compute surplus/deficit from clipping
      4. Redistribute surplus to victims whose raw share was BETWEEN
         floor and cap (truly uncapped — not floored, not capped)
      5. Save final allocations

    Comparison column:
      Traditional_Equal_BDT = TotalFund / N  (flat equal share baseline)
      Used in Gini coefficient analysis to show fairness improvement.
    """
    print("=" * 60)
    print("DYNAMIC FUND ALLOCATION  (Fixed v2)")
    print("=" * 60)

    try:
        scored_df = pd.read_csv(SCORED_VICTIMS_PATH)
        print(f"Scored victims loaded: {len(scored_df)} records")
    except FileNotFoundError:
        print(f"ERROR: File not found → '{SCORED_VICTIMS_PATH}'")
        print("  Run fuzzy_ahp.py first to generate scored_victims.csv")
        return

    total_score = scored_df['Vulnerability_Score'].sum()
    if total_score == 0:
        print("ERROR: Total vulnerability score is zero. Cannot allocate.")
        return

    n = len(scored_df)

    # ---- Step 1: Raw proportional allocation ----
    scored_df['Raw_Allocation_BDT'] = (
        TOTAL_FUND_POOL_BDT * (scored_df['Vulnerability_Score'] / total_score)
    ).round(2)

    # ---- Step 2: Clip to floor/cap ----
    scored_df['Allocated_Fund_BDT'] = scored_df['Raw_Allocation_BDT'].clip(
        lower=MIN_RELIEF_BDT,
        upper=MAX_RELIEF_BDT
    )

    # ---- Step 3: Compute surplus from clipping ----
    total_allocated = scored_df['Allocated_Fund_BDT'].sum()
    surplus = TOTAL_FUND_POOL_BDT - total_allocated

    # ---- Step 4: FIX — use RAW value to identify truly uncapped ----
    # "Truly uncapped" = raw share was already between floor and cap
    # (neither floored-up nor capped-down by clipping)
    truly_uncapped_mask = (
        (scored_df['Raw_Allocation_BDT'] > MIN_RELIEF_BDT) &
        (scored_df['Raw_Allocation_BDT'] < MAX_RELIEF_BDT)
    )

    if abs(surplus) > 1 and truly_uncapped_mask.any():
        uncapped_scores = scored_df.loc[truly_uncapped_mask, 'Vulnerability_Score']
        # Distribute surplus proportionally among uncapped victims
        adjustment = surplus * (uncapped_scores / uncapped_scores.sum())
        scored_df.loc[truly_uncapped_mask, 'Allocated_Fund_BDT'] += adjustment
        # Re-clip to make sure no uncapped victim accidentally exceeds cap
        scored_df.loc[truly_uncapped_mask, 'Allocated_Fund_BDT'] = \
            scored_df.loc[truly_uncapped_mask, 'Allocated_Fund_BDT'].clip(
                upper=MAX_RELIEF_BDT
            )

    scored_df['Allocated_Fund_BDT'] = scored_df['Allocated_Fund_BDT'].round(0)

    # ---- Step 5: Traditional baseline (equal distribution) ----
    equal_amount = TOTAL_FUND_POOL_BDT / n
    scored_df['Traditional_Equal_BDT'] = round(equal_amount, 0)

    # ---- Step 6: ETH equivalent (for smart contract) ----
    # config.BDT_TO_ETH = conversion rate (e.g. 0.0000085 ETH per BDT)
    bdt_to_eth = getattr(config, 'BDT_TO_ETH', 0.0000085)
    scored_df['Allocated_Fund_ETH'] = (
        scored_df['Allocated_Fund_BDT'] * bdt_to_eth
    ).round(8)

    # ---- Save ----
    priority_cols = [
        'Victim_ID', 'NID', 'Name', 'Upazila',
        'Vulnerability_Score',
        'Raw_Allocation_BDT', 'Allocated_Fund_BDT',
        'Allocated_Fund_ETH', 'Traditional_Equal_BDT',
        'Phone', 'MFS_Account'
    ]
    existing_priority = [c for c in priority_cols if c in scored_df.columns]
    remaining = [c for c in scored_df.columns if c not in existing_priority]
    final_cols = existing_priority + remaining

    scored_df[final_cols].to_csv(FUND_ALLOCATION_PATH, index=False)
    print(f"\nAllocation saved -> '{FUND_ALLOCATION_PATH}'")

    # ---- Summary ----
    floored  = (scored_df['Raw_Allocation_BDT'] < MIN_RELIEF_BDT).sum()
    capped   = (scored_df['Raw_Allocation_BDT'] > MAX_RELIEF_BDT).sum()
    uncapped = truly_uncapped_mask.sum()

    print("\n--- Allocation Summary ---")
    print(f"Total Fund Pool:          {TOTAL_FUND_POOL_BDT:>12,.0f} BDT")
    print(f"Total Allocated:          {scored_df['Allocated_Fund_BDT'].sum():>12,.0f} BDT")
    print(f"Difference (rounding):    {TOTAL_FUND_POOL_BDT - scored_df['Allocated_Fund_BDT'].sum():>12,.0f} BDT")
    print(f"Min Allocation:           {scored_df['Allocated_Fund_BDT'].min():>12,.0f} BDT")
    print(f"Max Allocation:           {scored_df['Allocated_Fund_BDT'].max():>12,.0f} BDT")
    print(f"Mean Allocation:          {scored_df['Allocated_Fund_BDT'].mean():>12,.0f} BDT")
    print(f"Traditional Equal Share:  {equal_amount:>12,.0f} BDT")
    print(f"\nClipping breakdown:")
    print(f"  Floor-capped  (< {MIN_RELIEF_BDT:,} BDT): {floored:>4} victims")
    print(f"  Cap-limited   (> {MAX_RELIEF_BDT:,} BDT): {capped:>4} victims")
    print(f"  Truly uncapped (proportional):  {uncapped:>4} victims")

    print("\n--- Top 5 Recipients ---")
    display_cols = [c for c in ['Victim_ID', 'NID', 'Vulnerability_Score',
                                 'Allocated_Fund_BDT'] if c in scored_df.columns]
    print(scored_df[display_cols].sort_values(
        'Allocated_Fund_BDT', ascending=False).head().to_string(index=False))

    print("\n--- Bottom 5 Recipients ---")
    print(scored_df[display_cols].sort_values(
        'Allocated_Fund_BDT', ascending=True).head().to_string(index=False))

    return scored_df


if __name__ == "__main__":
    allocate_proportional_funds()