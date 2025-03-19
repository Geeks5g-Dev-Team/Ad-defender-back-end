from flask import session
import requests
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
from google_ads_service import block_ips_in_google_ads

# NestJS API URL
NEST_API = "http://localhost:3000"

# Define fraud detection thresholds
MAX_CLICKS_PER_AD = 3
MAX_CLICKS_PER_CAMPAIGN = 10
TIME_WINDOW = 10  # Time window in minutes
BOT_USER_AGENTS = [
    "bot", "spider", "crawl", "curl", "wget", "Googlebot", "Bingbot", "Yahoo! Slurp",
    "DuckDuckBot", "Baiduspider", "YandexBot", "facebookexternalhit", "Applebot",
    "MJ12bot", "AhrefsBot", "SemrushBot", "Python-urllib"
]
MIN_SESSION_DURATION = 5
FREQUENT_CLICKS_THRESHOLD = 5

def fetch_clicks():
    """Fetches all clicks from NestJS API."""
    response = requests.get(f"{NEST_API}/clicks")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch clicks: {response.status_code}")
        return []

def fetch_blocked_ips():
    """Fetches already blocked IPs from NestJS API to prevent re-blocking."""
    response = requests.get(f"{NEST_API}/blocked-ips")
    if response.status_code == 200:
        blocked_ips = [entry["ip"] for entry in response.json()]
        return set(blocked_ips)  # Convert to set for faster lookups
    else:
        print(f"❌ Failed to fetch blocked IPs: {response.status_code}")
        return set()

def get_user_by_customer_id(customer_id):
    """Finds the user who owns a given Google Ads Customer ID."""
    response = requests.get(f"{NEST_API}/users?googleAccount={customer_id}")
    if response.status_code == 200 and response.json():
        user = response.json()
        return user.get("id")  # Return userId
    return None

def send_fraudulent_ip(ip, reason, clicks, customer_id):
    """Sends detected fraudulent IPs to NestJS for blocking with the correct userId."""
    user_id = get_user_by_customer_id(customer_id) or 1  # Default to admin if no user found

    data = {
        "userId": user_id,  # ✅ Assign correct userId dynamically
        "ip": ip,
        "reason": reason,
        "threatLevel": "high",
        "clicks": clicks,
        "moneySaved": clicks * 0.5
    }

    response = requests.post(f"{NEST_API}/blocked-ips", json=data)
    if response.status_code == 201:
        print(f"✅ Successfully blocked {ip} for user {user_id} - Reason: {reason}")
    else:
        print(f"❌ Failed to block {ip}: {response.status_code} - {response.text}")

def detect_fraudulent_clicks():
    """Detects fraudulent click patterns and immediately flags an IP after the first detected rule."""
    clicks = fetch_clicks()
    if not clicks:
        print("✅ No clicks to analyze.")
        return {"message": "No clicks available for analysis."}

    df = pd.DataFrame(clicks)
    if df.empty:
        print("✅ No clicks to analyze.")
        return {"message": "No clicks available for analysis."}

    blocked_ips = fetch_blocked_ips()
    print(f"\n🔍 Already blocked IPs: {blocked_ips}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    now = datetime.now(timezone.utc)
    time_threshold = now - timedelta(minutes=TIME_WINDOW)

    fraudulent_ips = {}

    # Step 1: Detect bot user-agents FIRST
    bot_pattern = "|".join(map(re.escape, BOT_USER_AGENTS))
    df["is_bot"] = df["userAgent"].astype(str).str.contains(bot_pattern, case=False, na=False)

    for ip in df[df["is_bot"]]["ip"].unique():
        if ip not in blocked_ips:
            print(f"🚀 Immediate block: {ip} flagged as bot")
            fraudulent_ips[ip] = "Detected bot-like user-agent"
            continue

    # Step 2: Too many clicks on the same ad
    repeated_clicks = df.groupby(["ip", "adId"]).size()
    for (ip, ad_id), count in repeated_clicks.items():
        if count >= MAX_CLICKS_PER_AD and ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for too many clicks on ad {ad_id}")
            fraudulent_ips[ip] = f"Clicked the same ad ({ad_id}) {count} times"
            continue  

    # Step 3: Short session duration
    short_sessions = df[(df["timestamp"] > time_threshold) & (df["sessionTime"] < MIN_SESSION_DURATION)]
    for ip in short_sessions["ip"].unique():
        if ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for short session duration")
            fraudulent_ips[ip] = "Short session duration detected"
            continue

    # Step 4: Clicking too frequently
    frequent_clicks = df[df["timestamp"] > time_threshold].groupby("ip").size()
    for ip, count in frequent_clicks.items():
        if count > FREQUENT_CLICKS_THRESHOLD and ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for clicking too frequently")
            fraudulent_ips[ip] = f"Clicked too frequently ({count} times in {TIME_WINDOW} mins)"
            continue

    # Step 5: Clicking multiple ads in the same campaign
    repeated_campaign_clicks = df.groupby(["ip", "campaignId"]).size()
    for (ip, campaign_id), count in repeated_campaign_clicks.items():
        if count >= MAX_CLICKS_PER_CAMPAIGN and ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for multiple ads in campaign {campaign_id}")
            fraudulent_ips[ip] = f"Clicked multiple ads in the same campaign ({campaign_id}) {count} times"
            continue

    # Step 6: Report fraudulent IPs per advertiser
    if not fraudulent_ips:
        print("✅ No new fraudulent activity detected.")
        return {"message": "No new fraudulent activity detected."}

    for ip, reason in fraudulent_ips.items():
        user_clicks = df[df["ip"] == ip]
        customer_id = user_clicks["customerId"].iloc[0] if "customerId" in df.columns else None
        clicks = len(user_clicks)

        if customer_id:
            print(f"🚀 Sending {ip} to block list for customer {customer_id} - Reason: {reason}")
            send_fraudulent_ip(ip, reason, clicks, customer_id)

            # ✅ Block the IP in Google Ads
            access_token = session.get("access_token")
            if access_token:
                block_ips_in_google_ads(access_token, customer_id, [ip])
            else:
                print(f"⚠️ Skipping Google Ads IP block for {ip} due to missing access token.")
        else:
            print(f"⚠️ No customer ID found for {ip}, skipping block.")

    print(f"🚨 New fraudulent IPs detected: {fraudulent_ips}")
    return {"fraudulent_ips": fraudulent_ips}

if __name__ == "__main__":
    detect_fraudulent_clicks()
