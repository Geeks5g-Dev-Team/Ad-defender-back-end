import requests
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
# from ipwhois import IPWhois

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
    
def get_user_by_ad_id(ad_id):
    """Finds the user who owns a given adId based on their Google Ads account."""
    response = requests.get(f"{NEST_API}/clicks?adId={ad_id}")  # Fetch click details
    if response.status_code != 200:
        print(f"❌ Failed to fetch click details for {ad_id}")
        return None

    click_data = response.json()
    if not click_data:
        print(f"⚠️ No click data found for adId: {ad_id}")
        return None

    google_account = click_data[0].get("googleAccount")  # Get Google Ads Customer ID from first matching click

    # Find the user who owns this Google Ads account
    user_response = requests.get(f"{NEST_API}/users?googleAccount={google_account}")
    if user_response.status_code == 200 and user_response.json():
        user = user_response.json()[0]  # Get the first matching user
        return user.get("id")  # Return userId
    return None

def mark_clicks_as_fraudulent(ip):
    """Marks all clicks from a flagged IP as fraudulent in the database and shows how many were updated."""
    response = requests.patch(f"{NEST_API}/clicks/mark-fraudulent/{ip}", json={"ip": ip})

    if response.status_code == 200:
        result = response.json()
        count = result.get("message", "").split(" ")[2]  # Extract number from response
        print(f"✅ Updated {count} click(s) as fraudulent for IP: {ip}.")
    else:
        print(f"❌ Failed to update clicks for {ip}: {response.status_code} - {response.text}")

def send_fraudulent_ip(ip, reason, clicks, ad_id):
    """Sends detected fraudulent IPs to NestJS for blocking with the correct userId."""
    user_id = get_user_by_ad_id(ad_id) or 1  # Default to admin if no user found

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
        mark_clicks_as_fraudulent(ip)
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

    # vpn_asn_list = [
    #     209093,  # Mullvad VPN
    #     39798,   # NordVPN
    #     52000,   # ProtonVPN
    #     200651,  # ExpressVPN
    #     46261,   # Private Internet Access (PIA)
    #     9009,    # M247 (used by many VPNs)
    #     16276,   # OVH SAS (many VPNs)
    #     32244,   # Liquid Web (Data center used by VPNs)
    #     13335,   # Cloudflare (often used for VPN proxying)
    #     39572,   # Performive (Data center that hosts VPN services)
    # ]

    # Step 2: Detect VPN Users Using ASN
    # for ip in df["ip"].unique():
    #     try:
    #         obj = IPWhois(ip)
    #         results = obj.lookup_rdap()
    #         asn_description = results.get("asn_description", "").lower()
    #         asn_number = results.get("asn")
    #         print(f"ASN Description for {ip}: {asn_description}")
    #         print(f"ASN Number for {ip}: {asn_number}")

    #         vpn_keywords = [
    #         "vpn", "proxy", "mullvad", "nordvpn", "expressvpn",
    #         "privateinternetaccess", "cyberghost", "surfshark",
    #         "hidemyass", "protonvpn", "ghostpath", "strongvpn"
    #         ]

    #         if any(keyword in asn_description for keyword in vpn_keywords):
    #             print(f"🚀 Immediate block: {ip} flagged as VPN user (ASN detection: {asn_description})")
    #             fraudulent_ips[ip] = "Detected VPN usage via ASN"
    #             continue
    #         if asn_number in vpn_asn_list:
    #             print(f"🚀 Immediate block: {ip} flagged as VPN user (ASN {asn_number})")
    #             fraudulent_ips[ip] = "Detected VPN usage via ASN"
    #             continue
    #     except Exception as e:
    #         print(f"⚠️ ASN lookup failed for {ip}: {e}")

    # Step 3: Too many clicks on the same ad
    repeated_clicks = df.groupby(["ip", "adId"]).size()
    for (ip, ad_id), count in repeated_clicks.items():
        if count >= MAX_CLICKS_PER_AD and ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for too many clicks on ad {ad_id}")
            fraudulent_ips[ip] = f"Clicked the same ad ({ad_id}) {count} times"
            continue  

    # Step 4: Short session duration
    short_sessions = df[(df["timestamp"] > time_threshold) & (df["sessionTime"] < MIN_SESSION_DURATION)]
    for ip in short_sessions["ip"].unique():
        if ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for short session duration")
            fraudulent_ips[ip] = "Short session duration detected"
            continue

    # Step 5: Clicking too frequently
    frequent_clicks = df[df["timestamp"] > time_threshold].groupby("ip").size()
    for ip, count in frequent_clicks.items():
        if count > FREQUENT_CLICKS_THRESHOLD and ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for clicking too frequently")
            fraudulent_ips[ip] = f"Clicked too frequently ({count} times in {TIME_WINDOW} mins)"
            continue

    # Step 6: Clicking multiple ads in the same campaign
    repeated_campaign_clicks = df.groupby(["ip", "campaignId"]).size()
    for (ip, campaign_id), count in repeated_campaign_clicks.items():
        if count >= MAX_CLICKS_PER_CAMPAIGN and ip not in blocked_ips and ip not in fraudulent_ips:
            print(f"🚀 Immediate block: {ip} flagged for multiple ads in campaign {campaign_id}")
            fraudulent_ips[ip] = f"Clicked multiple ads in the same campaign ({campaign_id}) {count} times"
            continue

    # If no new fraudulent IPs, show a different message
    if not fraudulent_ips:
        print("✅ No new fraudulent activity detected.")
        return {"message": "No new fraudulent activity detected."}

    # Report only new fraudulent IPs (avoid duplicates)
    for ip, reason in fraudulent_ips.items():
        clicks = df[df["ip"] == ip].shape[0]
        print(f"🚀 Sending {ip} to block list - Reason: {reason}")
        send_fraudulent_ip(ip, reason, clicks)

    print(f"🚨 New fraudulent IPs detected: {fraudulent_ips}")
    return {"fraudulent_ips": fraudulent_ips}

if __name__ == "__main__":
    detect_fraudulent_clicks()
