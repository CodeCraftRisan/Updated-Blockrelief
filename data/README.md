# Dataset Description

This folder contains synthetic data used for evaluating the Block-Relief prototype. These datasets simulate a real-world flood relief operation in the Sylhet region of Bangladesh.

## Core Files

- **National_ID_Database.csv:** A synthetic ground-truth database representing the national identity records. Used for verifying victim identities.
- **volunteer_input.csv:** Simulated field data collected by volunteers, including flood depth, duration, and proximity to shelters. Contains intentional errors and unregistered NIDs to test the anti-fraud layer.
- **bank_accounts.csv:** Dummy electronic banking records for simulated fund transfers.

## Pipeline Output Files

- **verified_victims.csv:** List of victims who successfully passed the NID verification and range checks.
- **rejected_entries.csv:** Records that were flagged as fraudulent or invalid, along with the reason for rejection.
- **scored_victims.csv:** Victims with calculated vulnerability scores based on Fuzzy AHP weights.
- **fund_allocation.csv:** The final allocation table showing how much BDT and ETH is assigned to each victim.
- **fuzzy_ahp_weights.csv:** The criteria weights derived from aggregated survey responses.
- **fairness_analysis_results.csv:** Key fairness metrics, including Gini coefficients for the proposed vs. baseline systems.

## Visualization Artifacts

- **lorenz_curve.png:** A plot comparing the cumulative fund distribution of Block-Relief against a perfect equality baseline.
- **distribution_outcome_report.png:** A multi-panel dashboard showing demographic and socio-economic breakdowns of the fund distribution.

## Privacy and Ethics

All identity data in these CSV files (names, NIDs, phone numbers, addresses) is **entirely synthetic** and generated using random seeds. No real-world personal information is included. This data is intended for academic research and framework validation only.
