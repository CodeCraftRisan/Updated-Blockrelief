# Block-Relief: Blockchain-Based Flood Relief Fund Distribution

Block-Relief is a prototype framework for transparent, priority-aware flood relief fund distribution. It integrates beneficiary verification using National ID datasets, Fuzzy AHP-based vulnerability scoring, and blockchain-based fund distribution to ensure accountability and fairness.

## Key Features

- **Victim Verification:** Multi-layer anti-fraud verification against a synthetic National ID database.
- **Fuzzy AHP Scoring:** Multi-criteria decision model for prioritizing aid based on flood severity, poverty index, house type, and more.
- **Blockchain Distribution:** Smart contract-based fund release with a pull-based claim model and reserve pool management.
- **Fairness Analysis:** Built-in Gini coefficient and Lorenz curve evaluation to measure humanitarian equity.
- **Research-Ready:** Automated sensitivity analysis and baseline comparisons for academic publication.

## System Architecture

The project consists of three main components:
1. **Smart Contract:** Located in `contracts/FloodRelief.sol`. Handles donations, victim registration, and fund distribution.
2. **Backend (Python):** Located in `Backend/`. Handles data generation, verification, scoring, and analysis.
3. **Frontend (Web):** A React-based dashboard (demo in `frontend/index.html` via `api_server.py`) for administrators, donors, and recipients.

## Installation

### Prerequisites
- Python 3.8+
- Node.js & npm (for Hardhat/frontend development, optional)
- Ganache (for local blockchain testing)

### Setup
1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your parameters:
   ```bash
   cp .env.example .env
   ```

## Running the Pipeline

You can run the entire research workflow (from dataset generation to final reports) with a single command:

```bash
python run_pipeline.py
```

This will:
1. Generate synthetic datasets.
2. Verify victims against the NID database.
3. Calculate vulnerability weights and scores using Fuzzy AHP.
4. Allocate funds proportionally.
5. Perform fairness and sensitivity analysis.
6. Generate an outcome report and visualizations.

## Smart Contract Development

### Compilation
Using `solc` (0.8.20):
```bash
solc --combined-json abi,bin contracts/FloodRelief.sol > contracts/FloodRelief_compilation.json
```

### Testing
Run the Python-based test suite:
```bash
python -m pytest tests/test_flood_relief.py
```

### Security Analysis
Static analysis using Slither:
```bash
slither contracts/FloodRelief.sol
```

## Dataset Documentation

See `data/README.md` for detailed information on the synthetic datasets used in this project.

## Research Evaluation

Experimental results, including Gini coefficients, Lorenz curves, and sensitivity analysis, are saved in the `reports/` and `data/` directories after running the pipeline. These artifacts are designed to be included directly in research papers and theses.

## Limitations

- The dataset is synthetic and for academic evaluation purposes.
- Identity verification relies on a trusted off-chain database.
- The current prototype uses a single administrator role; future work includes multi-signature governance.
- Privacy is managed via off-chain hashing; further improvements could use zero-knowledge proofs.

## License
MIT
