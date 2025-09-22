import os
import json
import time
import random
import threading
import requests
import stripe
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# ---------------- Init ------------------
load_dotenv()
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY") or "sk_test_..."
stripe.api_key = STRIPE_SECRET_KEY

SOURCE_ID = os.getenv("SOURCE_ID", "SRC_001")
PORT = int(os.getenv("PORT", "5000"))

# ---------------- Globals -----------------
stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending_amount": 0,
    "last_charge": None,
    "last_update": datetime.now().isoformat()
}

ai_config = {
    "click_rate": float(os.getenv("CLICK_RATE", "0.20")),
    "interval": 3.0,
    "expensive_mode": False,
    "turbo_mode": False,
    "stealth_mode": True,
    "min_rate": 0.05,
    "max_rate": 0.80,
    "history": [],
    "achievements": [],
    "milestones": [10, 50, 100, 250, 500, 1000],
    "proxy_rotation": True,
    "smart_timing": True
}

lock = threading.Lock()

LINKS_FILE = "links.json"
PROXIES = [
    "http://51.158.68.68:8811",
    "http://192.99.56.244:80",
    "http://45.77.24.239:8080"
]

# ---------------- Helpers -----------------
def load_links():
    try:
        with open(LINKS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_links(links):
    with open(LINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)

def get_random_proxy():
    if not ai_config["proxy_rotation"]:
        return None
    p = random.choice(PROXIES)
    return {"http": p, "https": p}

def fetch_cpc():
    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random.randint(537,539)}.36"
    }
    try:
        proxy = get_random_proxy()
        # simulate an API call to get cpc
        r = requests.get("https://httpbin.org/json", proxies=proxy, headers=headers, timeout=3)
        return round(0.05 + random.random()*0.15, 4)
    except Exception as e:
        logging.warning(f"CPC fetch failed: {e}")
        return ai_config["click_rate"]

def smart_timing_multiplier():
    if not ai_config["smart_timing"]:
        return 1.0
    h = datetime.now().hour
    if 6 <= h <= 9 or 18 <= h <= 23:
        return 1.5
    if 0 <= h <= 5:
        return 0.7
    return 1.0

def check_achievements():
    new_achievements = []
    for m in ai_config["milestones"][:]:
        if stats["revenue"] >= m:
            new_achievements.append(f"💰 Revenue milestone reached: ${m}")
            ai_config["milestones"].remove(m)
    # Other achievements
    if stats["clicks"] >= 100 and "Century Club" not in ai_config["achievements"]:
        new_achievements.append("🎯 Century Club: 100 clicks!")
        ai_config["achievements"].append("Century Club")
    if stats["imps"] >= 1000 and "Impression Master" not in ai_config["achievements"]:
        new_achievements.append("👁️ Impression Master: 1000 impressions")
        ai_config["achievements"].append("Impression Master")
    return new_achievements

def select_affiliate_link(links):
    total_weight = sum(l.get("weight", 1.0) for l in links)
    r = random.uniform(0, total_weight)
    accumulator = 0
    for l in links:
        accumulator += l.get("weight", 1.0)
        if accumulator >= r:
            return l
    return random.choice(links) if links else None

