"""
============================================================
  Block-Relief : SMS Gateway Debugger
  
  এই script তোমার Android app-এর সঠিক endpoint
  automatically খুঁজে বের করবে।
  
  Run: python sms_debug.py
============================================================
"""

import requests
import json

# ── তোমার phone-এর IP দাও ──
GATEWAY_IP   = "192.168.0.108"   # ← তোমার IP বদলাও
GATEWAY_PORT = "8080"
BASE_URL     = f"http://{GATEWAY_IP}:{GATEWAY_PORT}"

# Test phone number (তোমার নিজের number)
TEST_PHONE   = "+8801301581457"   # ← তোমার number দাও
TEST_MESSAGE = "Block-Relief Test Message - SMS system OK!"

print("=" * 60)
print("SMS GATEWAY ENDPOINT DEBUGGER")
print("=" * 60)
print(f"Target: {BASE_URL}")
print(f"Phone:  {TEST_PHONE}")
print()

# ============================================================
# সব popular SMS Gateway app-এর endpoint format
# ============================================================
ENDPOINTS_TO_TRY = [

    # ── 1. Artem Averin "SMS Gateway" (de.smsgateway) ──
    {
        "name": "Artem Averin - /message (JSON array)",
        "method": "POST",
        "url": f"{BASE_URL}/message",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message":      TEST_MESSAGE,
            "phoneNumbers": [TEST_PHONE]
        })
    },
    {
        "name": "Artem Averin - /message (single)",
        "method": "POST",
        "url": f"{BASE_URL}/message",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": TEST_MESSAGE,
            "phone":   TEST_PHONE
        })
    },
    {
        "name": "Artem Averin - /send",
        "method": "POST",
        "url": f"{BASE_URL}/send",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message":      TEST_MESSAGE,
            "phoneNumbers": [TEST_PHONE]
        })
    },

    # ── 2. SMS Gateway for IoT (smsgateway.me local) ──
    {
        "name": "SMSGateway.me - /api/send",
        "method": "POST",
        "url": f"{BASE_URL}/api/send",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "phone":   TEST_PHONE,
            "message": TEST_MESSAGE
        })
    },
    {
        "name": "SMSGateway.me - /api/messages",
        "method": "POST",
        "url": f"{BASE_URL}/api/messages",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "phone":   TEST_PHONE,
            "message": TEST_MESSAGE
        })
    },

    # ── 3. SMS Gateway (GET format) ──
    {
        "name": "GET format - ?phone=&msg=",
        "method": "GET",
        "url": f"{BASE_URL}/send",
        "params": {"phone": TEST_PHONE, "msg": TEST_MESSAGE},
        "headers": {}
    },
    {
        "name": "GET format - ?number=&message=",
        "method": "GET",
        "url": f"{BASE_URL}/send",
        "params": {"number": TEST_PHONE, "message": TEST_MESSAGE},
        "headers": {}
    },

    # ── 4. Other common formats ──
    {
        "name": "POST /sms",
        "method": "POST",
        "url": f"{BASE_URL}/sms",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "phone":   TEST_PHONE,
            "message": TEST_MESSAGE
        })
    },
    {
        "name": "POST / (root)",
        "method": "POST",
        "url": f"{BASE_URL}/",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message":      TEST_MESSAGE,
            "phoneNumbers": [TEST_PHONE]
        })
    },
    {
        "name": "POST /api/sms",
        "method": "POST",
        "url": f"{BASE_URL}/api/sms",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "phone":   TEST_PHONE,
            "message": TEST_MESSAGE
        })
    },
    {
        "name": "POST /v1/message",
        "method": "POST",
        "url": f"{BASE_URL}/v1/message",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message":      TEST_MESSAGE,
            "phoneNumbers": [TEST_PHONE]
        })
    },
]

# ============================================================
# Step 1: আগে check করো server reachable কিনা
# ============================================================
print("── Step 1: Server Reachability ──")
try:
    r = requests.get(BASE_URL, timeout=5)
    print(f"✅ Server is REACHABLE at {BASE_URL}")
    print(f"   Status: {r.status_code}")
    if r.text:
        print(f"   Response: {r.text[:200]}")
