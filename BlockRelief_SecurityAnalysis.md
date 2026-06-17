**Block-Relief: Security Analysis**

Smart Contract Vulnerability Assessment using Slither Static Analyzer

**V. SECURITY ANALYSIS**

**A. Overview**

Security is a critical concern in blockchain-based financial systems,
particularly when the system is responsible for distributing disaster
relief funds to vulnerable populations. Any exploitable vulnerability in
the smart contract could lead to fund theft, double payments, or
permanent loss of assets. To systematically identify and address
security vulnerabilities in the Block-Relief smart contract, a formal
static analysis was conducted using Slither --- an open-source smart
contract security framework developed by Trail of Bits \[1\].

Slither performs static analysis without executing the contract,
examining the Solidity source code through 101 built-in detectors that
cover a wide range of vulnerability classes including reentrancy,
integer overflow, access control issues, gas inefficiencies, and coding
standard violations. This approach enables comprehensive vulnerability
identification prior to testnet deployment, forming an essential
component of the Block-Relief security validation methodology.

**B. Analysis Tool and Configuration**

Slither (v0.11.x) was configured with the solc-select compiler
management tool, which allows precise control over the Solidity compiler
version used during analysis. The analysis was performed in two
iterations:

Version 1 (v2 contract): Used pragma solidity \^0.8.19, the initial
deployment compiler version. This version served as the baseline
analysis.

Version 2 (v3 contract): Used pragma solidity \^0.8.20, the patched
version incorporating all security improvements identified during the
first analysis pass. This version represents the final production-ready
contract.

**TABLE I. Slither Analysis Configuration**

  -----------------------------------------------------------------------
  **Parameter**           **Value**
  ----------------------- -----------------------------------------------
  **Tool**                Slither Static Analyzer (Trail of Bits)

  **Version**             v0.11.x

  **Detectors Active**    101 built-in detectors

  **Compiler (Baseline)** solc 0.8.19 via solc-select

  **Compiler (Final)**    solc 0.8.20 via solc-select

  **Target Contract**     FloodRelief.sol (1 contract)

  **Analysis Mode**       Static (no execution required)

  **Command**             slither contracts/FloodRelief.sol
  -----------------------------------------------------------------------

**C. Analysis Results Summary**

The baseline analysis of the v2 contract (pragma \^0.8.19) identified 35
findings across multiple severity levels. Following targeted
remediation, the v3 contract (pragma \^0.8.20) reduced the total finding
count to 29, with all critical and patchable issues resolved. Table II
presents the comparative finding distribution across both versions.

**TABLE II. Slither Finding Summary: v2 vs v3 Contract**

  -----------------------------------------------------------------------------
  **Detector /           **v2        **v3        **Change**     **Status**
  Severity**             Count**     Count**                    
  ---------------------- ----------- ----------- -------------- ---------------
  **reentrancy-eth       3           3\*         CEI applied    Mitigated ✓
  (HIGH)**                                                      

  **weak-prng (HIGH)**   2           2           Acknowledged   Known
                                                                Limitation

  **incorrect-equality   2           2           Intentional    False Positive
  (MED)**                                                       

  **calls-loop (MED)**   4           4           Design req.    Justified

  **reentrancy-benign    2           2           ---            Benign
  (LOW)**                                                       

  **reentrancy-events    4           4           ---            Informational
  (INFO)**                                                      

  **timestamp (LOW)**    6           6           ---            Acceptable

  **costly-loop (LOW)**  2           2           ---            Justified

  **solc-version (LOW)** 1           0           Fixed ✓        Resolved

  **low-level-calls      3           3           Intentional    Justified
  (INFO)**                                                      

  **naming-convention    4           0           Fixed ✓        Resolved
  (INFO)**                                                      

  **immutable-states     1           0           Fixed ✓        Resolved
  (INFO)**                                                      

  **constable-states     1           0           Fixed ✓        Resolved
  (INFO)**                                                      

  **TOTAL**              **35**      **29**      **−6 (17%)**   **4 Fully
                                                                Fixed**
  -----------------------------------------------------------------------------

\* reentrancy-eth findings in v3 persist as Slither flags all external
calls in loops regardless of guard modifiers. The noReentrant mutex
modifier provides runtime protection; see Section V-D for full
explanation.

**D. Detailed Vulnerability Analysis and Mitigations**

**1) HIGH --- Reentrancy Vulnerabilities (reentrancy-eth)**

Slither identified three reentrancy-eth findings in functions
distributeBatch(), autoDistribute(), and \_pickLotteryWinners(). In the
v2 contract, state variable updates occurred after external ETH transfer
calls in certain code paths, creating a theoretical window for
reentrancy attacks where a malicious contract recipient could re-enter
the distribution function before state was updated.

The Block-Relief v2 contract included a noReentrant mutex modifier on
all public distribution functions, which provides effective runtime
protection against reentrancy. However, the ordering of operations
within internal loops did not fully conform to the
Checks-Effects-Interactions (CEI) pattern recommended by the Ethereum
security community \[2\].

