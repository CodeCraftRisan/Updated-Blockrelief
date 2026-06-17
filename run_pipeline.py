import sys
from pathlib import Path
import logging

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import main functions from backend scripts
from Backend.generate_datasets import generate_large_scale_datasets as generate_datasets
from Backend.verify_victim import verify_victims
from Backend.fuzzy_ahp import main as run_fuzzy_ahp
from Backend.allocate_funds import allocate_proportional_funds
from Backend.fairness_analysis import run_fairness_analysis as fairness_analysis
from Backend.generate_outcome_report import generate_report
from Backend.sensitivity_analysis import run_sensitivity_analysis
from Backend.baseline_comparison import run_baseline_comparison

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data/pipeline.log"),
        logging.StreamHandler()
    ]
)

def run_pipeline():
    logging.info("Starting Block-Relief Pipeline")

    try:
        logging.info("Step 1: Generating Datasets")
        generate_datasets()

        logging.info("Step 2: Verifying Victims")
        verify_victims()

        logging.info("Step 3: Running Fuzzy AHP")
        run_fuzzy_ahp()

        logging.info("Step 4: Allocating Funds")
        allocate_proportional_funds()

        logging.info("Step 5: Running Fairness Analysis")
        fairness_analysis()

        logging.info("Step 6: Generating Outcome Report")
        generate_report()

        logging.info("Step 7: Running Sensitivity Analysis")
        run_sensitivity_analysis()

        logging.info("Step 8: Running Baseline Comparison")
        run_baseline_comparison()

        logging.info("Pipeline completed successfully.")
    except Exception as e:
        logging.critical(f"Pipeline failed at some step: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