except requests.exceptions.ConnectionError:
    print(f"❌ CANNOT CONNECT to {BASE_URL}")
    print()
    print("Possible reasons:")
    print("  1. SMS Gateway app-টা phone-এ চালু নেই")
    print("  2. Phone এবং PC same WiFi-তে নেই")
    print("  3. IP address ভুল")
    print()
    print("Check করো:")
    print("  → Android app open করো → 'START' চাপো")
    print("  → App screen-এ IP address দেখাবে — সেটা config.py তে দাও")
    print("  → PC তে: ping " + GATEWAY_IP)
    exit(1)
except Exception as e:
    print(f"⚠ Connection issue: {e}")
    print("App চলছে কিনা নিশ্চিত করো।")
    exit(1)

print()

# ============================================================
# Step 2: সব endpoint try করো
# ============================================================
print("── Step 2: Testing All Endpoints ──")
print(f"Trying {len(ENDPOINTS_TO_TRY)} different formats...\n")

working = []

for ep in ENDPOINTS_TO_TRY:
    name = ep["name"]
    try:
        if ep["method"] == "POST":
            r = requests.post(
                ep["url"],
                data=ep.get("body", ""),
                headers=ep.get("headers", {}),
                timeout=5
            )
        else:  # GET
            r = requests.get(
                ep["url"],
                params=ep.get("params", {}),
                headers=ep.get("headers", {}),
                timeout=5
            )

        status = r.status_code
        resp_text = r.text[:100] if r.text else "(empty)"

        if status in (200, 201, 202):
            print(f"✅ WORKING! [{status}] {name}")
            print(f"   Response: {resp_text}")
            working.append(ep)
        elif status == 404:
            print(f"   ❌ 404  {name}")
        elif status == 405:
            print(f"   ⚠ 405 (Method not allowed) {name}")
        elif status == 400:
            print(f"   ⚠ 400 (Bad request — endpoint exists but wrong body) {name}")
            print(f"   Response: {resp_text}")
            # 400 মানে endpoint আছে কিন্তু format ভুল — still useful
            working.append({**ep, "_note": f"400 - endpoint exists: {resp_text}"})
        else:
            print(f"   ⚠ {status}  {name}")
            print(f"   Response: {resp_text}")

    except requests.exceptions.ConnectionError:
        print(f"   ✕ No response  {name}")
    except Exception as e:
        print(f"   ✕ Error: {e}  {name}")

# ============================================================
# Step 3: Result Summary
# ============================================================
print()
print("=" * 60)
print("RESULTS")
print("=" * 60)

if working:
    print(f"\n✅ {len(working)} endpoint(s) worked or responded:\n")
    for ep in working:
        note = ep.get("_note", "")
        print(f"  → Method: {ep['method']}")
        print(f"     URL:    {ep['url']}")
        if "body" in ep:
            print(f"     Body:   {ep['body'][:100]}")
        if note:
            print(f"     Note:   {note}")
        print()

    best = working[0]
    print("\n── Copy this to sms_alert.py ──")
    print(f"""
url     = "{best['url']}"
payload = {best.get('body', '{}')}
r = requests.{best['method'].lower()}(url, data=payload, headers={best.get('headers', {})}, timeout=10)
""")
else:
    print("\n❌ কোনো endpoint কাজ করেনি।")
    print()
    print("পরামর্শ:")
    print("  1. Android app-এ 'API Documentation' বা 'Help' দেখো")
    print("  2. App-এর নাম আর version আমাকে জানাও")
    print("  3. App screen-এ যদি কোনো API URL দেখায় সেটা note করো")
    print()
    print("Alternative:")
    print("  SMS Gateway URL সরাসরি browser-এ খোলো:")
    print(f"  → {BASE_URL}")
    print("  → কী দেখায় সেটা screenshot নাও বা copy করো")
