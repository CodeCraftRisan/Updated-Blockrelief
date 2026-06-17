# Block-Relief Project Improvement Roadmap for Paper Publication

**Project:** Blockchain Based Flood Relief Fund Distribution  
**Paper direction:** Blockchain + Fuzzy AHP based transparent flood relief fund distribution  
**Current stage:** Functional prototype / academic demo  
**Target stage:** Reproducible, testable, security-reviewed research artifact

---

## 1. Executive Summary

The current project already has a strong foundation for a paper because it combines three meaningful components:

1. **Victim verification** using a National ID style dataset.
2. **Fuzzy AHP-based vulnerability scoring** for prioritizing flood victims.
3. **Blockchain-based fund distribution** for transparency and auditability.

However, the project should be improved before paper submission. The current version is suitable for a course/demo prototype, but reviewers may question its security, reproducibility, privacy, and experimental validity if the code is submitted as-is.

The most important improvements are:

- Remove hardcoded private keys, phone numbers, local IP addresses, and salts.
- Fix smart contract payout failure handling.
- Add duplicate beneficiary protection on-chain.
- Align the off-chain Python allocation amount with the on-chain smart contract payout logic.
- Add automated tests for smart contract and backend scripts.
- Rerun Slither correctly and include a clean final security report.
- Add reproducibility files such as `requirements.txt`, `.env.example`, and a clear run guide.
- Add research-level experiments such as sensitivity analysis, baseline comparison, scalability testing, and gas cost analysis.

---

## 2. Current Strengths of the Project

The project should not be discarded. It has several publishable strengths:

| Area | Strength |
|---|---|
| Problem relevance | Flood relief fund distribution is a socially important and practical use case. |
| Decision model | Fuzzy AHP is appropriate for multi-criteria vulnerability scoring. |
| Transparency | Blockchain records donations, victim registration, and fund release events. |
| Fairness analysis | The project already includes Gini coefficient and Lorenz curve analysis. |
| End-to-end workflow | The pipeline covers verification, scoring, allocation, blockchain registration, distribution, receipt generation, and SMS logging. |
| Prototype value | The project can be presented as a complete proof-of-concept system. |

For a paper, the project should be positioned as a **prototype framework**, not as a production-ready disaster relief system.

Recommended wording:

> This study presents a prototype framework for transparent and priority-aware flood relief fund distribution using blockchain and Fuzzy AHP. The system is evaluated using synthetic flood-relief datasets inspired by disaster-prone regions.

Avoid wording like:

> This system is ready for real-world national relief fund deployment.

---

## 3. Priority Classification

The improvements can be divided into four levels.

| Priority | Meaning | Examples |
|---|---|---|
| Critical | Must be fixed before paper/code submission | Hardcoded private key, payout failure bug, missing tests |
| High | Strongly recommended for publication quality | Duplicate prevention, clean Slither report, reproducibility files |
| Medium | Improves research quality | Sensitivity analysis, baseline comparison, better visualizations |
| Low | Improves presentation and maintainability | README polishing, folder cleanup, better comments |

---

# Part A: Critical Code Improvements

---

## 4. Remove Hardcoded Secrets and Personal Information

### Current Issue

The current `Backend/config.py` contains hardcoded sensitive values such as:

```python
GANACHE_URL = "http://127.0.0.1:7545"
CONTRACT_ADDRESS = "0x..."
ADMIN_PRIVATE_KEY = "0x..."
ADMIN_ADDRESS = "0x..."
SMS_GATEWAY_URL = "http://192.168.x.x:8080"
SMS_TEST_WHITELIST = ["+880..."]
HASH_SALT = "BlockRelief2026"
```

This is risky and unprofessional for a paper artifact because:

- Private keys should never be committed to a repository.
- Phone numbers are personal data.
- Local IP addresses make the code non-reproducible on another machine.
- A static identity hash salt can weaken privacy.

### Required Improvement

Move all secrets and environment-specific values into a `.env` file.

Example `.env`:

```env
GANACHE_URL=http://127.0.0.1:7545
CHAIN_ID=1337
CONTRACT_ADDRESS=0xYourContractAddressHere
ADMIN_PRIVATE_KEY=0xYourPrivateKeyHere
ADMIN_ADDRESS=0xYourAdminAddressHere
SMS_GATEWAY_URL=http://127.0.0.1:8080
SMS_GATEWAY_ENABLED=false
HASH_SECRET=replace_with_random_secret
ETH_TO_BDT_RATE=100000
```

Create `.env.example` for public sharing:

```env
GANACHE_URL=http://127.0.0.1:7545
CHAIN_ID=1337
CONTRACT_ADDRESS=
ADMIN_PRIVATE_KEY=
ADMIN_ADDRESS=
SMS_GATEWAY_URL=
SMS_GATEWAY_ENABLED=false
HASH_SECRET=
ETH_TO_BDT_RATE=100000
```

