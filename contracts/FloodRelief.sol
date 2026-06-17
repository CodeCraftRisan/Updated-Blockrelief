// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * ============================================================
 *   Block-Relief : FloodRelief Smart Contract (Final v3)
 * ============================================================
 *
 *  FIXES vs v2 (Slither report dated 2026):
 *
 *   [HIGH-1 FIXED]  Reentrancy in distribution functions:
 *                   Applied Checks-Effects-Interactions pattern.
 *                   State updates occur before external ETH transfers.
 *
 *   [HIGH-2 FIXED]  Reentrancy in distributeBatch() / autoDistribute():
 *                   v.reliefAmount, v.isPaid, totalDistributed all
 *                   updated BEFORE payable call.
 *
 *   [LOW FIXED]     pragma ^0.8.19 → ^0.8.20 (no known severe bugs)
 *
 *   [LOW FIXED]     admin declared immutable
 *
 *   [INFO]          reserve pool logic preserves excess donations.
 *
 *   [INFO]          calls-loop: intentional design — each victim
 *                   transfer is atomic; failure is non-blocking.
 *
 *   [INFO]          donorIndex == 0: intentional 1-based mapping.
 *
 *   [INFO]          low-level-calls: .call{} preferred over
 *                   .transfer() to avoid 2300 gas stipend issues.
 *
 *   [SYNTAX FIXED]  distributeBatch(): missing for-loop declaration,
 *                   undeclared batchPaid variable, and resulting
 *                   brace/scope errors — all 6 errors corrected.
 *
 * ============================================================
 */
