import pandas as pd
import numpy as np
from scipy.stats import gmean
import os
import sys
from pathlib import Path

# Add script directory to sys.path to resolve config import from any working directory
sys.path.append(str(Path(__file__).resolve().parent))
import config
from utils.logging_utils import get_logger

logger = get_logger("fuzzy_ahp")

# --- File Paths ---
SURVEY_DATA_PATH = config.DATA_DIR / 'Fuzzy_AHP_Survey_Responses.csv'
VERIFIED_VICTIMS_PATH = config.VERIFIED_CSV
SCORED_VICTIMS_PATH = config.SCORED_CSV

# --- Criteria Configuration ---
CRITERIA_NAMES = ['Water_Depth', 'House_Type', 'Flood_Duration', 'Poverty_Index', 'Distance']
N_CRITERIA = 5
RI_TABLE = {3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32}

# Column indices for pairwise comparison answers in survey CSV
SURVEY_PAIRWISE_START_COL = 3   # fixed: Q1 starts at index 3
SURVEY_PAIRWISE_END_COL = 13    # fixed: Q10 ends at index 13 (exclusive)


def calculate_fuzzy_ahp_weights():
    """
    Calculates Fuzzy AHP weights from 50-person survey data using
    Triangular Fuzzy Numbers and geometric mean aggregation.
    """
    logger.info("=" * 60)
    logger.info("STEP 1: FUZZY AHP WEIGHT CALCULATION")
    logger.info("=" * 60)

    try:
        survey_df = pd.read_csv(SURVEY_DATA_PATH)
        logger.info(f"Survey data loaded: {len(survey_df)} respondents")
    except FileNotFoundError:
        logger.error(f"Error: Survey file not found at '{SURVEY_DATA_PATH}'")
        return None

    # Extract pairwise comparison columns
    survey_data = survey_df.iloc[:, SURVEY_PAIRWISE_START_COL:SURVEY_PAIRWISE_END_COL]

    if survey_data.shape[1] != 10:
        logger.error(f"Error: Expected 10 pairwise columns, found {survey_data.shape[1]}")
        logger.error(f"Column names found: {list(survey_data.columns)}")
        return None

    logger.info(f"Using {survey_data.shape[1]} pairwise comparison columns")

    # --- Build TFN from survey responses ---
    tfn_list = []
    for i, col in enumerate(survey_data.columns):
        values = survey_data[col].dropna()
        if len(values) == 0:
            logger.error(f"Error: Column '{col}' has no valid data")
            return None
        m = float(gmean(values))
        l = float(np.percentile(values, 25))
        u = float(np.percentile(values, 75))
        l = min(l, m)
        u = max(u, m)
        tfn_list.append((l, m, u))
        logger.info(f"  Pair {i+1}: TFN = ({l:.3f}, {m:.3f}, {u:.3f})")

    # --- Build Fuzzy Pairwise Comparison Matrix ---
    matrix = np.full((N_CRITERIA, N_CRITERIA), None, dtype=object)
    idx = 0
    for i in range(N_CRITERIA):
        for j in range(N_CRITERIA):
            if i == j:
                matrix[i, j] = (1.0, 1.0, 1.0)
            elif i < j:
                l, m, u = tfn_list[idx]
                matrix[i, j] = (l, m, u)
                # Reciprocal: avoid division by zero
                matrix[j, i] = (
                    1.0 / max(u, 0.001),
                    1.0 / max(m, 0.001),
                    1.0 / max(l, 0.001)
                )
                idx += 1

    # --- Fuzzy Geometric Mean for each criterion ---
    weights_fuzzy = []
    for i in range(N_CRITERIA):
        lower = [matrix[i, j][0] for j in range(N_CRITERIA)]
        modal = [matrix[i, j][1] for j in range(N_CRITERIA)]
        upper = [matrix[i, j][2] for j in range(N_CRITERIA)]
        weights_fuzzy.append((gmean(lower), gmean(modal), gmean(upper)))

    # --- Defuzzification and Normalization ---
    weights_crisp = np.array([(l + 4*m + u) / 6 for l, m, u in weights_fuzzy])
    weights_normalized = weights_crisp / np.sum(weights_crisp)

    # --- Consistency Ratio ---
    modal_matrix = np.zeros((N_CRITERIA, N_CRITERIA))
    for i in range(N_CRITERIA):
        for j in range(N_CRITERIA):
            modal_matrix[i, j] = matrix[i, j][1]

    eigvals = np.linalg.eigvals(modal_matrix)
    lambda_max = max(eigvals).real
    CI = (lambda_max - N_CRITERIA) / (N_CRITERIA - 1)
    CR = CI / RI_TABLE[N_CRITERIA]

    # --- Results ---
    logger.info("\n" + "=" * 60)
    logger.info("FUZZY AHP RESULTS")
    logger.info("=" * 60)

    results = pd.DataFrame({
        'Criterion': CRITERIA_NAMES,
        'Fuzzy_Weight_L': [w[0] for w in weights_fuzzy],
        'Fuzzy_Weight_M': [w[1] for w in weights_fuzzy],
        'Fuzzy_Weight_U': [w[2] for w in weights_fuzzy],
        'Crisp_Weight': weights_crisp,
        'Normalized_Weight_%': weights_normalized * 100
    }).sort_values(by='Normalized_Weight_%', ascending=False)

    logger.info("\n" + results.to_string(index=False))
    logger.info(f"\nConsistency Ratio (CR): {CR:.4f}")

    if CR < 0.10:
        logger.info("CR < 0.10: Model is CONSISTENT and VALID")
    else:
        logger.warning("WARNING: CR >= 0.10. Survey data may have inconsistencies.")

    # --- Save weights for reference ---
    results.to_csv(config.WEIGHTS_CSV, index=False)
    logger.info(f"\nWeights saved to '{config.WEIGHTS_CSV}'")

    return dict(zip(CRITERIA_NAMES, weights_normalized))