Update `config.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONTRACT_DIR = BASE_DIR / "contracts"

GANACHE_URL = os.getenv("GANACHE_URL", "http://127.0.0.1:7545")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1337"))
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY", "")
ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS", "")
SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "")
SMS_GATEWAY_ENABLED = os.getenv("SMS_GATEWAY_ENABLED", "false").lower() == "true"
HASH_SECRET = os.getenv("HASH_SECRET", "")
ETH_TO_BDT_RATE = float(os.getenv("ETH_TO_BDT_RATE", "100000"))
BDT_TO_ETH = 1 / ETH_TO_BDT_RATE
```

### Also Add `.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/

# Environment files
.env
.env.local

# Generated reports and logs
*.log
data/receipts/
data/event_listener_state.json

# OS/editor files
.DS_Store
.vscode/
```

### Paper Benefit

This improvement allows you to claim:

> Sensitive deployment parameters were externalized using environment variables to support safe configuration and reproducible deployment.

---

## 5. Remove `.venv` From Repository or ZIP

### Current Issue

The uploaded zip includes a full `.venv` directory. This makes the project very large and unsuitable for GitHub or paper artifact submission.

Problems:

- It increases file size unnecessarily.
- It may contain platform-specific binaries.
- It makes the project hard to reproduce on other machines.
- Reviewers expect dependency files, not an entire virtual environment.

### Required Improvement

Delete `.venv` from the project folder before submitting.

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force .venv
```

Linux/macOS/Git Bash:

```bash
rm -rf .venv
```

Then create `requirements.txt`:

```txt
pandas
numpy
matplotlib
flask
flask-cors
web3
python-dotenv
eth-account
```

If you use Slither locally:

```txt
slither-analyzer
solc-select
```

Then users can reproduce the environment using:

```bash
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# or
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### Paper Benefit

This makes the codebase much more acceptable as a reproducible research artifact.

---

## 6. Fix Smart Contract Payout Failure Handling

### Current Issue

In the current `FloodRelief.sol`, victim payout state is updated before the ETH transfer:

```solidity
v.reliefAmount = share;
v.isPaid = true;
totalDistributed += share;
batchPaid += share;

(bool ok, ) = payable(v.walletAddress).call{value: share}("");
if (ok) {
    emit FundReleased(i, share, v.walletAddress);
}
```

This follows the Checks-Effects-Interactions pattern, which is good for reentrancy protection. However, there is a serious logical problem:

> If the ETH transfer fails, the victim is still marked as paid.

That means:

- `isPaid = true`, even if the victim did not receive money.
- `totalDistributed` increases, even if the money stayed in the contract.
- The system may show false successful distribution.
- A reviewer can criticize this as an accounting inconsistency.

### Option 1: Revert on Failed Transfer

The simplest fix is to require the transfer to succeed.

```solidity
(bool ok, ) = payable(v.walletAddress).call{value: share}("");
require(ok, "Payment failed");

v.reliefAmount = share;
v.isPaid = true;
totalDistributed += share;
batchPaid += share;

emit FundReleased(i, share, v.walletAddress);
```

However, this reintroduces the external call before state updates. To keep safety, use a reentrancy guard and ensure the function cannot be exploited.

### Option 2: Use Pull Payment Model — Recommended

A better academic design is to avoid sending ETH inside a loop. Instead:

1. Admin finalizes allocation.
2. The contract stores each victim's claimable amount.
3. Victims call `claimRelief()` themselves.
4. The claim function marks the victim as paid only after successful transfer.

Example:

```solidity
mapping(uint256 => uint256) public claimableAmount;

function finalizeAllocation(uint256 victimId, uint256 amount) external onlyAdmin {
    require(victims[victimId].isRegistered, "Not registered");
    require(claimableAmount[victimId] == 0, "Already allocated");
    claimableAmount[victimId] = amount;
}