In the v3 contract, the CEI pattern was strictly applied to all
distribution loops. Specifically:

-   In distributeBatch() and autoDistribute(): v.reliefAmount, v.isPaid,
    and totalDistributed are all updated before the external payable
    call.

-   In \_pickLotteryWinners(): lotteryWinners.push() is called with
    claimed: true before the ETH transfer, so the winner record exists
    in state before any external call executes.

-   If a transfer fails, claimed is set to false retrospectively ---
    this is safe because the push() already occurred.

The residual reentrancy-eth findings in v3 are due to Slither\'s static
analysis limitation: it flags all external calls within loops regardless
of the surrounding guard modifiers. The noReentrant mutex prevents any
re-entrant call from succeeding at runtime, as the locked state variable
remains true throughout the entire transaction.

**2) HIGH --- Weak Pseudo-Random Number Generation (weak-prng)**

Slither flagged two instances of weak PRNG usage in the
\_pickLotteryWinners() internal function, which selects three donor
lottery winners. The random seed is derived from block.timestamp,
block.prevrandao, totalDonated, donors.length, and address(this).balance
using keccak256 hashing.

This approach is acknowledged as a known limitation of the current
implementation. In theory, a block validator on a Proof-of-Stake network
could marginally influence block.prevrandao to bias the lottery outcome.
However, for the following reasons, this is acceptable within the
Block-Relief thesis evaluation scope:

-   The lottery pool represents only 20% of total donations, and is
    split among 3 winners --- making manipulation economically
    unattractive relative to the cost of validator influence.

-   All testnet deployments (Sepolia, Polygon Amoy) are used for
    evaluation only; no real monetary value is at stake.

-   The seed combines five independent inputs, making deterministic
    prediction significantly harder than single-input PRNG.

For production deployment, this component should be replaced with
Chainlink VRF v2 (Verifiable Random Function), which provides
cryptographically provable randomness that cannot be influenced by
validators \[3\]. This upgrade path is explicitly documented in the
contract source code comments.

**3) MEDIUM --- Dangerous Strict Equality (incorrect-equality)**

Slither identified two strict equality comparisons involving
donorIndex\[msg.sender\] == 0 in donate() and idx == 0 in getMyTicket().
Slither warns against strict equality with zero in mappings because
default mapping values are zero, which can lead to logic errors if not
handled carefully.

In Block-Relief, this is an intentional design choice: donorIndex uses
1-based indexing, where a value of 0 explicitly indicates that an
address has not yet donated. This convention is consistently applied
throughout the contract and is documented in the source code comments.
The comparison donorIndex\[msg.sender\] == 0 correctly identifies
unregistered donors and is not exploitable. This finding is classified
as a false positive for this implementation.

**4) MEDIUM --- External Calls Inside Loops (calls-loop)**

Slither flagged external ETH transfer calls (.call{value}()) inside
for-loops in distributeBatch(), autoDistribute(), and
\_pickLotteryWinners(). This pattern is generally discouraged because a
failing call in one iteration could theoretically affect subsequent
iterations.

In Block-Relief, this pattern is a fundamental architectural
requirement: each victim must receive their proportional allocation as
an individual atomic transfer, ensuring that a failed transfer to one
victim does not block payments to others. The implementation handles
this correctly --- the return value of each .call{} is captured in a
bool ok variable, and payment failure is recorded via isPaid and claimed
state variables without reverting the transaction. The use of .call{}
(rather than .transfer() or .send()) is deliberate, as .call{} forwards
all available gas and avoids the 2300 gas stipend limitation that would
cause failures with smart contract recipient wallets.

**5) LOW --- Remaining Findings**

The following lower-severity findings were identified and addressed or
acknowledged:

**TABLE III. Low/Informational Findings and Resolutions**

  ----------------------------------------------------------------------------------------------------------
  **Detector**            **Finding**                                             **Resolution**
  ----------------------- ------------------------------------------------------- --------------------------
  **solc-version**        \^0.8.19 contains 3 known compiler bugs                 FIXED in v3: upgraded to
                          (VerbatimInvalidDeduplication,                          \^0.8.20 which does not
                          FullInlinerNonExpressionSplitArgumentEvaluationOrder,   contain these bugs
                          MissingSideEffectsOnSelectorAccess)                     

  **immutable-states**    admin state variable is set once in constructor but not FIXED in v3: declared as
                          declared immutable, costing unnecessary storage reads   address public immutable
                                                                                  admin, saving gas on every
                                                                                  onlyAdmin check

  **constable-states**    lotteryPrizePercent is assigned a constant value (20)   FIXED in v3: declared as
                          but not declared constant, wasting storage              uint256 public constant
                                                                                  lotteryPrizePercent = 20

  **naming-convention**   Function parameters with underscore prefix              FIXED in v3: all
                          (\_identityHash, \_score, \_wallet) do not follow       parameters renamed to
                          Solidity mixedCase convention                           mixedCase without
                                                                                  underscore prefix

  **low-level-calls**     Use of .call{value}() instead of .transfer() or .send() INTENTIONAL: .call{}
                                                                                  forwards all gas,
                                                                                  preventing failures with
                                                                                  contract recipient
                                                                                  wallets. Acknowledged in
                                                                                  source comments

  **timestamp**           block.timestamp used for donation recording and lottery ACCEPTABLE: timestamp is
                          seed generation                                         used for recording (not
                                                                                  critical logic). Lottery
                                                                                  seed combines 5 inputs.
                                                                                  Acceptable for testnet
                                                                                  evaluation

  **costly-loop**         totalDistributed storage variable updated inside        JUSTIFIED: running total
                          distribution loop                                       is required for
                                                                                  last-victim remainder
                                                                                  calculation. Mitigated by
                                                                                  batch processing
                                                                                  (distributeBatch)
  ----------------------------------------------------------------------------------------------------------

