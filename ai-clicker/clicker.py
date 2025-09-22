import os, time, random, threading, json, requests, stripe, logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or "sk_test_..."
SOURCE_ID = os.getenv("SOURCE_ID", "SRC_000")
PORT = int(os.getenv("PORT", "5000"))

# --- Global state ---
stats = {
    "imps": 0, "clicks": 0, "revenue": 0.0,
    "pending": 0, "last_charge": None,
    "last_update": datetime.now().isoformat()
}
ai_cfg = {"click_rate": 0.20, "interval": 3.0}
lock = threading.Lock()

LINKS_FILE = "links.json"
PROXIES = [
    "http://51.158.68.68:8811",
    "http://192.99.56.244:80",
    "http://45.77.24.239:8080"
]

# --- Helpers ---
def load_links():
    try:
        with open(LINKS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_links(links):
    with open(LINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)

def select_link(links):
    total = sum(l["weight"] for l in links)
    r = random.uniform(0, total)
    acc = 0
    for l in links:
        acc += l["weight"]
        if acc >= r:
            return l
    return random.choice(links) if links else None

# --- Scan loop ---
def scan_loop():
    while True:
        cpc = round(0.05 + random.random() * 0.15, 4)
        with lock:
            stats["imps"] += 1
            if random.random() < ai_cfg["click_rate"]:
                stats["clicks"] += 1
                stats["pending"] += int(cpc * 100)
                links = load_links()
                link = select_link(links)
                if link:
                    url = link["url"].replace("{SOURCE_ID}", SOURCE_ID).replace("{CLICK_ID}", str(stats["clicks"]))
                    proxy = {"http": random.choice(PROXIES), "https": random.choice(PROXIES)}
                    try:
                        r = requests.head(url, proxies=proxy, timeout=2)
                        payout = float(r.headers.get("X-Payout", cpc))
                    except Exception:
                        payout = cpc
                    link["weight"] = link["weight"] * 0.9 + payout * 0.1
                    save_links(links)
                    logging.info(f"Clicked {link['network']} → payout {payout}")
                if stats["clicks"] % 10 == 0 and stats["pending"] > 0:
                    try:
                        intent = stripe.PaymentIntent.create(
                            amount=stats["pending"],
                            currency="usd",
                            payment_method_types=["card"],
                            confirm=True,
                            payment_method="pm_card_visa"
                        )
                        stats["revenue"] += stats["pending"] / 100.0
                        stats["last_charge"] = {
                            "id": intent.id,
                            "amount": intent.amount / 100.0,
                            "time": datetime.now().isoformat()
                        }
                        stats["pending"] = 0
                        logging.info(f"Stripe charge succeeded: {stats['last_charge']}")
                    except Exception as e:
                        logging.error(f"Stripe error: {e}")
            stats["last_update"] = datetime.now().isoformat()
        time.sleep(ai_cfg["interval"])

# --- API routes ---
@app.route("/links", methods=["GET", "POST"])
def links_api():
    if request.method == "GET":
        return jsonify(load_links())
    data = request.get_json()
    links = load_links()
    new_id = (max(l["id"] for l in links) + 1) if links else 1
    new_link = {
        "id": new_id,
        "network": data["network"],
        "url": data["url"],
        "weight": 1.0
    }
    links.append(new_link)
    save_links(links)
    logging.info(f"Added link: {new_link}")
    return jsonify(new_link), 201

@app.route("/stats")
def get_stats():
    with lock:
        ctr = round(stats["clicks"] / max(stats["imps"], 1) * 100, 2)
        return jsonify({**stats, "ctr": ctr})

@app.route("/")
def dashboard():
    return open("web/index.html").read()

# --- Main ---
if __name__ == "__main__":
    threading.Thread(target=scan_loop, daemon=True).start()
    logging.info("🚀 AI Clicker started")
    app.run(host="0.0.0.0", port=PORT)