function claimRelief(uint256 victimId) external noReentrant {
    Victim storage v = victims[victimId];
    require(v.walletAddress == msg.sender, "Only victim wallet");
    require(!v.isPaid, "Already paid");

    uint256 amount = claimableAmount[victimId];
    require(amount > 0, "No claimable amount");

    v.isPaid = true;
    v.reliefAmount = amount;
    claimableAmount[victimId] = 0;

    (bool ok, ) = payable(msg.sender).call{value: amount}("");
    require(ok, "Claim transfer failed");

    emit FundReleased(victimId, amount, msg.sender);
}
```

### Why Pull Payment Is Better

| Issue | Push payment loop | Pull payment model |
|---|---|---|
| Gas limit risk | High for many victims | Lower |
| One failed wallet blocks system | Possible | No |
| Accounting clarity | Weaker | Stronger |
| Scalability | Limited | Better |
| Reviewer confidence | Medium | High |

### Paper Benefit

You can state:

> The improved contract adopts a pull-based claim model to avoid failed batch transfers and improve payout accountability.

---

## 7. Add Duplicate Victim Protection On-Chain

### Current Issue

The off-chain Python verification step removes fake or invalid entries. However, the smart contract does not prevent duplicate identity hashes from being registered.

Current logic:

```solidity
victimCount += 1;
victims[victimCount] = Victim(...);
```

If the admin script accidentally submits the same victim twice, the contract will accept it.

### Required Improvement

Add a mapping:

```solidity
mapping(bytes32 => bool) public registeredIdentity;
```

Update `registerVictim()`:

```solidity
function registerVictim(
    bytes32 identityHash,
    uint256 score,
    address wallet
) external onlyAdmin {
    require(!isDistributed, "Distribution already done");
    require(score > 0, "Score must be > 0");
    require(wallet != address(0), "Invalid wallet");
    require(!registeredIdentity[identityHash], "Duplicate victim");

    registeredIdentity[identityHash] = true;

    victimCount += 1;
    victims[victimCount] = Victim({
        id: victimCount,
        identityHash: identityHash,
        score: score,
        reliefAmount: 0,
        walletAddress: wallet,
        isRegistered: true,
        isPaid: false
    });

    totalScore += score;
    emit VictimRegistered(victimCount, identityHash, score, wallet);
}
```

### Backend Improvement

Also check duplicates before blockchain registration:

```python
df = pd.read_csv(config.ALLOCATION_CSV)
if df["NID"].duplicated().any():
    raise ValueError("Duplicate NID found before registration")
```

### Paper Benefit

This supports an anti-fraud claim:

> Duplicate beneficiary registration is prevented both during off-chain verification and on-chain registration through identity hash tracking.

---

## 8. Align Off-Chain Allocation With On-Chain Distribution

### Current Issue

The Python script calculates final allocation amounts:

```python
Allocated_Fund_BDT
Allocated_Fund_ETH
```

But the smart contract does not use these exact values. Instead, the contract recalculates payout using only scores:

```solidity
uint256 share = (victimPool * v.score) / totalScore;
```

This means the Python cap/floor allocation logic is not fully enforced on-chain.

Example problem:

- Python may apply minimum relief floor of 2,000 BDT.
- Python may apply maximum cap of 25,000 BDT.
- Smart contract ignores those cap/floor results.
- The actual blockchain distribution may differ from the reported allocation file.

This is a major research consistency issue.

### Option 1: Store Final Allocation Amount On-Chain

Modify the victim struct:

```solidity
struct Victim {
    uint256 id;
    bytes32 identityHash;
    uint256 score;
    uint256 allocatedAmount;
    uint256 reliefAmount;
    address walletAddress;
    bool isRegistered;
    bool isPaid;
}
```

Modify registration:

```solidity
function registerVictim(
    bytes32 identityHash,
    uint256 score,
    uint256 allocatedAmount,
    address wallet
) external onlyAdmin {
    require(allocatedAmount > 0, "Amount must be > 0");
    ...
}
```

Then distribution uses:

```solidity
uint256 share = v.allocatedAmount;
```

### Option 2: Merkle Root Allocation — Stronger Research Design

For a more scalable paper contribution:

1. Python generates final allocation table.
2. Create a Merkle tree from `(victimId, wallet, amount)`.
3. Store only the Merkle root on-chain.
4. Victims claim funds using Merkle proof.

Advantages:

- Lower storage cost.
- Stronger scalability.
- Common in blockchain distribution systems.
- Good for publication.

### Recommended Direction

For your current timeline, use **Option 1** because it is easier to implement and explain.

For a stronger paper, mention Merkle root distribution as future work.

### Paper Benefit

This improvement ensures that the system's reported allocation and actual blockchain payout are consistent.

---

## 9. Fix Currency Conversion Inconsistency

### Current Issue

`config.py` defines:

```python
ETH_TO_BDT_RATE = 100000
```

But `allocate_funds.py` uses:

```python
bdt_to_eth = getattr(config, 'BDT_TO_ETH', 0.0000085)
```

If `1 ETH = 100000 BDT`, then:

```python
BDT_TO_ETH = 1 / 100000 = 0.00001
```

But the fallback value is:

```python
0.0000085
```

That means the BDT-to-ETH calculation may not match the declared exchange rate.

### Required Improvement

Add this to `config.py`:

```python
ETH_TO_BDT_RATE = float(os.getenv("ETH_TO_BDT_RATE", "100000"))
BDT_TO_ETH = 1 / ETH_TO_BDT_RATE
```

Update `allocate_funds.py`:

```python
bdt_to_eth = config.BDT_TO_ETH
scored_df['Allocated_Fund_ETH'] = (
    scored_df['Allocated_Fund_BDT'] * bdt_to_eth
).round(8)
```

### Paper Benefit

This prevents reviewers from finding inconsistent monetary calculations.

---

# Part B: Backend and API Improvements

---

## 10. Fix Flask API Debug Mode

### Current Issue

The API runs with:

```python
app.run(debug=True, port=5000)
```

Debug mode should not be enabled in a public or paper demonstration environment because it may expose internal details during errors.

### Required Improvement

Use:

```python
if __name__ == "__main__":
    app.run(debug=False, port=5000)
