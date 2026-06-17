import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Backend import config
from Backend.utils.logging_utils import get_logger

logger = get_logger("baseline_comparison")

def run_baseline_comparison():
    logger.info("Starting Baseline Comparison")

    # Load scored victims
    try:
        df = pd.read_csv(config.ALLOCATION_CSV)
    except FileNotFoundError:
        logger.error("Fund allocation file not found. Run pipeline first.")
        return

    # Baselines
    # 1. Equal distribution (already in Traditional_Equal_BDT)
    # 2. Poverty-only distribution
    # 3. Flood-depth-only distribution

    total_fund = config.TOTAL_FUND_POOL_BDT
    n = len(df)

    # Poverty-only
    poverty_scores = df['Poverty_Index']
    df['Alloc_Poverty_Only'] = (total_fund * (poverty_scores / poverty_scores.sum())).round(0)

    # Flood-depth-only
    depth_scores = df['Water_Depth_ft']
    df['Alloc_Depth_Only'] = (total_fund * (depth_scores / depth_scores.sum())).round(0)

    baselines = {
        'Fuzzy AHP (Proposed)': df['Allocated_Fund_BDT'],
        'Equal Distribution': df['Traditional_Equal_BDT'],
        'Poverty-Only': df['Alloc_Poverty_Only'],
        'Flood-Depth-Only': df['Alloc_Depth_Only']
    }

    results = []

    def gini(v):
        v = np.sort(np.array(v, dtype=float))
        n = len(v)
        if n == 0 or v.sum() == 0: return 0
        return (np.sum((2 * np.arange(1, n + 1) - n - 1) * v)) / (n * np.sum(v))

    for name, alloc in baselines.items():
        results.append({
            'Model': name,
            'Gini': round(gini(alloc), 4),
            'Min': alloc.min(),
            'Max': alloc.max(),
            'Std Dev': round(alloc.std(), 2)
        })

    results_df = pd.DataFrame(results)
    logger.info("\n" + results_df.to_string(index=False))

    results_df.to_csv(config.REPORTS_DIR / "baseline_comparison.csv", index=False)

    # Plotting
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(12, 6))

    # Sort by Fuzzy AHP for consistent x-axis
    df_sorted = df.sort_values('Vulnerability_Score').reset_index()

    ax.plot(df_sorted['Allocated_Fund_BDT'], label='Fuzzy AHP (Proposed)', linewidth=2)
    ax.plot(df_sorted['Alloc_Poverty_Only'], label='Poverty-Only', alpha=0.6)
    ax.plot(df_sorted['Alloc_Depth_Only'], label='Flood-Depth-Only', alpha=0.6)
    ax.axhline(y=total_fund/n, color='k', linestyle='--', label='Equal Distribution')

    ax.set_title("Fund Allocation: Proposed vs Baselines")
    ax.set_xlabel("Victims (sorted by Vulnerability Score)")
    ax.set_ylabel("Allocation (BDT)")
    ax.legend()

    plt.savefig(config.REPORTS_DIR / "baseline_comparison.png")
    logger.info(f"Baseline comparison plot saved to {config.REPORTS_DIR / 'baseline_comparison.png'}")

if __name__ == "__main__":
    run_baseline_comparison()
