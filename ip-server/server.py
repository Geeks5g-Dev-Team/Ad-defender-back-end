from flask import Flask, request, jsonify, redirect, render_template_string, session
from flask_cors import CORS
from flask_session import Session
import requests
import threading
import time
import fraud_detection
from google_ads_service import (
  get_google_auth_url,
  exchange_code_for_token,
  get_google_ads_customer_ids,
  get_overall_campaign_performance,
  update_user_google_account,
  get_google_ads_campaigns,
  get_valid_access_token
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key_here"  # 🔥 Ensure this is set!
app.config["SESSION_TYPE"] = "filesystem"  # ✅ Store session on disk
app.config["SESSION_PERMANENT"] = True  # ✅ Keep session after browser closes
app.config["SESSION_USE_SIGNER"] = True  # ✅ Prevent session tampering
app.config["SESSION_COOKIE_SECURE"] = False  # ✅ Change to True in production
Session(app)
CORS(app)

NEST_API = "http://localhost:3000"

CLIENT_ID = "489689065901-tknvbdhgpbqihc5qnm0kt0hvsjfupbcr.apps.googleusercontent.com"
REDIRECT_URI = "https://oauth.pstmn.io/v1/callback"
SCOPE = "https://www.googleapis.com/auth/adwords"

TOKENS_STORE = {}

def get_location_from_ip(ip):
  """Fetches the location of an IP address using ip-api.com."""
  if not ip or ip == "127.0.0.1":
    return {"error": "Invalid or local IP"}

  url = f"http://ip-api.com/json/{ip}"
  try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data.get("status") == "success":
        return {
          "lat": data.get("lat"),
          "lon": data.get("lon"),
          "city": data.get("city"),
          "region": data.get("regionName"),
          "country": data.get("country"),
        }
    else:
      return {"error": data.get("message", "Location not found")}
  except requests.exceptions.RequestException as e:
    return {"error": str(e)}

@app.route('/track', methods=['POST'])
def track_click():
  """Receives click data and forwards it to NestJS."""
  user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
  if user_ip:
    user_ip = user_ip.split(',')[0].strip()
    location = get_location_from_ip("8.8.8.8")
    print(location)

  data = request.json
  if not data.get("gclid"):
    return jsonify({"error": "No gclid found"}), 400

  click_data = {
    "gclid": data.get("gclid"),
    # "ip": user_ip,
    "ip": data.get("ip"),
    "customerId": data.get("customerId"),
    "location": location,
    "userAgent": data.get("userAgent"),
    "referrer": data.get("referrer"),
    "adId": data.get("adId"),
    "adGroupId": data.get("adGroupId"),
    "campaignId": data.get("campaignId"),
    "sessionTime": data.get("sessionTime")
  }

  clean_click_data = {k: v for k, v in click_data.items() if v is not None}
  response = requests.post(f"{NEST_API}/clicks", json=clean_click_data)
  return response.json()

@app.route('/detect-fraud', methods=['GET'])
def run_fraud_detection():
  """API to manually trigger fraud detection."""
  fraud_ips = fraud_detection.detect_fraudulent_clicks()
  return {"fraudulent_ips": fraud_ips}

# Run fraud detection every 10 minutes
def schedule_fraud_detection():
  while True:
    fraud_detection.detect_fraudulent_clicks()
    time.sleep(60)  # 10 minutes

@app.route("/google-auth")
def google_auth():
    """Redirects the user to Google's OAuth 2.0 authorization page."""
    return redirect(get_google_auth_url())

@app.route("/callback")
def google_callback():
  """Handles OAuth 2.0 callback and exchanges authorization code for access token."""
  auth_code = request.args.get("code")
  print(f"🔑 Received auth code: {auth_code}")

  tokens = exchange_code_for_token(auth_code)
  if not tokens:
    return jsonify({"error": "Failed to get access token"}), 400

  print(f"🔑 Received tokens: {tokens}")
  access_token = tokens["access_token"]
  refresh_token = tokens.get("refresh_token")  # Optional for long-term access

  session["access_token"] = access_token
  session["refresh_token"] = refresh_token
  session.modified = True

  print("-----------",session.get("access_token"))
  print("-----------",session.get("refresh_token"))

  TOKENS_STORE["access_token"] = access_token
  TOKENS_STORE["refresh_token"] = refresh_token

  # ✅ Fetch Google Ads Customer ID
  customer_ids = get_google_ads_customer_ids(access_token)

  if not customer_ids:
    return jsonify({"error": "No Google Ads accounts found"}), 400

  return render_template_string(
    """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Google Ads Connected</title>
        <script>
            window.opener.postMessage({ 
                message: "Google Ads Connected!", 
                customer_ids: {{ customer_ids | tojson }} 
            }, "*");
            window.close();
        </script>
    </head>
    <body>
        <h2>✅ Google Ads Account Connected!</h2>
        <p>You can now close this window.</p>
    </body>
    </html>
    """,
    customer_ids=customer_ids
  )

@app.route("/select-customer-id", methods=["POST"])
def select_customer_id():
  """Stores the selected Google Ads Customer ID in the database."""
  data = request.json
  selected_customer_id = data.get("customerId")
  id = data.get("id")

  if not selected_customer_id:
    return jsonify({"error": "Invalid Customer ID selected"}), 400
  
  update_user_google_account(id, selected_customer_id)

  return jsonify({
    "message": "Google Ads Customer ID stored successfully",
    "selected_customer_id": selected_customer_id
  })

@app.route("/get-campaigns", methods=["POST"])
def get_campaigns():
    """Retrieves campaigns for the selected Google Ads Customer ID."""
    data = request.json
    customer_id = data.get("customerId")

    if not customer_id:
      return jsonify({"error": "Customer ID is required"}), 400

    # ✅ Ensure access token is valid
    # access_token = get_valid_access_token()
    access_token = TOKENS_STORE.get("access_token")
    print(f"🔑 Retrieved access token: {access_token}")
    if not access_token or access_token == None:
      return jsonify({"error": "Session expired, please re-authenticate"}), 401
    
    # ✅ Fetch campaigns
    campaigns = get_google_ads_campaigns(access_token, customer_id)
    return jsonify({"campaigns": campaigns})

@app.route("/get-overall-performance", methods=["POST"])
def get_overall_performance():
    """Retrieves overall performance metrics for all campaigns."""
    data = request.json
    customer_id = data.get("customerId")

    if not customer_id:
      return jsonify({"error": "Customer ID is required"}), 400

    # ✅ Ensure access token is valid
    # access_token = session.get("access_token")
    access_token = TOKENS_STORE.get("access_token")
    if not access_token:
      return jsonify({"error": "Session expired, please re-authenticate"}), 401

    # ✅ Fetch overall campaign performance
    performance = get_overall_campaign_performance(access_token, customer_id)

    if performance:
      return jsonify({"performance": performance})
    else:
      return jsonify({"error": "Failed to retrieve campaign performance"}), 500

if __name__ == '__main__':
  threading.Thread(target=schedule_fraud_detection, daemon=True).start()
  app.run(host='0.0.0.0', port=5000, debug=True)