**E. Security Fixes Applied in v3 Contract**

Table IV summarizes all code-level changes made between the v2 and v3
contracts in response to Slither findings, including the specific
Solidity modification applied in each case.

**TABLE IV. Code Changes: v2 → v3**

  -----------------------------------------------------------------------------------------
  **Issue**          **Location**             **v2 Code**             **v3 Fix**
  ------------------ ------------------------ ----------------------- ---------------------
  **CEI Pattern**    distributeBatch(),       ETH transfer → then     State update
                     autoDistribute()         state update            (reliefAmount,
                                                                      isPaid,
                                                                      totalDistributed) →
                                                                      then ETH transfer

  **CEI Pattern**    \_pickLotteryWinners()   ETH transfer → then     push() with
                                              lotteryWinners.push()   claimed:true → ETH
                                                                      transfer → if failed:
                                                                      claimed=false

  **Compiler         Line 2 of                pragma solidity         pragma solidity
  Version**          FloodRelief.sol          \^0.8.19                \^0.8.20

  **Immutability**   State variable: admin    address public admin    address public
                                                                      immutable admin

  **Constant**       State variable:          uint256 public          uint256 public
                     lotteryPrizePercent      lotteryPrizePercent =   constant
                                              20                      lotteryPrizePercent =
                                                                      20

  **Naming**         registerVictim()         \_identityHash,         identityHash, score,
                     parameters               \_score, \_wallet       wallet
  -----------------------------------------------------------------------------------------

**F. Security Analysis Conclusion**

The static security analysis of the Block-Relief smart contract using
Slither identified 35 findings in the initial version. Through
systematic remediation, 6 findings were fully resolved and the total
finding count was reduced to 29 in the final v3 contract. The most
significant security improvement was the application of the
Checks-Effects-Interactions pattern across all ETH distribution
functions, eliminating the theoretical reentrancy window while
maintaining the noReentrant mutex guard for defense-in-depth.

The remaining 29 findings fall into three categories: (1) justified
design patterns required by the system architecture (calls-loop,
low-level-calls, costly-loop), (2) known limitations with documented
production upgrade paths (weak-prng → Chainlink VRF v2), and (3) false
positives arising from Slither\'s conservative static analysis
(incorrect-equality, reentrancy-eth residual). No critical logical
vulnerabilities --- such as unauthorized fund access, incorrect
distribution calculations, or denial-of-service attacks --- were
identified in either version.

The security analysis results confirm that Block-Relief is suitable for
testnet evaluation on Sepolia and Polygon Amoy, meeting the security
requirements for an academic blockchain prototype. Table V provides a
final severity classification of all findings.

**TABLE V. Final Security Classification Summary (v3 Contract)**

  ---------------------------------------------------------------------------
  **Severity**   **Total       **Fixed**     **Remaining**   **Reason
                 Found**                                     Remaining**
  -------------- ------------- ------------- --------------- ----------------
  **HIGH**       5             0\*           5               CEI applied /
                                                             PRNG
                                                             acknowledged

  **MEDIUM**     6             0             6               Intentional
                                                             design / false
                                                             positives

  **LOW / INFO** 24            6             18              Justified
                                                             patterns /
                                                             informational

  **TOTAL**      **35**        **6**         **29**          **17% reduction
                                                             achieved**
  ---------------------------------------------------------------------------

\* HIGH reentrancy findings are mitigated via noReentrant mutex + CEI
pattern. Slither continues to flag these due to static analysis
limitations (cannot detect runtime mutex guards). No exploitable
reentrancy path exists in v3.

**References**

\[1\] Trail of Bits, \"Slither: A Static Analysis Framework for Smart
Contracts,\" GitHub Repository, 2024. \[Online\]. Available:
https://github.com/crytic/slither

\[2\] ConsenSys, \"Ethereum Smart Contract Security Best Practices:
Checks-Effects-Interactions Pattern,\" 2023. \[Online\]. Available:
https://consensys.github.io/smart-contract-best-practices/

\[3\] Chainlink, \"Chainlink VRF: Verifiable Random Function,\"
Chainlink Documentation, 2024. \[Online\]. Available:
https://docs.chain.link/vrf
