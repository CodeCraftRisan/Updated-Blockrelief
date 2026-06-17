"""
============================================================
  Block-Relief : Fairness Analysis
============================================================
  Generates:
    1. Gini Coefficient — Block-Relief vs Flat Distribution
    2. Lorenz Curve Graph (publication-ready)
    3. Summary statistics table

  Run from project root:
    python Backend/fairness_analysis.py

  Output:
    data/fairness_analysis_results.csv
    data/lorenz_curve.png    ← use in thesis
============================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')   # no display needed — saves to file
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import config

# --- Output paths ---
OUTPUT_CSV = config.DATA_DIR / 'fairness_analysis_results.csv'
OUTPUT_PNG = config.DATA_DIR / 'lorenz_curve.png'


# ============================================================
#  GINI COEFFICIENT
# ============================================================

def gini_coefficient(values: np.ndarray) -> float:
    """
    Calculate Gini coefficient.
    Gini = 0  → perfect equality (everyone gets same)
    Gini = 1  → maximum inequality (one person gets everything)

    For flood relief:
      Lower Gini is NOT always better.
      Our system should have MODERATE Gini (high-need victims
      get more) vs flat distribution's Gini = 0.
      The point is that our Gini reflects NEED-BASED inequality,
      not arbitrary inequality.
    """
    values = np.sort(np.array(values, dtype=float))
    n = len(values)
    if n == 0 or values.sum() == 0:
        return 0.0
    index  = np.arange(1, n + 1)
    gini   = (2 * np.sum(index * values)) / (n * values.sum()) - (n + 1) / n
    return round(float(gini), 4)


def lorenz_curve_points(values: np.ndarray):
    """
    Returns (x, y) for Lorenz curve.
    x = cumulative share of population (0 to 1)
    y = cumulative share of income/funds (0 to 1)
    """
    values = np.sort(np.array(values, dtype=float))
    total  = values.sum()
    if total == 0:
        return np.array([0, 1]), np.array([0, 1])
    cum_y  = np.concatenate([[0], np.cumsum(values) / total])
    cum_x  = np.linspace(0, 1, len(cum_y))
    return cum_x, cum_y


# ============================================================
#  MAIN ANALYSIS
# ============================================================

def run_fairness_analysis():
    print("=" * 60)
    print("BLOCK-RELIEF : FAIRNESS ANALYSIS")
    print("=" * 60)

    # ---- Load data ----
    try:
        df = pd.read_csv(config.ALLOCATION_CSV)
        print(f"Loaded: {len(df)} victims from '{config.ALLOCATION_CSV}'")
    except FileNotFoundError:
        print(f"ERROR: '{config.ALLOCATION_CSV}' not found.")
        print("  Run allocate_funds.py first.")
        return

    required = ['Allocated_Fund_BDT', 'Traditional_Equal_BDT', 'Vulnerability_Score']
    for col in required:
        if col not in df.columns:
            print(f"ERROR: Column '{col}' missing from allocation CSV.")
            return

    block_relief = df['Allocated_Fund_BDT'].values
    flat_dist    = df['Traditional_Equal_BDT'].values

    # ---- Gini ----
    gini_br   = gini_coefficient(block_relief)
    gini_flat = gini_coefficient(flat_dist)

    print(f"\n--- Gini Coefficients ---")
    print(f"  Block-Relief (Fuzzy AHP):    {gini_br:.4f}")
    print(f"  Flat Equal Distribution:     {gini_flat:.4f}  (expected ~ 0)")
    print(f"\n  Interpretation:")
    print(f"  Block-Relief Gini = {gini_br:.4f} reflects NEED-BASED distribution.")
    print(f"  Higher-score (more vulnerable) victims receive proportionally more.")
    print(f"  This is INTENTIONAL and desirable - not a flaw.")

    # ---- Lorenz curve data ----
    x_br,   y_br   = lorenz_curve_points(block_relief)
    x_flat, y_flat = lorenz_curve_points(flat_dist)
    x_equal = np.array([0, 1])
    y_equal = np.array([0, 1])   # perfect equality line

    # ---- Summary statistics ----
    stats = pd.DataFrame({
        'Metric': [
            'Number of Victims',
            'Total Fund (BDT)',
            'Gini Coefficient',
            'Min Allocation (BDT)',
            'Max Allocation (BDT)',
            'Mean Allocation (BDT)',
            'Std Dev (BDT)',
            'Coefficient of Variation (%)',
        ],
        'Block-Relief (Fuzzy AHP)': [
            len(block_relief),
            f"{block_relief.sum():,.0f}",
            f"{gini_br:.4f}",
            f"{block_relief.min():,.0f}",
            f"{block_relief.max():,.0f}",
            f"{block_relief.mean():,.0f}",
            f"{block_relief.std():,.0f}",
            f"{(block_relief.std()/block_relief.mean()*100):.1f}%",
        ],
        'Flat Equal Distribution': [
            len(flat_dist),
            f"{flat_dist.sum():,.0f}",
            f"{gini_flat:.4f}",
            f"{flat_dist.min():,.0f}",
            f"{flat_dist.max():,.0f}",
            f"{flat_dist.mean():,.0f}",
            f"{flat_dist.std():,.0f}",
            f"{(flat_dist.std()/flat_dist.mean()*100 if flat_dist.mean()>0 else 0):.1f}%",
        ]
    })

    print(f"\n--- Summary Statistics ---")
    print(stats.to_string(index=False))
    stats.to_csv(OUTPUT_CSV, index=False)
    print(f"\nResults saved -> '{OUTPUT_CSV}'")

    # ---- Correlation: score vs allocation ----
    corr = np.corrcoef(
        df['Vulnerability_Score'].values,
        df['Allocated_Fund_BDT'].values
    )[0, 1]
    print(f"\n  Score-Allocation Pearson Correlation: {corr:.4f}")
    print(f"  (Should be close to 1.0 for a fair proportional system)")

    # ============================================================
    #  PLOT — Lorenz Curve (thesis quality)
    # ============================================================

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        'Block-Relief : Fairness Analysis\nLorenz Curve & Fund Distribution',
        fontsize=14, fontweight='bold', y=1.01
    )

    # ---- Left: Lorenz Curve ----
    ax1 = axes[0]
    ax1.plot(x_equal, y_equal, 'k--', linewidth=1.5, label='Perfect Equality (Gini=0)')
    ax1.plot(x_br,    y_br,    'b-',  linewidth=2.5, label=f'Block-Relief (Gini={gini_br:.4f})')
    ax1.plot(x_flat,  y_flat,  'r:',  linewidth=2.0, label=f'Flat Distribution (Gini={gini_flat:.4f})')

    # Shade area between equality line and Block-Relief curve
    ax1.fill_between(x_br, x_br, y_br, alpha=0.12, color='blue', label='Inequality Area (Block-Relief)')

    ax1.set_xlabel('Cumulative Share of Victims (sorted by allocation)', fontsize=11)
    ax1.set_ylabel('Cumulative Share of Total Funds', fontsize=11)
    ax1.set_title('Lorenz Curve Comparison', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    # Annotations
    ax1.annotate(
        f'Block-Relief\nGini = {gini_br:.4f}',
        xy=(0.5, 0.35), fontsize=9, color='blue',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.5)
    )

    # ---- Right: Allocation Distribution Plot ----
    ax2 = axes[1]

    # Sort by vulnerability score for x-axis
    df_sorted = df.sort_values('Vulnerability_Score').reset_index(drop=True)
    x_idx = np.arange(len(df_sorted))

    ax2.bar(x_idx, df_sorted['Allocated_Fund_BDT'],
            color='steelblue', alpha=0.75, width=0.8,
            label='Block-Relief Allocation')
    ax2.axhline(
        y=df_sorted['Traditional_Equal_BDT'].iloc[0],
        color='red', linestyle='--', linewidth=2,
        label=f"Flat Equal Share ({df_sorted['Traditional_Equal_BDT'].iloc[0]:,.0f} BDT)"
    )

    ax2.set_xlabel('Victims (sorted by vulnerability score, low→high)', fontsize=11)
    ax2.set_ylabel('Allocated Fund (BDT)', fontsize=11)
    ax2.set_title('Fund Allocation vs Flat Distribution', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')

    # Add Gini text box
    textstr = f'Block-Relief Gini: {gini_br:.4f}\nFlat Gini: {gini_flat:.4f}\nCorrelation (score↔fund): {corr:.4f}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.6)
    ax2.text(0.02, 0.97, textstr, transform=ax2.transAxes, fontsize=9,
             verticalalignment='top', bbox=props)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches='tight')
    print(f"\nLorenz curve saved -> '{OUTPUT_PNG}'")
    print("  [SUCCESS] Use this image directly in your thesis chapter.")
    plt.close()

    # ---- Final verdict ----
    print("\n" + "=" * 60)
    print("FAIRNESS VERDICT")
    print("=" * 60)
    print(f"  Block-Relief Gini:   {gini_br:.4f}  (need-based, intentional)")
    print(f"  Flat Equal Gini:     {gini_flat:.4f}  (no discrimination)")
    print(f"  Score-Fund Corr:     {corr:.4f}  (target: > 0.90)")
    if corr > 0.90:
        print("  [SUCCESS] High correlation confirms Fuzzy AHP weights work correctly.")
    else:
        print("  [WARNING] Low correlation - check weight calculation in fuzzy_ahp.py.")

    # ---- Trigger outcome report generation ----
    try:
        import generate_outcome_report
        generate_outcome_report.generate_report()
    except Exception as e:
        print(f"Warning: Could not auto-generate demographic outcome report: {e}")


if __name__ == "__main__":
    config.DATA_DIR.mkdir(exist_ok=True)
    run_fairness_analysis()