```

Or use an environment variable:

```python
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
app.run(debug=DEBUG_MODE, port=5000)
```

### Paper Benefit

This improves basic security hygiene.

---

## 11. Improve API Error Handling

### Current Issue

Some API routes may fail if files are missing or columns are absent. For a paper demo, the API should return clean JSON errors instead of crashing.

### Required Improvement

Add a helper function:

```python
def load_csv_safely(path, required_columns=None):
    if not Path(path).exists():
        return None, {"error": f"Missing file: {path}"}

    df = pd.read_csv(path)

    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return None, {"error": f"Missing columns: {missing}"}

    return df, None
```

Then use it in each route:

```python
@app.route("/api/allocation")
def allocation():
    df, error = load_csv_safely(config.ALLOCATION_CSV, ["Victim_ID", "Allocated_Fund_BDT"])
    if error:
        return jsonify(error), 400
    return jsonify(df.to_dict(orient="records"))
```

### Paper Benefit

This makes the demo more reliable during presentation or review.

---

## 12. Add Script-Level Logging

### Current Issue

Most scripts use `print()` statements. For a reproducible research artifact, logs should be saved to files.

### Required Improvement

Use Python logging:

```python
import logging

logging.basicConfig(
    filename="data/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Verification started")
logging.info("Verified victims: %s", len(verified_df))
```

### Paper Benefit

This makes the experiment traceable.

---

## 13. Create a Single End-to-End Pipeline Script

### Current Issue

The project has many separate scripts:

- `generate_datasets.py`
- `verify_victim.py`
- `fuzzy_ahp.py`
- `allocate_funds.py`
- `register_victims.py`
- `fairness_analysis.py`
- `generate_outcome_report.py`

This is good modularity, but reviewers need a simple way to reproduce the full pipeline.

### Required Improvement

Create `run_pipeline.py`:

```python
from Backend.generate_datasets import main as generate_datasets
from Backend.verify_victim import main as verify_victims
from Backend.fuzzy_ahp import main as run_fuzzy_ahp
from Backend.allocate_funds import allocate_proportional_funds
from Backend.fairness_analysis import main as fairness_analysis
from Backend.generate_outcome_report import main as generate_report


def main():
    generate_datasets()
    verify_victims()
    run_fuzzy_ahp()
    allocate_proportional_funds()
    fairness_analysis()
    generate_report()


if __name__ == "__main__":
    main()
