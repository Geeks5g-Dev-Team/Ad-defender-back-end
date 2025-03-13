import requests
from flask import session
from datetime import datetime

# Google OAuth & API Config
CLIENT_ID = "489689065901-tknvbdhgpbqihc5qnm0kt0hvsjfupbcr.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:5000/callback"
# REDIRECT_URI = "https://oauth.pstmn.io/v1/callback"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/adwords"
DEVELOPER_TOKEN="OOhmsVHUJh80WDKzdnAJaw"
NEST_API = "http://localhost:3000"

def get_google_auth_url():
    """Generates the Google OAuth 2.0 authorization URL."""
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        "response_type=code&"
        f"scope={SCOPE}&"
        "access_type=offline&"
        "prompt=consent"
    )
    return auth_url

def exchange_code_for_token(auth_code):
    """Exchanges authorization code for an access token."""
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        return response.json()  # Returns access_token & refresh_token
    else:
        print(f"❌ Failed to get access token: {response.text}")
        return None
    
def refresh_access_token(refresh_token):
    """Uses the refresh token to get a new access token."""
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        return response.json()  # Returns new access_token
    else:
        print(f"❌ Failed to refresh access token: {response.text}")
        return None
    
def get_valid_access_token():
    """Ensures a valid access token is available. Refreshes if expired."""
    access_token = session.get("access_token")
    refresh_token = session.get("refresh_token")

    if not access_token and refresh_token:
        print("🔄 Refreshing access token...")
        new_tokens = refresh_access_token(refresh_token)
        if new_tokens:
            session["access_token"] = new_tokens["access_token"]
            return new_tokens["access_token"]
        else:
            print("❌ Failed to refresh access token.")
            return None
    return access_token

def get_google_ads_customer_ids(access_token):
    """Fetches all accessible Google Ads Customer IDs."""
    url = "https://googleads.googleapis.com/v19/customers:listAccessibleCustomers"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": DEVELOPER_TOKEN
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        customer_ids = [cid.split("/")[-1] for cid in data.get("resourceNames", [])]

        if customer_ids:
            return customer_ids  # ✅ Return all customer IDs
        else:
            print("⚠️ No Google Ads Customer IDs found.")
            return []
    else:
        print(f"❌ Failed to fetch Customer IDs: {response.text}")
        return []

def update_user_google_account(id, google_account):
    """Update the user's Google Ads Customer ID in the database."""
    response = requests.patch(f"{NEST_API}/users/{id}", json={"googleAccount": google_account})

    if response.status_code == 200:
        return google_account
    else:
        print(f"❌ Failed to update user in database: {response.text}")
        return None

def get_google_ads_campaigns(access_token, customer_id):
    """Fetches campaigns for a selected Google Ads Customer ID within a date range."""
    url = f"https://googleads.googleapis.com/v19/customers/{customer_id}/googleAds:search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": DEVELOPER_TOKEN,
    }

    # ✅ Google Ads Query Language (GAQL) query with DATE FILTER
    query = f"""
        SELECT 
          campaign.id, 
          campaign.name, 
          campaign.status, 
          metrics.impressions, 
          metrics.clicks, 
          metrics.conversions, 
          metrics.cost_micros 
        FROM campaign 
        WHERE campaign.status = 'ENABLED'
    """

    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code == 200:
        data = response.json()
        def safe_int(value):
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        campaigns = []
        for row in data.get("results", []):
            clicks = safe_int(row["metrics"].get("clicks", 0))
            cost = safe_int(row["metrics"].get("costMicros", 0)) / 1_000_000  # Convert micros to currency
            cpc = round(cost / clicks, 2) if clicks > 0 else 0  # Avoid division by zero

            campaigns.append({
                "id": row["campaign"]["id"],
                "name": row["campaign"]["name"],
                "status": row["campaign"]["status"],
                "impressions": safe_int(row["metrics"].get("impressions", 0)),
                "clicks": clicks,
                "cost": cost,
                "cpc": cpc
            })
        return campaigns
    else:
        print(f"❌ Failed to fetch campaigns: {response.text}")
        return []
    
def get_google_ads_campaign_details(access_token, customer_id, campaign_id, start_date=None, end_date=None):
    """Fetches detailed metrics for a specific campaign within a date range."""
    url = f"https://googleads.googleapis.com/v19/customers/{customer_id}/googleAds:search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": DEVELOPER_TOKEN,
    }

    # ✅ Default to today's date if no range is provided
    today = datetime.today().strftime("%Y-%m-%d")
    start_date = start_date or today
    end_date = end_date or today

    query = f"""
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.start_date,
            campaign.end_date,
            campaign.bidding_strategy_type,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.cost_micros
        FROM campaign
        WHERE campaign.id = {campaign_id}
        AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    """

    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code == 200:
        data = response.json()
        def safe_int(value):
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

        if "results" in data and data["results"]:
            campaign = data["results"][0]["campaign"]  # Get the first result
            metrics = data["results"][0]["metrics"]

            clicks = safe_int(metrics.get("clicks", 0))
            cost = safe_int(metrics.get("costMicros", 0)) / 1_000_000  # Convert micros to currency
            cpc = round(cost / clicks, 2) if clicks > 0 else 0  # Avoid division by zero

            return {
                "id": campaign["id"],
                "name": campaign["name"],
                "status": campaign["status"],
                "start_date": campaign.get("startDate", "N/A"),
                "end_date": campaign.get("endDate", "N/A"),
                "bidding_strategy": campaign.get("biddingStrategyType", "Unknown"),
                "channel_type": campaign.get("advertisingChannelType", "Unknown"),
                "impressions": safe_int(metrics.get("impressions", 0)),
                "conversions": safe_int(metrics.get("conversions", 0)),
                "clicks": clicks,
                "cost": cost,
                "cpc": cpc  # ✅ Include CPC
            }
        else:
            print(f"⚠️ No data found for campaign {campaign_id}.")
            return None
    else:
        print(f"❌ Failed to fetch campaign details: {response.text}")
        return None

def get_overall_campaign_performance(access_token, customer_id, start_date=None, end_date=None):
    """Fetches overall performance metrics for campaigns within a date range."""
    url = f"https://googleads.googleapis.com/v19/customers/{customer_id}/googleAds:search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": DEVELOPER_TOKEN,
    }

    today = datetime.today().strftime("%Y-%m-%d")
    start_date = start_date or today
    end_date = end_date or today

    query = f"""
        SELECT 
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_micros
        FROM campaign
        WHERE campaign.status = 'ENABLED'
        AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    """

    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code == 200:
        data = response.json()
        def safe_int(value):
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

        # Aggregate overall performance
        total_impressions = sum(safe_int(row["metrics"].get("impressions", 0)) for row in data.get("results", []))
        total_clicks = sum(safe_int(row["metrics"].get("clicks", 0)) for row in data.get("results", []))
        total_conversions = sum(safe_int(row["metrics"].get("conversions", 0)) for row in data.get("results", []))
        total_cost_micros = sum(safe_int(row["metrics"].get("costMicros", 0)) for row in data.get("results", []))
        total_cost = total_cost_micros / 1_000_000  # Convert micros to currency units
        cpc = round(total_cost / total_clicks, 2) if total_clicks > 0 else 0  # Avoid division by zero

        return {
            "total_campaigns": len(data.get("results", [])),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_cost": total_cost,
            "cpc": cpc
        }
    else:
        print(f"❌ Failed to fetch overall performance: {response.text}")
        return None