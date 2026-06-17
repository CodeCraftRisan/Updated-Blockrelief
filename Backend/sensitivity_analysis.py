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

logger = get_logger("sensitivity_analysis")

def run_sensitivity_analysis():
    logger.info("Starting Sensitivity Analysis")

    # Load verified victims
    try:
        df = pd.read_csv(config.VERIFIED_CSV)
    except FileNotFoundError:
        logger.error("Verified victims file not found. Run pipeline first.")
        return

    # Base weights (from fuzzy_ahp.py)
    # CRITERIA_NAMES = ['Water_Depth', 'House_Type', 'Flood_Duration', 'Poverty_Index', 'Distance']
    base_weights = {
        'Water_Depth': 0.3185,
        'House_Type': 0.1270,
        'Flood_Duration': 0.1280,
        'Poverty_Index': 0.3822,
        'Distance': 0.0443
    }

    # Normalization (mirroring fuzzy_ahp.py)
    df['Norm_Depth'] = df['Water_Depth_ft'] / df['Water_Depth_ft'].max()
    df['Norm_House'] = (4.0 - df['House_Type']) / 3.0
    df['Norm_Duration'] = df['Duration_Days'] / df['Duration_Days'].max()
    df['Norm_Poverty'] = df['Poverty_Index']
    df['Norm_Distance'] = df['Distance_km'] / df['Distance_km'].max()

    def calculate_score(row, weights):
        return (
            row['Norm_Depth'] * weights['Water_Depth'] +
            row['Norm_House'] * weights['House_Type'] +
            row['Norm_Duration'] * weights['Flood_Duration'] +
            row['Norm_Poverty'] * weights['Poverty_Index'] +
            row['Norm_Distance'] * weights['Distance']
        ) * 100

    scenarios = {
        'Original Fuzzy AHP': base_weights,
        'Equal Weights': {k: 0.2 for k in base_weights},
        'Poverty Priority (+10%)': {
            'Water_Depth': 0.28, 'House_Type': 0.11, 'Flood_Duration': 0.11,
            'Poverty_Index': 0.46, 'Distance': 0.04
        },
        'Flood Severity Priority (+10%)': {
            'Water_Depth': 0.42, 'House_Type': 0.11, 'Flood_Duration': 0.11,
            'Poverty_Index': 0.32, 'Distance': 0.04
        }
    }

    results = []

    for name, weights in scenarios.items():
        # Ensure weights sum to 1
        total_w = sum(weights.values())
        weights = {k: v/total_w for k, v in weights.items()}

        df[f'Score_{name}'] = df.apply(lambda row: calculate_score(row, weights), axis=1)

        # Gini Coefficient (simplified for this script)
        scores = np.sort(df[f'Score_{name}'].values)
        n = len(scores)
        gini = (np.sum((2 * np.arange(1, n + 1) - n - 1) * scores)) / (n * np.sum(scores))

        results.append({
            'Scenario': name,
            'Gini': round(gini, 4),
            'Mean Score': round(df[f'Score_{name}'].mean(), 2),
            'Max Score': round(df[f'Score_{name}'].max(), 2)
        })

    results_df = pd.DataFrame(results)
    logger.info("\n" + results_df.to_string(index=False))

    # Save sensitivity results
    results_df.to_csv(config.REPORTS_DIR / "sensitivity_analysis.csv", index=False)

    # Plotting
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))

    for name in scenarios:
        sorted_scores = np.sort(df[f'Score_{name}'].values)
        ax.plot(np.linspace(0, 100, len(sorted_scores)), sorted_scores, label=name)

    ax.set_title("Vulnerability Score Sensitivity Analysis")
    ax.set_xlabel("Victim Percentile")
    ax.set_ylabel("Vulnerability Score")
    ax.legend()

    plt.savefig(config.REPORTS_DIR / "sensitivity_analysis.png")
    logger.info(f"Sensitivity analysis plot saved to {config.REPORTS_DIR / 'sensitivity_analysis.png'}")

if __name__ == "__main__":
    run_sensitivity_analysis()
