from flask import Flask, request, jsonify
import requests
import threading
import time
import fraud_detection

app = Flask(__name__)

NEST_API = "http://localhost:3000"

@app.route('/track', methods=['POST'])
def track_click():
  """Receives click data and forwards it to NestJS."""
  user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
  if user_ip:
    user_ip = user_ip.split(',')[0].strip()

  data = request.json
  if not data.get("gclid"):
    return jsonify({"error": "No gclid found"}), 400

  click_data = {
    "gclid": data.get("gclid"),
    # "ip": user_ip,
    "ip": data.get("ip"),
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

if __name__ == '__main__':
  threading.Thread(target=schedule_fraud_detection, daemon=True).start()
  app.run(host='0.0.0.0', port=5000, debug=True)
