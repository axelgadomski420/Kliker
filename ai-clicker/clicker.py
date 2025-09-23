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

# Inicjalizacja
load_dotenv()
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
SOURCE_ID = os.getenv("SOURCE_ID", "SRC_000")
PORT = int(os.getenv("PORT", "5000"))
DEFAULT_CLICK_RATE = float(os.getenv("CLICK_RATE", "0.20"))

stats = {
    "imps": 0, "clicks": 0, "revenue": 0.0,
    "pending": 0, "last_charge": None,
    "last_update": datetime.now().isoformat()
}

ai_cfg = {
    "click_rate": DEFAULT_CLICK_RATE,
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
    "smart_timing": True,
}

lock = threading.Lock()
LINKS_FILE = "links.json"

# Stabilne proxy
PROXIES = [
    "http://139.59.59.240:8080",
    "http://134.209.29.120:3128"
]

def load_links():
    try:
        with open(LINKS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_links(links):
    with open(LINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)

def get_proxy():
    if not ai_cfg["proxy_rotation"]:
        return None
    proxy_url = random.choice(PROXIES)
    return {"http": proxy_url, "https": proxy_url}

def fetch_cpc():
    try:
        headers = {"User-Agent": f"Mozilla/5.0 AppleWebKit/{random.randint(537,539)}.36"}
        requests.get("https://httpbin.org/get", proxies=get_proxy(), headers=headers, timeout=3)
        return round(0.05 + random.random()*0.15, 4)
    except Exception as e:
        logging.warning(f"CPC fetch failed with proxy: {e}")
        return ai_cfg["click_rate"]

def smart_timing_multiplier():
    if not ai_cfg["smart_timing"]:
        return 1.0
    h = datetime.now().hour
    if 6 <= h <= 9 or 18 <= h <= 23:
        return 1.5
    if 0 <= h <= 5:
        return 0.7
    return 1.0

def check_achievements():
    new = []
    for m in ai_cfg["milestones"][:]:
        if stats["revenue"] >= m:
            new.append(f"💰 Milestone: ${m}")
            ai_cfg["milestones"].remove(m)
    if stats["clicks"] >= 100 and "Century Club" not in ai_cfg["achievements"]:
        new.append("🎯 Century Club: 100 clicks")
        ai_cfg["achievements"].append("Century Club")
    if stats["imps"] >= 1000 and "Impression Master" not in ai_cfg["achievements"]:
        new.append("👁️ Impression Master: 1000 imps")
        ai_cfg["achievements"].append("Impression Master")
    return new

def select_affiliate_link(links):
    total = sum(l.get("weight",1.0) for l in links)
    r = random.uniform(0, total)
    acc = 0
    for l in links:
        acc += l.get("weight",1.0)
        if acc >= r:
            return l
    return random.choice(links) if links else None

def ai_scan_worker(worker_id):
    logging.info(f"Worker-{worker_id} started")
    while True:
        cpc = fetch_cpc()
        mult = smart_timing_multiplier()
        with lock:
            stats["imps"] += 1
            rate = ai_cfg["click_rate"] * mult
            if ai_cfg["expensive_mode"]: rate *= 2.0
            if ai_cfg["turbo_mode"]: rate *= 1.5
            if ai_cfg["stealth_mode"]: rate *= random.uniform(0.8, 1.2)

            if random.random() < min(rate, 0.95):
                stats["clicks"] += 1
                stats["pending"] += int(cpc * 100)

                links = load_links()
                ln = select_affiliate_link(links)
                if ln:
                    url = ln["url"].replace("{SOURCE_ID}", SOURCE_ID).replace("{CLICK_ID}", str(stats["clicks"]))
                    try:
                        r = requests.head(url, proxies=get_proxy(), timeout=3)
                        payout = float(r.headers.get("X-Payout", cpc))
                    except:
                        payout = cpc
                    ln["weight"] = ln.get("weight", 1.0) * 0.9 + payout * 0.1
                    save_links(links)
                    logging.info(f"Worker-{worker_id} clicked {ln['network']} payout={payout}")

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
                        logging.info(f"Stripe OK: {stats['last_charge']}")
                    except Exception as e:
                        logging.error(f"Stripe ERROR: {e}")

            stats["last_update"] = datetime.now().isoformat()
            ai_cfg["history"].append(stats["revenue"])
            if len(ai_cfg["history"]) > 50:
                ai_cfg["history"].pop(0)
            for a in check_achievements():
                logging.info(f"Achievement: {a}")

        time.sleep(ai_cfg["interval"] * random.uniform(0.8,1.2))

@app.route("/links", methods=["GET", "POST"])
def links_api():
    if request.method == "GET":
        return jsonify(load_links())

    data = request.get_json()
    if not data or "network" not in data or "url" not in data:
        return jsonify({"error": "network i url wymagane"}), 400

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
    logging.info(f"Dodano link: {new_link}")
    return jsonify(new_link), 201

@app.route("/stats")
def stats_api():
    with lock:
        ctr = round(stats["clicks"] / max(stats["imps"],1) * 100, 2)
        return jsonify({**stats,"ctr": ctr})

@app.route("/command", methods=["POST"])
def command_api():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    with lock:
        if action == "toggle_expensive":
            ai_cfg["expensive_mode"] = not ai_cfg["expensive_mode"]
            return jsonify({"expensive_mode": ai_cfg["expensive_mode"], "message":"💎 Expensive toggled"})
        if action == "toggle_turbo":
            ai_cfg["turbo_mode"] = not ai_cfg["turbo_mode"]
            return jsonify({"turbo_mode": ai_cfg["turbo_mode"], "message":"🚀 Turbo toggled"})
        if action == "toggle_stealth":
            ai_cfg["stealth_mode"] = not ai_cfg["stealth_mode"]
            return jsonify({"stealth_mode": ai_cfg["stealth_mode"], "message":"🥷 Stealth toggled"})
        if action == "set_click_rate":
            try:
                v = float(data.get("value", ai_cfg["click_rate"]))
                ai_cfg["click_rate"] = min(max(v, ai_cfg["min_rate"]), ai_cfg["max_rate"])
                return jsonify({"click_rate": ai_cfg["click_rate"], "message": f"📈 click_rate={ai_cfg['click_rate']}"})
            except:
                return jsonify({"error":"invalid value"}),400
        if action == "boost":
            stats["revenue"] += 10.0
            return jsonify({"revenue": stats["revenue"], "message": "💰 Boost +$10!"})
        if action == "reset":
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending": 0})
            ai_cfg["history"].clear()
            return jsonify({"message": "🔄 Stats reset", **stats})
    return jsonify({"error":"unknown command"}),400

@app.route("/scan", methods=["POST"])
def manual_scan():
    with lock:
        stats["imps"] += 3
        cpc = fetch_cpc()
        if random.random() < ai_cfg["click_rate"] * 2.5:
            stats["clicks"] += 1
            stats["pending"] += int(cpc*100)
        stats["last_update"] = datetime.now().isoformat()
    return jsonify(stats)

@app.route("/")
def index():
    return open("web/index.html").read()

if __name__ == "__main__":
    logging.info("🚀 Starting AI Clicker Engine...")
    for i in range(4):
        t = threading.Thread(target=ai_scan_worker, args=(i+1,), daemon=True)
        t.start()
        logging.info(f"✅ Worker-{i+1} started")
    app.run(host="0.0.0.0", port=PORT)