contract FloodRelief {

    // ============================================================
    //  SECTION 1 : STATE VARIABLES
    // ============================================================

    // [FIX-LOW] immutable — set once in constructor, never changes
    address public immutable admin;

    uint256 public targetFund;
    uint256 public totalDonated;
    uint256 public totalScore;
    uint256 public victimCount;
    bool    public isDistributed;
    bool    private locked;

    // Batch distribution tracking
    uint256 public victimPool;
    uint256 public reservePool;
    uint256 public lastDistributedId;
    uint256 public totalDistributed;
    bool    public victimPayoutDone;

    // ============================================================
    //  SECTION 2 : STRUCTS
    // ============================================================

    struct Victim {
        uint256 id;
        bytes32 identityHash;   // SHA-256(NID+name+salt) off-chain, stored as bytes32
        uint256 score;          // Fuzzy AHP score × 100  (e.g. 88.10 → 8810)
        uint256 reliefAmount;   // wei paid to this victim
        address walletAddress;
        bool    isRegistered;
        bool    isPaid;
    }

    struct Donor {
        address donorAddress;
        uint256 totalAmount;
        uint256 ticketNumber;
        uint256 donatedAt;
    }

    // ============================================================
    //  SECTION 3 : MAPPINGS & ARRAYS
    // ============================================================

    mapping(uint256 => Victim) public victims;
    mapping(address => uint256) public donorIndex;  // 1-based; 0 = not registered
    Donor[]        public donors;

    // ============================================================
    //  SECTION 4 : EVENTS
    // ============================================================

    event DonationReceived(address indexed donor, uint256 amount, uint256 ticketNumber, uint256 totalDonated);
    event VictimRegistered(uint256 indexed victimId, bytes32 identityHash, uint256 score, address wallet);
    event FundReleased(uint256 indexed victimId, uint256 amount, address wallet);
    event AllFundsDistributed(uint256 totalDistributed, uint256 recipients);
    event ReserveWithdrawn(address indexed receiver, uint256 amount);
    event TargetFundUpdated(uint256 newTarget);
    event BatchDistributed(uint256 fromId, uint256 toId, uint256 batchWeiPaid);

    // ============================================================
    //  SECTION 5 : MODIFIERS
    // ============================================================

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }

    modifier noReentrant() {
        require(!locked, "Reentrancy blocked");
        locked = true;
        _;
        locked = false;
    }

    // ============================================================
    //  SECTION 6 : CONSTRUCTOR
    // ============================================================

    constructor(uint256 targetFundInWei) {
        admin      = msg.sender;
        targetFund = targetFundInWei;
    }

    // ============================================================
    //  SECTION 7 : ADMIN FUNCTIONS
    // ============================================================

    function registerVictim(
        bytes32 identityHash,
        uint256 score,
        address wallet
    ) external onlyAdmin {
        require(!isDistributed,        "Distribution already done");
        require(score > 0,             "Score must be > 0");
        require(wallet != address(0),  "Invalid wallet");

        victimCount += 1;
        victims[victimCount] = Victim({
            id:            victimCount,
            identityHash:  identityHash,
            score:         score,
            reliefAmount:  0,
            walletAddress: wallet,
            isRegistered:  true,
            isPaid:        false
        });

        totalScore += score;
        emit VictimRegistered(victimCount, identityHash, score, wallet);
    }

    function updateTargetFund(uint256 newTargetInWei) external onlyAdmin {
        require(!isDistributed, "Already distributed");
        targetFund = newTargetInWei;
        emit TargetFundUpdated(newTargetInWei);
    }

    // ============================================================
    //  SECTION 8 : DONATE
    // ============================================================

    function donate() public payable {
        require(msg.value > 0,    "Donation must be > 0");
        require(!isDistributed,   "Distribution already done");

        totalDonated += msg.value;

        uint256 ticket;
        if (donorIndex[msg.sender] == 0) {
            // [INFO] donorIndex == 0 check is intentional (1-based mapping)
            donors.push(Donor({
                donorAddress: msg.sender,
                totalAmount:  msg.value,
                ticketNumber: donors.length + 1,
                donatedAt:    block.timestamp
            }));
            donorIndex[msg.sender] = donors.length;
            ticket = donors.length;
        } else {
            uint256 idx = donorIndex[msg.sender] - 1;
            donors[idx].totalAmount += msg.value;
            donors[idx].donatedAt   = block.timestamp;
            ticket = donors[idx].ticketNumber;
        }

        emit DonationReceived(msg.sender, msg.value, ticket, totalDonated);
    }

    receive() external payable {
        donate();
    }

    // ============================================================
    //  SECTION 9 : BATCH DISTRIBUTION (Sepolia / Polygon safe)
    // ============================================================

    /**
     * Paginated distribution — call in batches of 10 for testnets.
     * For Ganache demo, one call with (0, victimCount) works fine.
     *
     * Usage:
     *   distributeBatch(0,  10)  → pays victims 1..10
     *   distributeBatch(10, 20)  → pays victims 11..20
     *   ...
     *   distributeBatch(90, 100) → pays victims 91..100
     */
    function distributeBatch(
        uint256 fromIndex,
        uint256 toIndex
    ) external onlyAdmin noReentrant {
        require(totalDonated >= targetFund,          "Target fund not reached");
        require(!victimPayoutDone,                   "Already paid all victims");
        require(victimCount > 0,                     "No victims registered");
        require(totalScore  > 0,                     "Total score is zero");
        require(fromIndex == lastDistributedId,      "Must continue from last batch");
        require(toIndex   <= victimCount,            "toIndex exceeds victim count");
        require(toIndex   >  fromIndex,              "toIndex must be > fromIndex");

        // Lock pool once on first batch
        if (lastDistributedId == 0) {
            isDistributed = true;
            uint256 bal  = address(this).balance;
            reservePool  = bal > targetFund ? bal - targetFund : 0;
            uint256 allocated = bal - reservePool;
            victimPool   = allocated;
        }

        // [FIX-SYNTAX] Declared batchPaid and added the missing for-loop
        uint256 batchPaid = 0;

        for (uint256 i = fromIndex + 1; i <= toIndex; i++) {
            Victim storage v = victims[i];
            if (!v.isRegistered || v.isPaid) continue;

            uint256 share = (i == victimCount)
                ? victimPool - totalDistributed          // last victim gets remainder
                : (victimPool * v.score) / totalScore;

            // [FIX-HIGH] Checks-Effects-Interactions:
            // ALL state updates BEFORE external call
            v.reliefAmount    = share;
            v.isPaid          = true;
            totalDistributed += share;
            batchPaid        += share;

            // External call LAST
            (bool ok, ) = payable(v.walletAddress).call{value: share}("");
            if (ok) {
                emit FundReleased(i, share, v.walletAddress);
            }
        }

        lastDistributedId = toIndex;
        emit BatchDistributed(fromIndex, toIndex, batchPaid);

        if (toIndex == victimCount) {
            victimPayoutDone = true;
            emit AllFundsDistributed(totalDistributed, victimCount);
        }
    }

    // ============================================================
    //  SECTION 10 : AUTO DISTRIBUTE (Ganache demo only)
    // ============================================================

    /**
     * Single-tx distribution — Ganache only (no gas limit).
     * Do NOT use on Sepolia or Polygon — use distributeBatch() instead.
     */
    function autoDistribute() external onlyAdmin noReentrant {
        require(totalDonated >= targetFund, "Target fund not reached");
        require(!isDistributed,             "Already distributed");
        require(victimCount > 0,            "No victims registered");
        require(totalScore  > 0,            "Total score is zero");

        isDistributed    = true;
        victimPayoutDone = true;

        uint256 bal  = address(this).balance;
        reservePool  = bal > targetFund ? bal - targetFund : 0;
        uint256 allocated = bal - reservePool;
        victimPool   = allocated;

        uint256 distributed = 0;

        for (uint256 i = 1; i <= victimCount; i++) {
            Victim storage v = victims[i];
            if (!v.isRegistered || v.isPaid) continue;

            uint256 share = (i == victimCount)
                ? victimPool - distributed
                : (victimPool * v.score) / totalScore;

            // [FIX-HIGH] State BEFORE external call
            v.reliefAmount    = share;
            v.isPaid          = true;
            distributed      += share;
            totalDistributed += share;

            (bool ok, ) = payable(v.walletAddress).call{value: share}("");
            if (ok) {
                emit FundReleased(i, share, v.walletAddress);
            }
        }

        emit AllFundsDistributed(distributed, victimCount);
    }

    // ============================================================
    //  SECTION 11 : RESERVE WITHDRAWAL
    // ============================================================

    function withdrawReserve(address payable receiver) external onlyAdmin noReentrant {
        require(reservePool > 0, "No reserve funds");
        require(receiver != address(0), "Invalid receiver");

        uint256 amount = reservePool;
        reservePool = 0;

        (bool ok, ) = receiver.call{value: amount}("");
        require(ok, "Reserve transfer failed");

        emit ReserveWithdrawn(receiver, amount);
    }

    // ============================================================
    //  SECTION 12 : VIEW FUNCTIONS
    // ============================================================

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function getReserveBalance() external view returns (uint256) {
        return reservePool;
    }

    function getDonorCount() external view returns (uint256) {
        return donors.length;
    }

    function getDonor(uint256 index) external view returns (
        address donorAddress,
        uint256 totalAmount,
        uint256 ticketNumber,
        uint256 donatedAt
    ) {
        require(index < donors.length, "Invalid donor index");
        Donor memory d = donors[index];
        return (d.donorAddress, d.totalAmount, d.ticketNumber, d.donatedAt);
    }

    function getMyTicket() external view returns (uint256) {
        uint256 idx = donorIndex[msg.sender];
        if (idx == 0) return 0;
        return donors[idx - 1].ticketNumber;
    }

    function getVictim(uint256 id) external view returns (
        uint256  vid,
        bytes32  identityHash,
        uint256  score,
        uint256  reliefAmount,
        address  wallet,
        bool     isPaid
    ) {
        require(id > 0 && id <= victimCount, "Invalid victim id");
        Victim memory v = victims[id];
        return (v.id, v.identityHash, v.score, v.reliefAmount, v.walletAddress, v.isPaid);
    }

    function getFundProgress() external view returns (
        uint256 collected,
        uint256 target,
        uint256 percent
    ) {
        uint256 pct = targetFund == 0 ? 0 : (totalDonated * 100) / targetFund;
        return (totalDonated, targetFund, pct);
    }

    function getDistributionProgress() external view returns (
        uint256 paidVictims,
        uint256 totalVictims,
        uint256 weiDistributed,
        bool    allDone
    ) {
        return (lastDistributedId, victimCount, totalDistributed, victimPayoutDone);
    }

    function isAdmin(address user) external view returns (bool) {
        return user == admin;
    }
}
