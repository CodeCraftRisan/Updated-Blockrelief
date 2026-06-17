import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add script directory to sys.path to resolve config import from any working directory
sys.path.append(str(Path(__file__).resolve().parent))
import config

def generate_large_scale_datasets(num_victims=100, num_volunteers=110):
    """
    Generates three large-scale, realistic datasets for Block-Relief thesis:
    1. National_ID_Database.csv (Trusted Baseline Source)
    2. volunteer_input.csv (Field Data with intentional errors for anti-fraud testing)
    3. bank_accounts.csv (Dummy E-Banking accounts)
    """
    print(f"Generating large-scale datasets for {num_victims} victims...")
    
    np.random.seed(42)
    
    # --- Realistic Bengali Names ---
    first_names = ['Abdul', 'Fatema', 'Rahim', 'Karim', 'Amina', 'Jamal', 'Rashida',
                   'Sumon', 'Nasrin', 'Belal', 'Halima', 'Tariq', 'Shahana', 'Mokbul',
                   'Roksana', 'Habib', 'Kulsum', 'Anwar', 'Salma', 'Mizan', 'Nurjahan',
                   'Rafiq', 'Dilara', 'Shafiq', 'Josna', 'Babul', 'Monira', 'Sohel',
                   'Parvin', 'Aziz']
    last_names = ['Hossain', 'Begum', 'Uddin', 'Akter', 'Islam', 'Rahman', 'Khatun',
                  'Ahmed', 'Mia', 'Sarker', 'Khan', 'Sultana', 'Ali', 'Parveen', 'Chowdhury']
    
    upazilas = ['Companiganj', 'Sunamganj Sadar', 'Gowainghat', 'Jaintiapur',
                'Bishwamvarpur', 'Tahirpur', 'Zakiganj', 'Kanaighat',
                'Osmaninagar', 'Balaganj']

    # --- 1. National ID Database (Ground Truth) ---
    nids = [f'NID{str(i).zfill(5)}' for i in range(1, num_victims + 1)]
    
    baseline_data = {
        'NID': nids,
        'Name': [f'{np.random.choice(first_names)} {np.random.choice(last_names)}'
                 for _ in range(num_victims)],
        'Upazila': np.random.choice(upazilas, num_victims),
        'House_Type': np.random.choice([1, 2, 3], num_victims, p=[0.15, 0.30, 0.55]),
        'Poverty_Index': np.round(np.random.uniform(0.3, 1.0, num_victims), 2),
        'Phone': [f'+8801{np.random.choice([3,5,6,7,8,9])}{np.random.randint(10000000, 99999999)}'
                  for _ in range(num_victims)],
        'MFS_Account': [f'bKash-{str(i).zfill(5)}' for i in range(1, num_victims + 1)]
    }
    baseline_df = pd.DataFrame(baseline_data)

    # --- 2. Volunteer Input (With Intentional Errors) ---
    num_fake = num_volunteers - num_victims  # 10 fake entries
    volunteer_nids = list(nids) + [f'NID_FAKE_{i}' for i in range(1, num_fake + 1)]
    np.random.shuffle(volunteer_nids)

    volunteer_data = {
        'NID': volunteer_nids,
        'Water_Depth_ft': np.round(np.random.uniform(1, 12, num_volunteers), 1),
        'Duration_Days': np.random.randint(1, 20, num_volunteers),
        'Distance_km': np.round(np.random.uniform(0.5, 15, num_volunteers), 1)
    }
    volunteer_df = pd.DataFrame(volunteer_data)

    # --- 3. Bank Accounts Database ---
    bank_data = {
        'NID': nids,
        'Account_Number': [f'ACC{str(i).zfill(5)}' for i in range(1, num_victims + 1)],
        'Account_Holder': baseline_df['Name'].values,
        'Current_Balance': np.zeros(num_victims),
        'MFS_Linked': baseline_df['MFS_Account'].values
    }
    bank_df = pd.DataFrame(bank_data)

    # --- 4. Save Files ---
    config.DATA_DIR.mkdir(exist_ok=True)

    baseline_df.to_csv(config.NID_DB_CSV, index=False)
    volunteer_df.to_csv(config.VOLUNTEER_CSV, index=False)
    bank_df.to_csv(config.BANK_ACCOUNTS_CSV, index=False)

    print(f"Successfully generated 3 files in '{config.DATA_DIR}' folder:")
    print(f"   - {config.NID_DB_CSV.name} ({len(baseline_df)} rows)")
    print(f"   - {config.VOLUNTEER_CSV.name} ({len(volunteer_df)} rows, {num_fake} fake NIDs)")
    print(f"   - {config.BANK_ACCOUNTS_CSV.name} ({len(bank_df)} rows)")
    
    # --- 5. Print Sample for Verification ---
    print("\n--- Sample: National_ID_Database (first 3 rows) ---")
    print(baseline_df.head(3).to_string(index=False))
    print("\n--- Sample: volunteer_input (first 3 rows) ---")
    print(volunteer_df.head(3).to_string(index=False))

if __name__ == "__main__":
    generate_large_scale_datasets(num_victims=100, num_volunteers=110)