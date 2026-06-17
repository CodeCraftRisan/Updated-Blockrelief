from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
CONTRACT_DIR = BASE_DIR / "contracts"
FRONTEND_DIR = BASE_DIR / "frontend"
REPORTS_DIR = BASE_DIR / "reports"
TESTS_DIR = BASE_DIR / "tests"
RECEIPT_DIR = DATA_DIR / "receipts"
PIPELINE_LOG = DATA_DIR / "pipeline.log"
EVENT_STATE_FILE = DATA_DIR / "event_listener_state.json"

for path in (DATA_DIR, CONTRACT_DIR, REPORTS_DIR, RECEIPT_DIR, TESTS_DIR):
    path.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))

def _get_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))

def _get_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

# -------------------------------------------------------------------
# Blockchain
# -------------------------------------------------------------------
GANACHE_URL = os.getenv("GANACHE_URL", "http://127.0.0.1:7545")
CHAIN_ID = _get_int("CHAIN_ID", 1337)
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
ABI_PATH = CONTRACT_DIR / "FloodRelief_abi.json"

ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY", "")
ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS", "")

# -------------------------------------------------------------------
# Project parameters
# -------------------------------------------------------------------
TOTAL_FUND_POOL_BDT = _get_int("TOTAL_FUND_POOL_BDT", 1_000_000)
MIN_RELIEF_BDT = _get_int("MIN_RELIEF_BDT", 2_000)
MAX_RELIEF_BDT = _get_int("MAX_RELIEF_BDT", 25_000)
RANDOM_SEED = _get_int("RANDOM_SEED", 42)
DEBUG_MODE = _get_bool("DEBUG_MODE", False)

ETH_TO_BDT_RATE = _get_float("ETH_TO_BDT_RATE", 100000.0)
if ETH_TO_BDT_RATE <= 0:
    raise ValueError("ETH_TO_BDT_RATE must be > 0")

BDT_TO_ETH = 1 / ETH_TO_BDT_RATE
WEI_PER_ETH = 10**18
BDT_TO_WEI = int(round(BDT_TO_ETH * WEI_PER_ETH))

# -------------------------------------------------------------------
# Messaging / privacy
# -------------------------------------------------------------------
SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "")
SMS_GATEWAY_ENABLED = _get_bool("SMS_GATEWAY_ENABLED", False)
SMS_TEST_WHITELIST = _get_list("SMS_TEST_WHITELIST", "")

HASH_SECRET = os.getenv("HASH_SECRET", "")
HASH_SALT = HASH_SECRET  # backward-compatible alias

# -------------------------------------------------------------------
# Data files
# -------------------------------------------------------------------
NID_DB_CSV = DATA_DIR / "National_ID_Database.csv"
VOLUNTEER_CSV = DATA_DIR / "volunteer_input.csv"
VERIFIED_CSV = DATA_DIR / "verified_victims.csv"
REJECTED_CSV = DATA_DIR / "rejected_entries.csv"
WEIGHTS_CSV = DATA_DIR / "fuzzy_ahp_weights.csv"
SCORED_CSV = DATA_DIR / "scored_victims.csv"
ALLOCATION_CSV = DATA_DIR / "fund_allocation.csv"
REGISTRATION_CSV = DATA_DIR / "registration_log.csv"
BANK_ACCOUNTS_CSV = DATA_DIR / "bank_accounts.csv"
RECEIPTS_CSV = DATA_DIR / "receipts.csv"
SMS_LOG_CSV = DATA_DIR / "sms_log.csv"
VERIFICATION_REPORT_PATH = DATA_DIR / "verification_report.txt"
FAIRNESS_RESULTS_CSV = DATA_DIR / "fairness_analysis_results.csv"

# -------------------------------------------------------------------
# Column constants
# -------------------------------------------------------------------
COL_VICTIM_ID = "Victim_ID"
COL_NID = "NID"
COL_NAME = "Name"
COL_PHONE = "Phone"
COL_SCORE = "Vulnerability_Score"
COL_ALLOCATED = "Allocated_Fund_BDT"
COL_ALLOCATED_ETH = "Allocated_Fund_ETH"
COL_ALLOCATED_WEI = "Allocated_Fund_Wei"
COL_ACC_NUM = "Account_Number"
COL_ACC_HOLDER = "Account_Holder"
COL_BALANCE = "Current_Balance"
COL_MFS = "MFS_Linked"

def normalize_phone(raw) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("880"):
        return "+" + digits
    if digits.startswith("0"):
        return "+88" + digits
    return "+880" + digits

def require_non_empty(name: str, value: str) -> None:
    if not str(value).strip():
        raise ValueError(
            f"Missing required configuration: {name}. "
            f"Set it in your .env file or environment variables."
        )