```

Then document:

```bash
python run_pipeline.py
```

### Paper Benefit

This makes the system reproducible with one command.

---

# Part C: Smart Contract Research Improvements

---

## 14. Add Smart Contract Tests

### Current Issue

The project does not include automated smart contract tests. For a blockchain paper, this is a serious weakness.

### Required Test Cases

| Test Case | Expected Result |
|---|---|
| Admin can register victim | Success |
| Non-admin cannot register victim | Revert |
| Duplicate identity hash is rejected | Revert |
| Donation with zero ETH is rejected | Revert |
| Valid donation is recorded | Donor amount and totalDonated increase |
| Distribution cannot happen before target fund | Revert |
| Distribution pays correct allocated amount | Victim receives correct ETH |
| Failed payout does not mark victim as paid | Revert or remains unpaid |
| Reserve withdrawal only admin | Non-admin reverts |
| Batch distribution continues in order | `fromIndex` must match `lastDistributedId` |

### Example Hardhat Test Structure

Create:

```text
contracts/FloodRelief.sol
test/FloodRelief.test.js
hardhat.config.js
package.json
```

Example test:

```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FloodRelief", function () {
  let contract, admin, victim1, nonAdmin;

  beforeEach(async function () {
    [admin, victim1, nonAdmin] = await ethers.getSigners();
    const FloodRelief = await ethers.getContractFactory("FloodRelief");
    contract = await FloodRelief.deploy(ethers.parseEther("1"));
  });

  it("allows admin to register a victim", async function () {
    const hash = ethers.keccak256(ethers.toUtf8Bytes("victim-1"));
    await contract.registerVictim(hash, 9000, victim1.address);
    expect(await contract.victimCount()).to.equal(1);
  });

  it("rejects non-admin victim registration", async function () {
    const hash = ethers.keccak256(ethers.toUtf8Bytes("victim-1"));
    await expect(
      contract.connect(nonAdmin).registerVictim(hash, 9000, victim1.address)
    ).to.be.revertedWith("Only admin");
  });
});
```

### Paper Benefit

You can report:

> The smart contract was validated using unit tests covering access control, donation tracking, victim registration, duplicate prevention, and payout correctness.

---

## 15. Add Security Analysis With Clean Slither Output

### Current Issue

The existing Slither report files are not clean final evidence:

- One report contains command/encoding errors.
- Another appears to refer to older contract logic with lottery-related functions.
- The current contract file no longer contains those lottery functions.

### Required Improvement

Run Slither cleanly from the project root.

Recommended setup:

```bash
pip install slither-analyzer solc-select
solc-select install 0.8.20
solc-select use 0.8.20
slither contracts/FloodRelief.sol --json data/slither_report_final.json
slither contracts/FloodRelief.sol > data/slither_report_final.txt
```

If using Windows and PowerShell causes encoding issues, run through Git Bash or WSL.

### What to Include in Paper

Include a table:

| Tool | Purpose | Result |
|---|---|---|
| Slither | Static vulnerability detection | No high severity issue after fixes |
| Manual review | Business logic validation | Payout accounting issue fixed |
| Unit tests | Functional correctness | All tests passed |

Do not claim:

> Slither proves the contract is completely secure.

Better claim:

> Static analysis using Slither did not identify high-severity vulnerabilities after the implemented fixes; however, formal verification remains future work.

---

## 16. Add Gas Cost and Scalability Analysis

### Current Issue

The system has some cost analysis files, but for a paper, the gas analysis should be structured and repeatable.

### Required Experiments

Measure gas for:

| Operation | Victim Count |
|---|---|
| Contract deployment | N/A |
| Victim registration | 1, 10, 50, 100, 500 |
| Donation | 1 donor, repeated donor |
| Batch distribution | 10, 25, 50 victims per batch |
| Reserve withdrawal | N/A |

### Example Table for Paper

| Function | Avg Gas Used | ETH Cost at X gwei | BDT Equivalent |
|---|---:|---:|---:|
| donate() | TBD | TBD | TBD |
| registerVictim() | TBD | TBD | TBD |
| distributeBatch(10) | TBD | TBD | TBD |
| withdrawReserve() | TBD | TBD | TBD |

### Paper Benefit

This helps answer:

- Is the system scalable?
- How expensive is transparent blockchain-based relief distribution?
- What batch size is practical?

---

# Part D: Privacy and Data Protection Improvements

---

## 17. Improve Identity Hashing

### Current Issue

The current design uses a hash like:

```python
SHA256(NID + name + static_salt)
```

This is better than storing raw NID on-chain, but it is still weak if:

- The salt is known.
- The NID range is predictable.
- The victim name is known or guessable.
- The same salt is reused for all victims.

### Recommended Improvement

Use HMAC instead of plain SHA-256:

```python
import hmac
import hashlib


