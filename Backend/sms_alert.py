"""
============================================================
  Block-Relief : Android SMS Gateway Bridge (Offline-Capable)
  UPDATED: Whitelist support for testing (2-3 numbers only)
============================================================
  Mode:
   - SMS_GATEWAY_ENABLED = False  → simulation (console + CSV log)
   - SMS_GATEWAY_ENABLED = True   → real SMS, but only to SMS_TEST_WHITELIST
   
  To test with 2-3 people:
   1. Set SMS_GATEWAY_ENABLED = True in config.py
   2. Set SMS_TEST_WHITELIST = ["+880...", "+880..."] in config.py
   3. Only those numbers get real SMS, rest are SIMULATED
============================================================
"""

import requests
from datetime import datetime
import pandas as pd

import config


def _log_sms(mobile: str, message: str, status: str, response: str = ""):
    """প্রতিটা SMS attempt log করো (thesis evaluation-এর জন্য)।"""
    row = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Mobile":    mobile,
        "Message":   message[:300],
        "Status":    status,
        "Response":  str(response)[:200],
    }
    df_new = pd.DataFrame([row])
    if config.SMS_LOG_CSV.exists():
        df = pd.concat([pd.read_csv(config.SMS_LOG_CSV), df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(config.SMS_LOG_CSV, index=False)


def _is_whitelisted(mobile: str) -> bool:
    """
    Check if this number is in the test whitelist.
    If no whitelist defined → allow all (old behavior).
    """
    whitelist = getattr(config, 'SMS_TEST_WHITELIST', [])
    if not whitelist:
        return True   # no whitelist set → allow all
    return mobile in whitelist


def send_sms_via_android(mobile: str, message: str) -> bool:
    if not mobile or mobile.strip() == "":
        _log_sms("", message, status="NO_NUMBER")
        print("   ⚠️  No mobile number provided")
        return False

    # ---- Simulation mode ----
    if not config.SMS_GATEWAY_ENABLED:
        print(f"   📱 [SIMULATED SMS → {mobile}]")
        for line in message.split("\n"):
            if line.strip():
                print(f"      {line}")
        _log_sms(mobile, message, status="SIMULATED")
        return True

    # ---- Whitelist check ----
    if not _is_whitelisted(mobile):
        print(f"   📱 [SIMULATED — not in whitelist → {mobile}]")
        _log_sms(mobile, message, status="SIMULATED_WHITELIST")
        return True

    # ---- Real SMS — Simple SMS Gateway (Pabrik Aplikasi) ----
    try:
        payload = {
            "phone":   mobile,    # ← এই app এর format
            "message": message,
        }
        url = f"{config.SMS_GATEWAY_URL}/send-sms"  # ← এই app এর endpoint

        r = requests.post(url, json=payload, timeout=10)

        if r.status_code in (200, 201, 202):
            _log_sms(mobile, message, status="SENT", response=r.text)
            print(f"   ✅ Real SMS sent to {mobile}")
            return True

        _log_sms(mobile, message, status="FAILED", response=r.text)
        print(f"   ❌ SMS failed [{r.status_code}]: {r.text[:100]}")
        return False

    except Exception as e:
        _log_sms(mobile, message, status="ERROR", response=str(e))
        print(f"   ⚠️  SMS error: {e}")
        return False

def send_relief_confirmation(mobile: str, receipt: dict) -> bool:
    """Victim-কে Bengali confirmation SMS পাঠাও।"""
    msg = (
        "Block-Relief\n"
        "প্রিয় সুবিধাভোগী,\n"
        "আপনার ত্রাণ তহবিল নিশ্চিত হয়েছে।\n"
        f"পরিমাণ: {receipt['Amount_BDT']:,.0f} BDT\n"
        f"Receipt: {receipt['ReceiptID']}\n"
        f"তারিখ: {receipt['Timestamp'][:10]}"
    )
    return send_sms_via_android(mobile, msg)


# ---- CLI: Send test SMS to whitelist numbers ----
def send_test_sms_to_whitelist():
    """
    Manually test SMS by sending to whitelist numbers only.
    Run: python sms_alert.py
    """
    whitelist = getattr(config, 'SMS_TEST_WHITELIST', [])
    if not whitelist:
        print("⚠️  SMS_TEST_WHITELIST is empty in config.py")
        print("   Add your test numbers there first.")
        return

    print(f"📱 Sending test SMS to {len(whitelist)} number(s)...")
    dummy_receipt = {
        "ReceiptID":   "FRD-TEST-0001",
        "Amount_BDT":  5000,
        "Timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    for number in whitelist:
        print(f"\n→ {number}")
        send_relief_confirmation(number, dummy_receipt)


if __name__ == "__main__":
    print("📱 SMS Alert — Whitelist Test Mode")
    print("=" * 60)
    send_test_sms_to_whitelist()