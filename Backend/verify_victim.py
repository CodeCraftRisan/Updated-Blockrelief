import pandas as pd
import os
import sys
from pathlib import Path

# Add script directory to sys.path to resolve config import from any working directory
sys.path.append(str(Path(__file__).resolve().parent))
import config

# --- File Paths ---
BASELINE_DB_PATH = config.NID_DB_CSV
VOLUNTEER_INPUT_PATH = config.VOLUNTEER_CSV
VERIFIED_OUTPUT_PATH = config.VERIFIED_CSV
REJECTED_OUTPUT_PATH = config.REJECTED_CSV
VERIFICATION_REPORT_PATH = config.DATA_DIR / 'verification_report.txt'

# --- Validation Rules (Based on Sylhet 2022 realistic ranges) ---
VALID_RANGES = {
    'Water_Depth_ft': (0.5, 15.0),
    'Duration_Days': (1, 30),
    'Distance_km': (0.1, 20.0)
}

def verify_victims():
    """
    Anti-Fraud Verification Layer for Block-Relief.
    1. Loads volunteer field data and trusted baseline database.
    2. Detects duplicate NID submissions.
    3. Validates numerical ranges.
    4. Merges with baseline to verify NID existence.
    5. Flags and logs all rejected entries.
    6. Outputs verified victims and a verification report.
    """
    print("=" * 60)
    print("BLOCK-RELIEF: ANTI-FRAUD VERIFICATION LAYER")
    print("=" * 60)

    # ========== 1. Load Datasets ==========
    try:
        baseline_df = pd.read_csv(BASELINE_DB_PATH)
        volunteer_df = pd.read_csv(VOLUNTEER_INPUT_PATH)
        print(f"Baseline database loaded: {len(baseline_df)} records")
        print(f"Volunteer input loaded:   {len(volunteer_df)} records")
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure CSV files are in the 'data' folder.")
        return

    # ========== 2. Detect Duplicate NIDs ==========
    duplicate_mask = volunteer_df.duplicated(subset='NID', keep='first')
    duplicates_df = volunteer_df[duplicate_mask].copy()
    duplicates_df['Rejection_Reason'] = 'Duplicate NID'
    
    # Keep only first occurrence of each NID
    volunteer_clean = volunteer_df.drop_duplicates(subset='NID', keep='first').copy()
    print(f"\nDuplicate NIDs found and removed: {len(duplicates_df)}")

    # ========== 3. Range Validation ==========
    range_violations = pd.DataFrame()
    
    for column, (min_val, max_val) in VALID_RANGES.items():
        if column in volunteer_clean.columns:
            invalid_mask = ~volunteer_clean[column].between(min_val, max_val)
            invalid_rows = volunteer_clean[invalid_mask].copy()
            invalid_rows['Rejection_Reason'] = f'{column} out of range [{min_val}-{max_val}]'
            range_violations = pd.concat([range_violations, invalid_rows])
            
            # Remove invalid entries from clean data
            volunteer_clean = volunteer_clean[~invalid_mask]
    
    print(f"Range violations found and removed: {len(range_violations)}")

    # ========== 4. NID Verification Against Baseline ==========
    # Using indicator=True for robust merge detection
    merged_df = pd.merge(
        volunteer_clean,
        baseline_df,
        on='NID',
        how='left',
        indicator=True
    )

    # Separate verified and unverified
    verified_mask = merged_df['_merge'] == 'both'
    
    unverified_df = merged_df[~verified_mask].copy()
    unverified_df['Rejection_Reason'] = 'NID not found in baseline database'
    
    verified_df = merged_df[verified_mask].copy()
    verified_df.drop(columns=['_merge'], inplace=True)

    print(f"NID verification - Verified: {len(verified_df)}, Unverified: {len(unverified_df)}")

    # ========== 5. Add Victim ID and Status ==========
    verified_df.insert(0, 'Victim_ID', range(1, 1 + len(verified_df)))
    verified_df['Verification_Status'] = 'Verified'

    # ========== 6. Save Verified Victims ==========
    verified_df.to_csv(VERIFIED_OUTPUT_PATH, index=False)
    print(f"\nVerified victims saved to: '{VERIFIED_OUTPUT_PATH}'")

    # ========== 7. Save All Rejected Entries ==========
    all_rejected = pd.concat([
        duplicates_df,
        range_violations,
        unverified_df[['NID', 'Water_Depth_ft', 'Duration_Days', 'Distance_km', 'Rejection_Reason']]
    ], ignore_index=True)
    
    all_rejected.to_csv(REJECTED_OUTPUT_PATH, index=False)
    print(f"Rejected entries saved to: '{REJECTED_OUTPUT_PATH}'")

    # ========== 8. Generate Verification Report ==========
    report_lines = [
        "=" * 60,
        "BLOCK-RELIEF VERIFICATION REPORT",
        "=" * 60,
        f"Total volunteer submissions:    {len(volunteer_df)}",
        f"Duplicate NIDs removed:         {len(duplicates_df)}",
        f"Range violations removed:       {len(range_violations)}",
        f"Unverified NIDs (not in DB):    {len(unverified_df)}",
        f"Total rejected:                 {len(all_rejected)}",
        "-" * 60,
        f"FINAL VERIFIED VICTIMS:         {len(verified_df)}",
        f"Verification Rate:              {len(verified_df)/len(volunteer_df)*100:.1f}%",
        f"Fraud Detection Rate:           {len(all_rejected)/len(volunteer_df)*100:.1f}%",
        "=" * 60
    ]
    
    report_text = '\n'.join(report_lines)
    print(f"\n{report_text}")

    with open(VERIFICATION_REPORT_PATH, 'w') as f:
        f.write(report_text)
    print(f"\nReport saved to: '{VERIFICATION_REPORT_PATH}'")

    # ========== 9. Preview Output ==========
    print("\n--- Verified Victims (First 5) ---")
    print(verified_df.head().to_string(index=False))
    
    if len(all_rejected) > 0:
        print("\n--- Rejected Entries (All) ---")
        print(all_rejected.to_string(index=False))

if __name__ == "__main__":
    config.DATA_DIR.mkdir(exist_ok=True)
    verify_victims()