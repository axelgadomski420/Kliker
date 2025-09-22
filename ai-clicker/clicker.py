import os, time, random, logging, stripe, requests
from threading import Thread
from flask import Flask, jsonify, request
from huggingface_hub import InferenceClient

# Config
CLICK_RATE = float(os.getenv("CLICK_RATE", "0.20"))
NGINX_URL = os.getenv("NGINX_URL")
VPN_PATH = os.getenv("VPN_CONFIG_PATH")
HUG_TOKEN = os.getenv("HUG_TOKEN")

stripe.api_key = os.getenv("STRIPE_SECRET")
STRIPE_PUBLIC = os.getenv("STRIPE_PUBLIC")

# Stats
stats = {"imps": 0, "clicks": 0, "stripe_amount": 0}

# HuggingFace
hf_client = InferenceClient(token=HUG_TOKEN)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def simulate_ads():
    while True:
        # Simuluj 4-5 reklam jednocześnie
        for _ in range(random.randint(4,5)):
            stats["imps"] += 1
            if random.random() < CLICK_RATE:
                stats["clicks"] += 1
        time.sleep(5)

@app.route('/stats')
def get_stats():
    return jsonify(stats)

@app.route('/scan', methods=['POST'])
def magnet():
    # Burst 4-5 ads on demand
    for _ in range(random.randint(4,5)):
        stats["imps"] += 1
        if random.random() < CLICK_RATE:
            stats["clicks"] += 1
    return jsonify(stats)

@app.route('/stripe/create-payment', methods=['POST'])
def create_payment():
    data = request.json
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(data['amount']*100),
                'product_data': {'name':'Ad Boost'}
            },
            'quantity':1
        }],
        mode='payment',
        success_url=data['success_url'],
        cancel_url=data['cancel_url']
    )
    stats["stripe_amount"] += data['amount']
    return jsonify({"url": session.url})

@app.route('/explain')
def explain():
    prompt = "Explain this ad mining platform architecture and flow."
    response = hf_client.text_generation(prompt, model="mistralai/Mistral-7B-Instruct-v0.2", max_new_tokens=100)
    return jsonify({"description": response})

if __name__ == "__main__":
    Thread(target=simulate_ads, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
