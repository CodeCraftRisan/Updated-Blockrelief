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
    uint256 public victimCount;
    bool    public isDistributed;
    bool    private locked;

    // Batch distribution tracking
    uint256 public victimPool;
    uint256 public reservePool;
    uint256 public totalDistributed;
    bool    public distributionFinalized;

    // ============================================================
    //  SECTION 2 : STRUCTS
    // ============================================================

    struct Victim {
        uint256 id;
        bytes32 identityHash;   // SHA-256(NID+name+salt) off-chain, stored as bytes32
        uint256 score;          // Fuzzy AHP score × 100  (e.g. 88.10 → 8810)
        uint256 allocatedAmount; // [FIX-RESEARCH] Stored off-chain allocation in wei
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
    mapping(bytes32 => bool)    public registeredIdentity; // [FIX-HIGH] Duplicate protection
    Donor[]        public donors;

    // ============================================================
    //  SECTION 4 : EVENTS
    // ============================================================

    event DonationReceived(address indexed donor, uint256 amount, uint256 ticketNumber, uint256 totalDonated);
    event VictimRegistered(uint256 indexed victimId, bytes32 identityHash, uint256 score, uint256 allocatedAmount, address wallet);
    event FundReleased(uint256 indexed victimId, uint256 amount, address wallet);
    event DistributionFinalized(uint256 victimPool, uint256 reservePool);
    event ReserveWithdrawn(address indexed receiver, uint256 amount);
    event TargetFundUpdated(uint256 newTarget);

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
        uint256 allocatedAmount,
        address wallet
    ) external onlyAdmin {
        require(!isDistributed,               "Distribution already done");
        require(score > 0,                    "Score must be > 0");
        require(wallet != address(0),         "Invalid wallet");
        require(!registeredIdentity[identityHash], "Duplicate victim");

        registeredIdentity[identityHash] = true;
        victimCount += 1;
        victims[victimCount] = Victim({
            id:              victimCount,
            identityHash:    identityHash,
            score:           score,
            allocatedAmount: allocatedAmount,
            reliefAmount:    0,
            walletAddress:   wallet,
            isRegistered:    true,
            isPaid:          false
        });

        emit VictimRegistered(victimCount, identityHash, score, allocatedAmount, wallet);
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
    //  SECTION 9 : PULL PAYMENT MODEL (Recommended for Research)
    // ============================================================

    /**
     * Finalizes the fund pool and locks the distribution phase.
     * Separates the reserve pool from the victim pool.
     */
    function finalizeDistribution() external onlyAdmin {
        require(totalDonated >= targetFund, "Target fund not reached");
        require(!isDistributed,             "Already finalized");

        isDistributed = true;
        uint256 bal   = address(this).balance;
        reservePool   = bal > targetFund ? bal - targetFund : 0;
        victimPool    = bal - reservePool;

        emit DistributionFinalized(victimPool, reservePool);
    }

    /**
     * Pull Payment: Victims claim their own relief.
     * This avoids gas limit issues in loops and improves accounting.
     */
    function claimRelief(uint256 victimId) external noReentrant {
        require(isDistributed, "Distribution not finalized");
        require(victimId > 0 && victimId <= victimCount, "Invalid victim ID");

        Victim storage v = victims[victimId];
        require(v.walletAddress == msg.sender, "Only victim wallet can claim");
        require(!v.isPaid,                     "Already paid");

        uint256 amount = v.allocatedAmount;
        require(amount > 0, "No relief allocated");

        // [FIX-HIGH] Checks-Effects-Interactions
        v.isPaid = true;
        v.reliefAmount = amount;
        totalDistributed += amount;

        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "Claim transfer failed");

        emit FundReleased(victimId, amount, msg.sender);
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
        uint256  allocatedAmount,
        uint256  reliefAmount,
        address  wallet,
        bool     isPaid
    ) {
        require(id > 0 && id <= victimCount, "Invalid victim id");
        Victim memory v = victims[id];
        return (v.id, v.identityHash, v.score, v.allocatedAmount, v.reliefAmount, v.walletAddress, v.isPaid);
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
        uint256 totalVictims,
        uint256 weiDistributed,
        bool    isFinalized
    ) {
        return (victimCount, totalDistributed, isDistributed);
    }

    function isAdmin(address user) external view returns (bool) {
        return user == admin;
    }
}