def calculate_vulnerability_scores(weights_dict):
    """
    Calculates vulnerability score for each verified victim using all 5 criteria.
    """
    if weights_dict is None:
        return

    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: VULNERABILITY SCORE CALCULATION")
    logger.info("=" * 60)

    try:
        victims_df = pd.read_csv(VERIFIED_VICTIMS_PATH)
        logger.info(f"Verified victims loaded: {len(victims_df)} records")
    except FileNotFoundError:
        logger.error(f"Error: File not found at '{VERIFIED_VICTIMS_PATH}'")
        return

    # --- Normalize all 5 factors to 0-1 scale ---
    victims_df['Norm_Depth'] = victims_df['Water_Depth_ft'] / victims_df['Water_Depth_ft'].max()
    # House type: 1 = Kutcha (most vulnerable), 2 = Semi-pucca, 3 = Pucca (least vulnerable)
    victims_df['Norm_House'] = (4.0 - victims_df['House_Type']) / 3.0
    victims_df['Norm_Duration'] = victims_df['Duration_Days'] / victims_df['Duration_Days'].max()
    victims_df['Norm_Poverty'] = victims_df['Poverty_Index']  # Already 0-1

    # Distance: higher distance = more vulnerable (harder to reach relief)
    if 'Distance_km' in victims_df.columns:
        victims_df['Norm_Distance'] = victims_df['Distance_km'] / victims_df['Distance_km'].max()
    else:
        logger.warning("Warning: Distance_km column not found. Setting Distance weight contribution to 0.")
        victims_df['Norm_Distance'] = 0

    # --- Calculate Weighted Score (0-100 scale) ---
    victims_df['Vulnerability_Score'] = (
        victims_df['Norm_Depth'] * weights_dict['Water_Depth'] +
        victims_df['Norm_House'] * weights_dict['House_Type'] +
        victims_df['Norm_Duration'] * weights_dict['Flood_Duration'] +
        victims_df['Norm_Poverty'] * weights_dict['Poverty_Index'] +
        victims_df['Norm_Distance'] * weights_dict['Distance']
    ) * 100

    victims_df['Vulnerability_Score'] = victims_df['Vulnerability_Score'].round(2)

    # --- Save ---
    victims_df.to_csv(SCORED_VICTIMS_PATH, index=False)
    logger.info(f"Scored victims saved to '{SCORED_VICTIMS_PATH}'")

    logger.info("\n--- Score Distribution ---")
    logger.info(f"Min Score:  {victims_df['Vulnerability_Score'].min()}")
    logger.info(f"Max Score:  {victims_df['Vulnerability_Score'].max()}")
    logger.info(f"Mean Score: {victims_df['Vulnerability_Score'].mean():.2f}")

    return victims_df

def main():
    weights = calculate_fuzzy_ahp_weights()
    if weights:
        calculate_vulnerability_scores(weights)

if __name__ == "__main__":
    main()