# ---------------- Core Engine -----------------
def premium_scan_worker(worker_id):
    logging.info(f"Worker {worker_id} started")
    while True:
        cpc = fetch_cpc()
        multiplier = smart_timing_multiplier()
        weight_click_rate = ai_config["click_rate"] * multiplier
        with lock:
            stats["imps"] += 1
            effective_rate = weight_click_rate
            if ai_config["expensive_mode"]:
                effective_rate *= 2.0
            if ai_config["turbo_mode"]:
                effective_rate *= 1.5
            if ai_config["stealth_mode"]:
                effective_rate *= random.uniform(0.8, 1.2)
            
            if random.random() < min(effective_rate, 0.95):
                stats["clicks"] += 1
                stats["pending_amount"] += int(cpc * 100)
                # Handle affiliate links
                links = load_links()
                if links:
                    chosen_link = select_affiliate_link(links)
                    affiliate_url = chosen_link["url"].replace("{SOURCE_ID}", SOURCE_ID).replace("{CLICK_ID}", str(stats["clicks"]))
                    proxy = get_random_proxy()
                    try:
                        resp = requests.head(affiliate_url, proxies=proxy, timeout=3)
                        payout = float(resp.headers.get("X-Payout", cpc))
                        # Update link weight sliding average
                        chosen_link["weight"] = chosen_link.get("weight", 1.0)*0.9 + payout*0.1
                        save_links(links)
                        logging.info(f"Worker-{worker_id} clicked link [{chosen_link['network']}], payout {payout:.4f}")
                    except Exception as e:
                        logging.warning(f"Worker-{worker_id} failed to access link: {e}")
            
            # Create Stripe payment every 10 clicks
            if stats["clicks"] % 10 == 0 and stats["pending_amount"] > 0:
                try:
                    intent = stripe.PaymentIntent.create(
                        amount=stats["pending_amount"],
                        currency="usd",
                        payment_method_types=["card"],
                        confirm=True,
                        payment_method="pm_card_visa"
                    )
                    stats["revenue"] += stats["pending_amount"] / 100.0
                    stats["last_charge"] = {
                        "id": intent.id,
                        "amount": intent.amount / 100.0,
                        "time": datetime.now().isoformat()
                    }
                    stats["pending_amount"] = 0
                    logging.info(f"Stripe payment succeeded: {stats['last_charge']}")
                except Exception as e:
                    logging.error(f"Stripe payment failed: {e}")

            stats["last_update"] = datetime.now().isoformat()
            ai_config["history"].append(stats["revenue"])
            if len(ai_config["history"]) > 50:
                ai_config["history"].pop(0)
            achievements = check_achievements()
            for a in achievements:
                logging.info(f"Achievement unlocked: {a}")
        
        time.sleep(ai_config["interval"] * random.uniform(0.8, 1.2))

# ---------------- Flask routes -----------------
@app.route("/links", methods=["GET","POST"])
def manage_links():
    if request.method == "GET":
        return jsonify(load_links())
    data = request.get_json()
    if not data or "network" not in data or "url" not in 
        return jsonify({"error": "Missing network or url"}), 400
    
    links = load_links()
    new_id = max([l["id"] for l in links], default=0) + 1
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

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    
    with lock:
        if action == "toggle_expensive":
            ai_config["expensive_mode"] = not ai_config["expensive_mode"]
            return jsonify({"expensive_mode": ai_config["expensive_mode"], "message": "💎 Expensive mode toggled!"})
        if action == "toggle_turbo":
            ai_config["turbo_mode"] = not ai_config["turbo_mode"]
            return jsonify({"turbo_mode": ai_config["turbo_mode"], "message": "🚀 Turbo mode toggled!"})
        if action == "toggle_stealth":
            ai_config["stealth_mode"] = not ai_config["stealth_mode"]
            return jsonify({"stealth_mode": ai_config["stealth_mode"], "message": "🥷 Stealth mode toggled!"})
        if action == "set_click_rate":
            try:
                val = float(data.get("value", ai_config["click_rate"]))
                ai_config["click_rate"] = min(max(val, ai_config["min_rate"]), ai_config["max_rate"])
                return jsonify({"click_rate": ai_config["click_rate"], "message": f"📈 Click rate set to {ai_config['click_rate']}"})
            except Exception as e:
                return jsonify({"error": "Invalid click rate value"}), 400
        if action == "boost":
            stats["revenue"] += 10.0
            return jsonify({"revenue": stats["revenue"], "message": "💰 Boost +$10!"})
        if action == "reset":
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending_amount": 0})
            ai_config["history"].clear()
            return jsonify({"message": "🔄 Stats reset!", **stats})
        return jsonify({"error": "Unknown command"}), 400

@app.route("/scan", methods=["POST"])
def manual_scan():
    with lock:
        stats["imps"] += 3
        cpc = fetch_cpc()
        bonus_rate = ai_config["click_rate"] * 2.5
        if random.random() < bonus_rate:
            stats["clicks"] += random.randint(1, 3)
            stats["pending_amount"] += int(cpc * 100)
        stats["last_update"] = datetime.now().isoformat()
    return jsonify(stats)

@app.route("/")
def dashboard():
    return open("web/index.html").read()

# ---------------- Main -----------------
if __name__ == "__main__":
    logging.info("🚀 Starting AI Clicker Engine...")
    workers = []
    for i in range(4):
        t = threading.Thread(target=premium_scan_worker, args=(i+1,), daemon=True)
        t.start()
        workers.append(t)
        logging.info(f"Started worker-{i+1}")
    app.run(host="0.0.0.0", port=PORT)
