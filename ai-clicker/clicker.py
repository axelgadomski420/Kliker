import os
import glob
import random
import subprocess
import time
import logging
import stripe
import requests
from threading import Thread
from flask import Flask, jsonify, request
from huggingface_hub import InferenceClient

# ——————————————————————————————
# KONFIGURACJA ŚRODOWISKOWA
# ——————————————————————————————
CLICK_RATE    = float(os.getenv("CLICK_RATE", "0.20"))           # 20% click rate
NGINX_URL     = os.getenv("NGINX_URL", "http://localhost:80")   # URL nginx-proxy
HUG_TOKEN     = os.getenv("HUG_TOKEN")                          # Twój token HuggingFace
STRIPE_SECRET = os.getenv("STRIPE_SECRET")                      # Stripe secret key
STRIPE_PUBLIC = os.getenv("STRIPE_PUBLIC")                      # Stripe public key

# ——————————————————————————————
# INICJALIZACJA
# ——————————————————————————————
stripe.api_key = STRIPE_SECRET
hf_client       = InferenceClient(token=HUG_TOKEN)
app             = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ——————————————————————————————
# STATYSTYKI
# ——————————————————————————————
stats = {
    "imps"          : 0,
    "clicks"        : 0,
    "stripe_amount" : 0
}

# ——————————————————————————————
# FUNKCJA URUCHAMIAJĄCA VPN (losowy plik .ovpn)
# ——————————————————————————————
def start_vpn():
    ovpns = glob.glob("/vpnbook/*.ovpn")
    auth  = "/vpnbook/auth.txt"
    if not ovpns or not os.path.isfile(auth):
        logging.error("Brak plików .ovpn lub auth.txt")
        return
    choice = random.choice(ovpns)
    logging.info(f"Łączenie VPN z: {choice}")
    subprocess.Popen([
        "openvpn",
        "--config", choice,
        "--auth-user-pass", auth
    ])
    # Poczekaj aż VPN się połączy
    time.sleep(10)

# ——————————————————————————————
# CLICKER: Generowanie reklam co 5 sekund, 4–5 jednocześnie
# ——————————————————————————————
def simulate_ads():
    while True:
        for _ in range(random.randint(4,5)):
            stats["imps"] += 1
            if random.random() < CLICK_RATE:
                stats["clicks"] += 1
        logging.info(f"Stats: imps={stats['imps']} clicks={stats['clicks']}")
        time.sleep(5)

# ——————————————————————————————
# ENDPOINTS FLASK
# ——————————————————————————————
@app.route("/stats")
def get_stats():
    return jsonify(stats)

@app.route("/scan", methods=["POST"])
def scan_now():
    # burst 4–5 reklam on demand
    for _ in range(random.randint(4,5)):
        stats["imps"] += 1
        if random.random() < CLICK_RATE:
            stats["clicks"] += 1
    return jsonify(stats)

@app.route("/stripe/create-payment", methods=["POST"])
def create_payment():
    data = request.json or {}
    amount     = data.get("amount", 0.0)
    success_url = data.get("success_url", request.host_url)
    cancel_url  = data.get("cancel_url", request.host_url)
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency"   : "usd",
                "unit_amount": int(amount * 100),
                "product_data": {"name":"Ad Boost"}
            },
            "quantity": 1
        }],
        mode          = "payment",
        success_url   = success_url,
        cancel_url    = cancel_url
    )
    stats["stripe_amount"] += amount
    return jsonify({"url": session.url})

@app.route("/explain")
def explain_system():
    prompt = ("Explain how this ad-mining platform works: VPN, nginx-proxy, "
              "AI clicker, Stripe payments, and dashboard.")
    response = hf_client.text_generation(
        prompt,
        model="mistralai/Mistral-7B-Instruct-v0.2",
        max_new_tokens=100
    )
    return jsonify({"description": response})

# ——————————————————————————————
# URUCHAMIAMY APLIKACJĘ
# ——————————————————————————————
if __name__ == "__main__":
    # 1. Start VPN w tle
    Thread(target=start_vpn, daemon=True).start()
    # 2. Start symulacji reklam w tle
    Thread(target=simulate_ads, daemon=True).start()
    # 3. Start Flask API
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
