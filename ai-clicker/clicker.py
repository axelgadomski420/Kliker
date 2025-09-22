import os
import time
import random
import threading
import requests
import stripe
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__, static_folder=None)

# ─── Stripe configuration ────────────────────────────────────────────────────────────────
stripe.api_key = "sk_test_51S8ZUk7Vc44kK9xyEOanxQOeTsa2Fs6ob6RbraWMu3ztUSnJEWX3O03tvrYABcVgbU145qMKtjQCcHWYtcAL1vHg003l8t4V4c"
PUBLIC_KEY = "pk_test_51S8ZUk7Vc44kK9xym9bYMvS1TFJcwqDyzZ3EpDQIY8Syr9S56wMjeVAgnCGcwPm5dIj3Ofoj0lylb6eZ6gCieiC000bIOvtsvr"

# ─── Global stats & AI settings ─────────────────────────────────────────────────────────
stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending_amount": 0,
    "last_charge": None,
    "last_update": datetime.now().isoformat()
}
ai = {
    "click_rate": float(os.getenv("CLICK_RATE", "0.20")),
    "min_rate": 0.05,
    "max_rate": 0.80,
    "interval": 3.0,
    "expensive_mode": False,
    "turbo_mode": False,
    "stealth_mode": True,
    "history": [],
    "milestones": [10, 50, 100, 250, 500, 1000],
    "achievements": [],
    "proxy_rotation": True,
    "smart_timing": True
}

lock = threading.Lock()

PROXIES = [
    "http://51.158.68.68:8811",
    "http://192.99.56.244:80",
    "http://45.77.24.239:8080",
    "http://165.16.64.198:8800",
    "http://159.89.49.217:3128",
]

def get_random_proxy():
    if not ai["proxy_rotation"]:
        return None
    p = random.choice(PROXIES)
    return {"http": p, "https": p}

def fetch_cpc():
    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random.randint(537, 539)}.36"
    }
    try:
        proxy = get_random_proxy()
        requests.get("https://httpbin.org/json", proxies=proxy, headers=headers, timeout=2)
        return round(0.05 + random.random() * 0.15, 4)
    except:
        return ai["click_rate"]

def smart_timing_multiplier():
    if not ai["smart_timing"]:
        return 1.0
    h = datetime.now().hour
    if 6 <= h <= 9 or 18 <= h <= 23:
        return 1.5
    if 0 <= h <= 5:
        return 0.7
    return 1.0

def check_achievements():
    new = []
    for m in ai["milestones"][:]:
        if stats["revenue"] >= m:
            new.append(f"💰 Reached ${m} revenue!")
            ai["milestones"].remove(m)
    if stats["clicks"] >= 100 and "First Century" not in ai["achievements"]:
        new.append("🎯 First Century - 100 clicks!")
        ai["achievements"].append("First Century")
    if stats["imps"] >= 1000 and "Impression Master" not in ai["achievements"]:
        new.append("👁️ Impression Master - 1000 impressions!")
        ai["achievements"].append("Impression Master")
    return new

def premium_scan_engine(worker_id):
    while True:
        cpc = fetch_cpc()
        timing = smart_timing_multiplier()
        with lock:
            ai["click_rate"] = min(max(cpc, ai["min_rate"]), ai["max_rate"])
            stats["imps"] += 1
            rate = ai["click_rate"] * timing
            if ai["expensive_mode"]:
                rate *= 2
            if ai["turbo_mode"]:
                rate *= 1.5
            if ai["stealth_mode"]:
                rate *= random.uniform(0.8, 1.2)
            if random.random() < min(rate, 0.95):
                stats["clicks"] += 1
                stats["pending_amount"] += int(cpc * 100)
            # create a PaymentIntent every 10 clicks
            if stats["clicks"] and stats["clicks"] % 10 == 0 and stats["pending_amount"] > 0:
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
                except Exception as e:
                    print("Stripe error:", e)
            stats["last_update"] = datetime.now().isoformat()
            ai["history"].append(stats["revenue"])
            if len(ai["history"]) > 50:
                ai["history"].pop(0)
            for ach in check_achievements():
                print(f"🏆 Worker-{worker_id}: {ach}")
        time.sleep(ai["interval"] * random.uniform(0.8, 1.2))

@app.route("/scan", methods=["POST"])
def manual_scan():
    with lock:
        stats["imps"] += 3
        cpc = fetch_cpc()
        bonus_rate = ai["click_rate"] * 2.5
        if random.random() < bonus_rate:
            stats["clicks"] += random.randint(1, 3)
            stats["pending_amount"] += int(cpc * 100)
        stats["last_update"] = datetime.now().isoformat()
    return jsonify(stats)

@app.route("/stats")
def get_stats():
    with lock:
        ctr = round((stats["clicks"] / max(stats["imps"], 1)) * 100, 2)
        return jsonify({
            **stats,
            "ctr": ctr,
            "public_key": PUBLIC_KEY,
            "ai_settings": {
                "expensive_mode": ai["expensive_mode"],
                "turbo_mode": ai["turbo_mode"],
                "stealth_mode": ai["stealth_mode"]
            }
        })

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    if action == "toggle_expensive":
        ai["expensive_mode"] = not ai["expensive_mode"]
        return jsonify({"expensive_mode": ai["expensive_mode"], "message": "💎 Expensive toggled!"})
    if action == "toggle_turbo":
        ai["turbo_mode"] = not ai["turbo_mode"]
        return jsonify({"turbo_mode": ai["turbo_mode"], "message": "🚀 Turbo toggled!"})
    if action == "toggle_stealth":
        ai["stealth_mode"] = not ai["stealth_mode"]
        return jsonify({"stealth_mode": ai["stealth_mode"], "message": "🥷 Stealth toggled!"})
    if action == "set_click_rate":
        try:
            v = float(data.get("value", ai["click_rate"]))
            ai["click_rate"] = min(max(v, ai["min_rate"]), ai["max_rate"])
            return jsonify({"click_rate": ai["click_rate"], "message": f"📈 Click rate set to {ai['click_rate']}"})
        except:
            return jsonify({"error": "Invalid value"}), 400
    if action == "boost":
        with lock:
            stats["revenue"] += 10.0
        return jsonify({"revenue": stats["revenue"], "message": "💰 Boost +$10!"})
    if action == "reset":
        with lock:
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending_amount": 0})
        return jsonify({"message": "🔄 Stats reset!", **stats})
    return jsonify({"error": "Unknown command"}), 400

@app.route("/")
def dashboard():
    return open("web/index.html").read()

if __name__ == "__main__":
    print("🚀 Starting Ultimate Ad Mining Platform...")
    for i in range(1, 5):
        threading.Thread(target=premium_scan_engine, args=(i,), daemon=True).start()
        print(f"✅ Worker-{i} launched")
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
