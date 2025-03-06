import requests
import time
import uuid
from datetime import datetime, timezone
from fraud_detection import detect_fraudulent_clicks, fetch_blocked_ips

# NestJS API URL
NEST_API = "http://localhost:3000"

def generate_gclid():
    """Generates a unique Google Click ID (gclid) for each click."""
    return str(uuid.uuid4())

def insert_test_clicks():
    """Inserts test click data into the real database."""
    now = datetime.now(timezone.utc).isoformat()

    test_clicks = [
        {"gclid": generate_gclid(), "ip": "192.168.1.1", "adId": "ad_123", "campaignId": "camp_1", "userAgent": "Mozilla", "timestamp": now},
        {"gclid": generate_gclid(), "ip": "192.168.1.1", "adId": "ad_123", "campaignId": "camp_1", "userAgent": "Mozilla", "timestamp": now},
        {"gclid": generate_gclid(), "ip": "192.168.1.1", "adId": "ad_123", "campaignId": "camp_1", "userAgent": "Mozilla", "timestamp": now},

        {"gclid": generate_gclid(), "ip": "203.0.113.5", "adId": "ad_456", "campaignId": "camp_2", "userAgent": "Googlebot", "timestamp": now},

        {"gclid": generate_gclid(), "ip": "198.51.100.10", "adId": "ad_789", "campaignId": "camp_3", "userAgent": "Mozilla", "timestamp": now, "sessionTime": 2}
    ]

    # Append dynamically generated test clicks
    test_clicks += [
        {"gclid": generate_gclid(), "ip": "203.0.113.10", "adId": f"ad_{i}", "campaignId": "camp_1", "userAgent": "Mozilla", "timestamp": now}
        for i in range(6)
    ]

    for click in test_clicks:
        response = requests.post(f"{NEST_API}/clicks", json=click)
        if response.status_code != 201:
            print(f"❌ Failed to insert test click: {click}")
        time.sleep(0.5)  # Avoid rate-limiting issues

    print("✅ Test clicks inserted successfully.")

def check_blocked_ips(expected_fraud):
    """Fetches blocked IPs and validates if the correct ones were blocked."""
    time.sleep(2)  # Give some time for fraud detection to process
    blocked_ips = fetch_blocked_ips()

    detected_fraud = {ip: expected_fraud[ip] for ip in blocked_ips if ip in expected_fraud}

    if detected_fraud == expected_fraud:
        print("✅ All expected fraudulent IPs were blocked correctly!")
    else:
        print(f"❌ Test Failed! Expected: {expected_fraud}, Got: {detected_fraud}")

def test_fraud_detection_real_db():
    """Runs fraud detection tests on the real database."""
    print("🚀 Running Fraud Detection Tests on Real DB...")

    # Expected fraud reasons
    expected_fraud = {
        "192.168.1.1": "Clicked the same ad (ad_123) 3 times",
        "203.0.113.5": "Detected bot-like user-agent",
        "198.51.100.10": "Short session duration detected",
        "203.0.113.10": "Clicked too frequently (6 times in 10 mins)"
    }

    # Step 1: Insert test clicks
    insert_test_clicks()

    # Step 2: Run fraud detection
    detect_fraudulent_clicks()

    # Step 3: Check blocked IPs
    check_blocked_ips(expected_fraud)

if __name__ == "__main__":
    test_fraud_detection_real_db()