def generate_identity_hash(nid, name, secret_key):
    message = f"{nid}|{name}".encode("utf-8")
    return hmac.new(
        secret_key.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
```

### Why HMAC Is Better

| Method | Weakness |
|---|---|
| SHA256(NID + name + salt) | If salt leaks, brute force is easier |
| HMAC(secret, NID + name) | Requires secret key to reproduce hash |

### Data Minimization

For public release, remove or anonymize:

- Real phone numbers.
- Real NIDs.
- Real names.
- Local IP addresses.
- Any real wallet private key.

Use synthetic examples only.

### Paper Benefit

You can state:

> Personally identifiable information is not stored on-chain. A keyed HMAC is used to generate pseudonymous identity commitments for duplicate prevention and auditability.

---

## 18. Add Ethical and Privacy Limitation Section

Because the project deals with disaster victims, the paper should include a short ethics section.

Suggested points:

- The current dataset is synthetic.
- No real victim data was used.
- On-chain data is permanent, so raw identity data must never be stored on-chain.
- Future deployment would require government/NGO approval, consent, and secure off-chain identity management.
- SMS notifications should be opt-in and privacy-preserving.

Suggested paragraph:

> Since disaster relief data may include sensitive socioeconomic and identity information, the proposed framework avoids storing raw personal data on-chain. The experimental evaluation uses synthetic data only. In real deployments, beneficiary identity verification should be handled by authorized institutions, and only privacy-preserving identity commitments should be stored on the blockchain.

---

# Part E: Fund Allocation and Fuzzy AHP Improvements

---

## 19. Improve Fuzzy AHP Methodology Explanation

### Current Strength

The use of Fuzzy AHP is a good research contribution because flood relief priority depends on multiple uncertain criteria.

Possible criteria include:

- Water depth.
- House damage.
- Poverty index.
- Number of family members.
- Elderly/children/dependent count.
- Disability or medical vulnerability.
- Distance from shelter.
- Income disruption.

### Required Paper Improvements

The paper should clearly explain:

1. Why Fuzzy AHP was chosen instead of normal AHP.
2. What criteria were used.
3. How pairwise comparisons were collected or simulated.
4. How fuzzy triangular numbers were assigned.
5. How fuzzy weights were defuzzified.
6. How final vulnerability score was calculated.

### Suggested Method Section Structure

```text
3.1 Beneficiary Verification
3.2 Vulnerability Criteria Selection
3.3 Fuzzy AHP Weight Calculation
3.4 Score Normalization
3.5 Fund Allocation With Floor and Cap Constraints
3.6 Blockchain Registration and Distribution
3.7 Fairness and Transparency Evaluation
```

### Paper Benefit

This helps reviewers understand the decision model instead of seeing it as a black box.

---

## 20. Add Sensitivity Analysis

### Current Issue

The project calculates Fuzzy AHP weights and uses them directly. But a paper should show whether the results are stable if weights change.

### Required Experiment

Run allocation under different weight scenarios:

| Scenario | Description |
|---|---|
| Original Fuzzy AHP | Current weights |
| Equal weight baseline | All criteria have same weight |
| Poverty priority +10% | Increase poverty weight |
| Water depth priority +10% | Increase flood severity weight |
| Housing damage priority +10% | Increase physical damage weight |
| Random perturbation | Add small noise to all weights |

### Metrics to Compare

| Metric | Purpose |
|---|---|
| Gini coefficient | Measures allocation inequality |
| Top-10 recipient overlap | Checks stability of most vulnerable selection |
| Spearman rank correlation | Checks score ranking stability |
| Mean allocation difference | Checks payout variation |
| Maximum allocation difference | Finds sensitive cases |

### Example Output Table

| Scenario | Gini | Top-10 Overlap | Spearman Correlation | Total Allocated |
|---|---:|---:|---:|---:|
| Original | 0.1199 | 100% | 1.000 | 999,999 BDT |
| Equal Weight | TBD | TBD | TBD | TBD |
| Poverty +10% | TBD | TBD | TBD | TBD |
| Water Depth +10% | TBD | TBD | TBD | TBD |

### Paper Benefit

Sensitivity analysis is one of the most important improvements for publishability because it shows that the method is not arbitrary.

---

## 21. Add Baseline Comparison

### Current Issue

The project compares dynamic allocation against equal allocation, but the paper can be stronger with more baselines.

### Recommended Baselines

| Baseline | Description |
|---|---|
| Equal distribution | Every verified victim gets equal amount |
| Poverty-only distribution | Allocation based only on poverty index |
| Flood-depth-only distribution | Allocation based only on water depth |
| Simple weighted sum | Normalized criteria multiplied by manually assigned weights |
| Fuzzy AHP proposed model | Your final model |

### Metrics

| Metric | Purpose |
|---|---|
| Gini coefficient | Fairness/inequality |
| Priority alignment | Whether more vulnerable victims receive more |
| Allocation correlation with score | Consistency |
| Minimum and maximum relief | Floor/cap behavior |
| Number of victims helped | Coverage |

### Paper Benefit

This allows a stronger claim:

> Compared with equal and single-criterion baselines, the proposed Fuzzy AHP model provides priority-aware allocation while maintaining controlled inequality.

---

## 22. Improve Rounding Logic in Allocation

### Current Issue

The current allocation rounds to whole BDT:

```python
scored_df['Allocated_Fund_BDT'] = scored_df['Allocated_Fund_BDT'].round(0)
```

This can create small leftover or over-allocation due to rounding.

### Required Improvement

After rounding, adjust the final victim or distribute the rounding difference.

Example:

```python
rounded = scored_df['Allocated_Fund_BDT'].round(0).astype(int)
diff = TOTAL_FUND_POOL_BDT - rounded.sum()

# Add rounding difference to the highest-scoring victim who is not capped
idx = scored_df['Vulnerability_Score'].idxmax()
rounded.loc[idx] += diff

scored_df['Allocated_Fund_BDT'] = rounded
```

Better version:

- Add positive leftover to victims below cap.
- Remove negative excess from victims above floor.

### Paper Benefit

This ensures exact fund conservation:

```text
Total allocated = Total available fund
```

---

# Part F: Reproducibility Improvements

---

## 23. Add a Professional README

Create a `README.md` with:

```text
# Block-Relief

## Overview
## System Architecture
## Dataset Description
## Installation
## Environment Variables
## Running the Pipeline
## Running the Flask Dashboard
## Deploying Smart Contract Locally
## Running Tests
## Reproducing Paper Results
## Limitations
```

### Example Installation Section

```bash
git clone <repo-url>
cd block-relief
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run_pipeline.py
```

### Paper Benefit

A clear README makes the work easier to review and reproduce.

---

## 24. Add `requirements.txt` or `environment.yml`

### Required File

`requirements.txt`:

```txt
pandas
numpy
matplotlib
flask
flask-cors
web3
python-dotenv
eth-account
pytest
```

Optional:

```txt
slither-analyzer
```

### Why This Matters

A reviewer should not need your local machine setup to run the code.

---

## 25. Add Dataset Documentation

Create `data/README.md`:

```text
# Dataset Description

This folder contains synthetic data used for evaluating the Block-Relief prototype.

## Files

- National_ID_Database.csv: synthetic baseline identity database
- volunteer_input.csv: victim applications submitted by volunteers
- verified_victims.csv: verified victims after NID matching
- rejected_entries.csv: rejected or fake entries
- scored_victims.csv: victims with vulnerability scores
- fund_allocation.csv: final relief allocation table
- fairness_analysis_results.csv: fairness metrics

## Privacy Note

All records are synthetic. No real victim identity data is included.
```

### Paper Benefit

This makes it clear that the dataset is synthetic and ethically safer.

---

## 26. Add a Reproducibility Checklist

Include this checklist in the repository:

```markdown
# Reproducibility Checklist

- [ ] `.venv` is not included in repository.
- [ ] `.env.example` is included.
- [ ] `.env` is ignored by Git.
- [ ] `requirements.txt` is included.
- [ ] One-command pipeline is available.
- [ ] Smart contract tests are included.
- [ ] Final Slither report is included.
- [ ] Generated figures are reproducible.
- [ ] Dataset is documented.
- [ ] Random seeds are fixed for synthetic data generation.
```

---

# Part G: Paper-Level Improvements

---

## 27. Add a Clear Threat Model

A blockchain paper should explain what threats the system handles and what it does not handle.

### Threats Addressed

| Threat | How It Is Addressed |
|---|---|
| Fake victim entry | NID verification and duplicate hash check |
| Duplicate beneficiary | On-chain identity hash mapping |
| Donation opacity | Public blockchain donation events |
| Fund misallocation | Transparent allocation and event logs |
| Manual favoritism | Fuzzy AHP score-based allocation |
| Post-distribution audit difficulty | Blockchain event logs and receipts |

### Threats Not Fully Addressed

| Threat | Limitation |
|---|---|
| Incorrect real-world survey data | Requires trusted field verification |
| Compromised admin private key | Needs multisig or DAO governance |
| Privacy leakage from metadata | Requires stronger privacy design |
| Blockchain transaction cost | Needs L2 or permissioned blockchain for scale |
| Oracle problem | Off-chain data must still be trusted |

### Paper Benefit

This makes the paper more honest and credible.

---

## 28. Add Governance Improvement: Multi-Signature Admin

### Current Issue

The contract uses one admin address:

```solidity
address public immutable admin;
```

This is simple, but it creates a single point of failure.

### Recommended Improvement

For real deployment, use multi-signature governance:

- NGO representative.
- Local government representative.
- Auditor.
- Disaster management authority.

For the paper, you can mention this as future work, or implement it using a multisig wallet such as Safe.

### Paper Benefit

You can write:

> The current prototype uses a single administrator for simplicity; future deployment should replace this with a multi-signature governance model.

---

## 29. Improve Claims About Blockchain

Avoid overclaiming. Blockchain does not automatically guarantee fair distribution. It guarantees tamper-evident record keeping after data is submitted.

Use careful wording:

Good claim:

> Blockchain improves transparency and auditability of donation and distribution records.

Avoid:

> Blockchain completely removes corruption from relief distribution.

Good claim:

> Fuzzy AHP supports systematic prioritization based on selected vulnerability criteria.

Avoid:

> Fuzzy AHP guarantees perfect fairness.

---

## 30. Add Limitations Section

A strong paper should openly state limitations.

Recommended limitations:

1. The dataset is synthetic and does not represent all real-world flood relief conditions.
2. Identity verification depends on trusted off-chain government or NGO databases.
3. The prototype uses a local blockchain/Ganache environment.
4. Real blockchain deployment may introduce gas cost and scalability constraints.
5. The current system uses a centralized admin role.
6. Privacy can be improved using stronger cryptographic approaches such as zero-knowledge proofs.
7. SMS notification reliability depends on external gateway availability.

Suggested paragraph:

> Although the proposed framework improves transparency and priority-aware allocation, it relies on trusted off-chain data sources for identity verification and damage assessment. The evaluation uses synthetic data and a local blockchain environment; therefore, large-scale deployment would require further testing with real institutional workflows, privacy-preserving identity management, and cost-optimized blockchain infrastructure.

---

# Part H: Suggested Final Repository Structure

A cleaner project structure should look like this:

```text
block-relief/
├── Backend/
│   ├── allocate_funds.py
│   ├── config.py
│   ├── fairness_analysis.py
│   ├── fuzzy_ahp.py
│   ├── generate_datasets.py
│   ├── generate_outcome_report.py
│   ├── register_victims.py
│   ├── verify_victim.py
│   └── utils/
│       ├── hashing.py
│       ├── logging_utils.py
│       └── validation.py
│
├── contracts/
│   ├── FloodRelief.sol
│   └── FloodRelief_abi.json
│
├── data/
│   ├── README.md
│   ├── National_ID_Database.csv
│   ├── volunteer_input.csv
│   ├── verified_victims.csv
│   ├── scored_victims.csv
│   └── fund_allocation.csv
│
├── frontend/
│   ├── api_server.py
│   └── index.html
│
├── tests/
│   ├── test_allocation.py
│   ├── test_verification.py
│   └── FloodRelief.test.js
│
├── reports/
│   ├── slither_report_final.txt
│   ├── gas_cost_analysis.csv
│   └── fairness_report.md
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run_pipeline.py
└── hardhat.config.js
```

---

# Part I: Recommended Implementation Roadmap

---

## Phase 1: Must-Fix Code Cleanup

Complete these first:

- [ ] Delete `.venv` from repository/zip.
- [ ] Add `.gitignore`.
- [ ] Add `.env.example`.
- [ ] Move private key and phone numbers out of `config.py`.
- [ ] Fix ETH-to-BDT conversion.
- [ ] Turn off Flask debug mode.
- [ ] Add `requirements.txt`.

Estimated result: project becomes safer and cleaner for GitHub.

---

## Phase 2: Smart Contract Correctness

Complete these before paper submission:

- [ ] Add duplicate identity hash mapping.
- [ ] Fix payout failure handling.
- [ ] Align on-chain payout with off-chain allocation.
- [ ] Add smart contract unit tests.
- [ ] Rerun Slither and save clean final report.

Estimated result: project becomes defensible as a blockchain research prototype.

---

## Phase 3: Research Evaluation

Complete these for a stronger paper:

- [ ] Add sensitivity analysis.
- [ ] Add equal allocation baseline.
- [ ] Add poverty-only baseline.
- [ ] Add flood-depth-only baseline.
- [ ] Add gas cost analysis for multiple victim counts.
- [ ] Add scalability discussion.
- [ ] Add privacy/ethics section.
- [ ] Add threat model.

Estimated result: paper becomes much stronger and more publishable.

---

# Part J: Minimum Acceptance Criteria Before Paper Submission

Before submitting the paper, the project should satisfy these conditions:

| Requirement | Status Needed |
|---|---|
| No hardcoded private key | Must pass |
| No real phone numbers in public repo | Must pass |
| `.venv` removed | Must pass |
| Smart contract compiles cleanly | Must pass |
| Duplicate victim registration blocked | Must pass |
| Payout failure handled correctly | Must pass |
| Python allocation equals blockchain payout logic | Must pass |
| Unit tests included | Strongly recommended |
| Slither final report included | Strongly recommended |
| Reproducible run instructions | Must pass |
| Sensitivity analysis | Strongly recommended |
| Baseline comparison | Strongly recommended |
| Limitations section | Must pass |

---

# Part K: Suggested Paper Contribution Statement

After improvements, the contribution can be written like this:

> This paper proposes Block-Relief, a prototype blockchain-based flood relief fund distribution framework that integrates beneficiary verification, Fuzzy AHP-based vulnerability scoring, and transparent smart contract-based fund allocation. The framework stores donation and distribution events on-chain to support auditability while keeping sensitive beneficiary identity data off-chain using pseudonymous identity commitments. Experimental evaluation using synthetic flood-relief data demonstrates that the proposed allocation method prioritizes high-vulnerability victims while maintaining controlled distribution inequality measured through fairness metrics such as the Gini coefficient and Lorenz curve analysis.

---

# Part L: Final Recommendation

The project is promising for a paper, but it should be improved before submission.

Current readiness:

```text
Prototype/demo readiness: 80%
Paper artifact readiness: 55–60%
Production readiness: Not ready
```

After completing Phase 1 and Phase 2:

```text
Prototype/demo readiness: 95%
Paper artifact readiness: 75–80%
Production readiness: Still not ready, but acceptable as future work
```

After completing Phase 3:

```text
Paper artifact readiness: 85–90%
```

The most important message for the paper is:

> This is a transparent and priority-aware prototype framework, not a complete real-world disaster relief deployment system.

That framing is honest, academically acceptable, and easier to defend during review.
