import os
import json
import time
import random
import threading
import requests
import logging
import re
import secrets
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PORT = int(os.getenv("PORT", "5000"))

# Global stats
stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending": 0,
    "last_update": datetime.now().isoformat()
}

# User agents pool for variability
user_agents_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)"
]

# Bots config with initial fields
ai_bots_cfg = {
    "Bot1": {
        "name": "HelperBot",
        "click_rate": 0.15,
        "expensive_mode": False,
        "turbo_mode": False,
        "stealth_mode": True,
        "min_rate": 0.05,
        "max_rate": 0.5,
        "history": [],
        "achievements": [],
        "mode": "normal",
        "interval": 3.0,
        "clicking_active": True,
        "watching_active": True,
        "milestones": [10, 20, 50, 100],
    },
    "Bot2": {
        "name": "TurboBot",
        "click_rate": 0.35,
        "expensive_mode": False,
        "turbo_mode": True,
        "stealth_mode": False,
        "min_rate": 0.1,
        "max_rate": 0.8,
        "history": [],
        "achievements": [],
        "mode": "turbo",
        "interval": 2.0,
        "clicking_active": True,
        "watching_active": True,
        "milestones": [10, 25, 60, 120],
    },
    "Bot3": {
        "name": "StealthBot",
        "click_rate": 0.1,
        "expensive_mode": True,
        "turbo_mode": False,
        "stealth_mode": True,
        "min_rate": 0.05,
        "max_rate": 0.4,
        "history": [],
        "achievements": [],
        "mode": "stealth",
        "interval": 4.0,
        "clicking_active": True,
        "watching_active": True,
        "milestones": [5, 15, 40, 90],
    },
    "Bot4": {
        "name": "BoosterBot",
        "click_rate": 0.25,
        "expensive_mode": False,
        "turbo_mode": True,
        "stealth_mode": True,
        "min_rate": 0.1,
        "max_rate": 0.7,
        "history": [],
        "achievements": [],
        "mode": "boost",
        "interval": 3.5,
        "clicking_active": True,
        "watching_active": True,
        "milestones": [20, 50, 100, 200],
    },
}

lock = threading.Lock()
proxy_lock = threading.Lock()
LINKS_FILE = "links.json"

PROXIES = [
    "http://fmjwfjea:2dg9ugb5gi@142.111.48.253:7030/",
    "http://fmjwfjea:2dg9ugb5gi@198.23.239.134:6540/",
    "http://fmjwfjea:2dg9ugb5gi@45.38.97.14:6014/",
    "http://fmjwfjea:2dg9ugb5gi@107.172.27.3:6543/",
    "http://fmjwfjea:2dg9ugb5gi@64.137.74.30:6641/",
    "http://fmjwfjea:2dg9ugb5gi@154.203.43.7:5536/",
    "http://fmjwfjea:2dg9ugb5gi@84.247.125.21:6095/",
    "http://fmjwfjea:2dg9ugb5gi@216.159.7.3:6837/",
    "http://fmjwfjea:2dg9ugb5gi@142.67.45.12:5611/",
    "http://fmjwfjea:2dg9ugb5gi@142.128.95.8:6593/",
]

proxy_health_results = {}
proxy_fail_counts = {p: 0 for p in PROXIES}

def proxy_health_check(proxy_url):
    try:
        headers = {"User-Agent": random.choice(user_agents_list)}
        resp = requests.get("https://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url}, headers=headers, timeout=3)
        return resp.status_code == 200
    except:
        return False

def get_next_proxy():
    with proxy_lock:
        # Check and prune failing proxies
        alive_proxies = []
        for proxy in PROXIES:
            if proxy in proxy_health_results:
                if proxy_health_results[proxy]:
                    alive_proxies.append(proxy)
                else:
                    proxy_fail_counts[proxy] += 1
                    if proxy_fail_counts[proxy] >= 3:
                        logging.warning(f"Removing proxy {proxy} due to repeated failures")
                        PROXIES.remove(proxy)
            else:
                if proxy_health_check(proxy):
                    proxy_health_results[proxy] = True
                    alive_proxies.append(proxy)
                else:
                    proxy_health_results[proxy] = False
                    proxy_fail_counts[proxy] = proxy_fail_counts.get(proxy, 0)+1
        if not alive_proxies:
            logging.error("No working proxies")
            return None
        chosen = random.choice(alive_proxies)
        return {"http": chosen, "https": chosen}

def generate_unique_id(num_bytes=8):
    return secrets.token_hex(num_bytes)

def fetch_cpc():
    # Simulated CPC fetching logic with proxy rotation
    proxy = get_next_proxy()
    headers = {"User-Agent": random.choice(user_agents_list)}
    try:
        # In actual scenario: replace with real endpoint to get CPC
        return round(0.05 + random.random() * 0.15, 4)
    except Exception as e:
        logging.warning(f"CPC fetch error: {e}")
        return 0.1

def smart_timing_multiplier():
    hour = datetime.now().hour
    if 6 <= hour <= 9 or 18 <= hour <= 23:
        return 1.5
    elif 0 <= hour <= 5:
        return 0.7
    else:
        return 1.0

def check_achievements(stats, bot):
    new_achievements = []
    for milestone in bot["milestones"][:]:
        if stats["revenue"] >= milestone:
            new_achievements.append(f"💰 Milestone reached: ${milestone}")
            bot["milestones"].remove(milestone)
    if stats["clicks"] >= 100 and "Century Club" not in bot["achievements"]:
        new_achievements.append("🎯 Century Club - 100 clicks")
        bot["achievements"].append("Century Club")
    if stats["imps"] >= 1000 and "Impression Master" not in bot["achievements"]:
        new_achievements.append("👁️ Impression Master - 1000 imps")
        bot["achievements"].append("Impression Master")
    return new_achievements

# Thread-safe flags for modes
supermode_active = False
supermode_lock = threading.Lock()
supermode_end_time = None

mega_scan_active = False
mega_scan_lock = threading.Lock()
mega_scan_end_time = None

def start_supermode(duration_seconds):
    global supermode_active, supermode_end_time
    with supermode_lock:
        supermode_active = True
        supermode_end_time = time.time() + duration_seconds
        with lock:
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = True
                bot["turbo_mode"] = True
                bot["stealth_mode"] = True
                bot["click_rate"] = 4.0
                bot["clicking_active"] = True
                bot["watching_active"] = True
    logging.info(f"Supermode activated for {duration_seconds} seconds")

def stop_supermode():
    global supermode_active
    with supermode_lock:
        supermode_active = False
        with lock:
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = False
                bot["turbo_mode"] = False
                bot["stealth_mode"] = False
                bot["clicking_active"] = False
                bot["watching_active"] = False
    logging.info("Supermode deactivated")

def start_mega_scan(duration_seconds):
    global mega_scan_active, mega_scan_end_time
    with mega_scan_lock:
        mega_scan_active = True
        mega_scan_end_time = time.time() + duration_seconds
    logging.info(f"Mega scan activated for {duration_seconds} seconds")

def ai_bot_worker(bot_name):
    bot = ai_bots_cfg[bot_name]
    logging.info(f"Bot '{bot['name']}' started")
    global supermode_active, supermode_end_time, mega_scan_active, mega_scan_end_time

    while True:
        with supermode_lock:
            if supermode_active and time.time() > supermode_end_time:
                logging.info("Supermode expired. Deactivating.")
                stop_supermode()

        with mega_scan_lock:
            if mega_scan_active and time.time() > mega_scan_end_time:
                logging.info("Mega scan expired. Deactivating.")
                mega_scan_active = False
            mega_active = mega_scan_active

        links = load_links()
        if not links:
            time.sleep(5)
            continue

        # Select random active link and fill parameters securely
        selected_link = random.choice(links)["url"]
        unique_source = generate_unique_id(6)
        unique_click = generate_unique_id(8)
        url = selected_link.replace("{SOURCE_ID}", unique_source).replace("{CLICK_ID}", unique_click)

        proxy = get_next_proxy()
        headers = {"User-Agent": random.choice(user_agents_list)}

        if not bot["clicking_active"]:
            time.sleep(bot["interval"])
            continue

        try:
            response = requests.get(url, proxies=proxy, headers=headers, timeout=15)
            if response.status_code == 200:
                with lock:
                    stats["clicks"] += 1
                    cpc = fetch_cpc()
                    stats["revenue"] += cpc
                    stats["imps"] += 1 if not mega_active else 4
                    stats["last_update"] = datetime.now().isoformat()
                logging.info(f"Bot '{bot['name']}' clicked URL successfully.")
            else:
                logging.warning(f"Bot '{bot['name']}' received status {response.status_code} for URL.")
        except Exception as e:
            logging.error(f"Bot '{bot['name']}' error during click: {e}")

        with lock:
            if mega_active:
                stats["imps"] += 3
                stats["revenue"] += 0.1

            # Additional revenue increments based on bot modes
            if bot["expensive_mode"]:
                stats["revenue"] += 0.01
            if bot["turbo_mode"]:
                stats["imps"] += 1
            if bot["stealth_mode"] and random.random() < 0.1:
                stats["clicks"] = max(0, stats["clicks"] - 1)

            # Record history for achievements and analytics
            bot["history"].append(stats["revenue"])
            if len(bot["history"]) > 50:
                bot["history"].pop(0)

            achievements_new = check_achievements(stats, bot)
            for ach in achievements_new:
                logging.info(f"{bot['name']} achieved: {ach}")

            # Random toggling for dynamic patterns
            r = random.random()
            if r < 0.03:
                bot["expensive_mode"] = not bot["expensive_mode"]
            elif r < 0.06:
                bot["turbo_mode"] = not bot["turbo_mode"]
            elif r < 0.09:
                bot["stealth_mode"] = not bot["stealth_mode"]
            elif r < 0.12:
                stats["revenue"] += 5.0
                logging.info(f"{bot['name']} got revenue boost +5")

        time.sleep(bot["interval"] * random.uniform(0.8,1.2))

@app.route("/stats")
def api_stats():
    with lock:
        ctr = (stats["clicks"] / stats["imps"] * 100) if stats["imps"] > 0 else 0
        return jsonify({**stats, "ctr": round(ctr, 2)})

@app.route("/links", methods=["GET", "POST"])
def api_links():
    if request.method == "GET":
        return jsonify(load_links())

    data = request.get_json()

    # Poprawiony warunek: dodane 'data' po "url" not in
    if not data or "network" not in data or "url" not in data:
        return jsonify({"error": "Missing required fields: 'network' or 'url'"}), 400

    links = load_links()
    new_id = max([l["id"] for l in links], default=0) + 1  # Zabezpieczenie przed pustą listą

    new_link = {
        "id": new_id,
        "network": data["network"],
        "url": data["url"],
        "weight": 1.0
    }

    links.append(new_link)
    save_links(links)
    return jsonify(new_link), 201

@app.route("/command", methods=["POST"])
def api_command():
    data = request.get_json() or {}
    action = data.get("action","").lower()

    if action == "przelacz_drogi_tryb":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = not bot["expensive_mode"]
        return jsonify({"message":"Toggled expensive mode"})

    if action == "przelacz_turbo":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["turbo_mode"] = not bot["turbo_mode"]
        return jsonify({"message":"Toggled turbo mode"})

    if action == "przelacz_ukryty":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["stealth_mode"] = not bot["stealth_mode"]
        return jsonify({"message":"Toggled stealth mode"})

    if action == "zwieksz_przychod":
        with lock:
            stats["revenue"] += 10.0
        return jsonify({"message":"Increased revenue by 10","revenue":stats["revenue"]})

    if action == "resetuj":
        with lock:
            stats.update(imps=0, clicks=0, revenue=0.0)
            for bot in ai_bots_cfg.values():
                bot["history"].clear()
                bot["achievements"].clear()
        return jsonify({"message":"Stats and bots reset","stats":stats})

    if action == "ustaw_click_rate":
        val = data.get("value")
        try:
            val = float(val)
        except Exception:
            return jsonify({"error":"Invalid click rate"}), 400
        with lock:
            for bot in ai_bots_cfg.values():
                bot["click_rate"] = max(bot["min_rate"], min(val, bot["max_rate"]))
        return jsonify({"message":f"Click rate set to {val}"})

    if action == "start_klikanie":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = True
        return jsonify({"message":"Started clicking"})

    if action == "stop_klikanie":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = False
        return jsonify({"message":"Stopped clicking"})

    if action == "start_oglądanie":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = True
        return jsonify({"message":"Started watching"})

    if action == "stop_oglądanie":
        with lock:
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = False
        return jsonify({"message":"Stopped watching"})

    if action == "aktywuj_supermode":
        start_supermode(6000)
        return jsonify({"message":"Supermode activated for 6000 seconds"})

    if action == "dezaktywuj_supermode":
        stop_supermode()
        return jsonify({"message":"Supermode deactivated"})

    if action == "start_mega_scan":
        start_mega_scan(3000)
        return jsonify({"message":"Mega scan activated for 3000 seconds"})

    return jsonify({"error":"Unknown command"}), 400

@app.route("/huggingface_chat", methods=["POST"])
def api_huggingface_chat():
    data = request.get_json()
    message = data.get("message","")
    if not message:
        return jsonify({"error":"Message missing"}), 400

    token = os.getenv("HUGGINGFACE_API_KEY","")
    if not token:
        return jsonify({"error":"Huggingface API token missing"}), 500

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        "https://api-inference.huggingface.co/models/gpt2",
        headers=headers,
        json={"inputs": message, "options": {"wait_for_model": True}}
    )
    if response.status_code != 200:
        return jsonify({"error":"Huggingface API error","details":response.text}), 500
    res_json = response.json()
    text_response = ""
    if isinstance(res_json, list) and res_json:
        text_response = res_json[0].get("generated_text","").strip()

    lmsg = message.lower()
    command_response = ""

    with lock:
        if "aktywuj supermode" in lmsg or "włącz supermode" in lmsg:
            start_supermode(6000)
            command_response = "Supermode activated."
        elif "dezaktywuj supermode" in lmsg or "wyłącz supermode" in lmsg:
            stop_supermode()
            command_response = "Supermode deactivated."
        elif "ustaw click rate" in lmsg:
            val = None
            match = re.search(r"(\d+(\.\d+)?)", lmsg)
            if match:
                val = float(match.group(1))
            if val is not None:
                for bot in ai_bots_cfg.values():
                    bot["click_rate"] = max(bot["min_rate"], min(val, bot["max_rate"]))
                command_response = f"Click rate set to {val} seconds."
            else:
                command_response = "Could not parse click rate value."
        else:
            command_response = "Command not recognized."

    return jsonify({"model_response": text_response, "command_response": command_response})

@app.route("/")
def index():
    try:
        return open("web/index.html").read()
    except:
        return "<h1>AI Clicker Platform</h1><p>Index file missing</p>"

@app.route("/scan", methods=["POST"])
def api_scan():
    start_mega_scan(3000)  # 50 minutes
    return jsonify({"message":"Mega scan started for 3000 seconds"})

if __name__ == "__main__":
    logging.info(f"Starting AI Clicker on port {PORT}")
    for bot_name in ai_bots_cfg:
        bot = ai_bots_cfg[bot_name]
        bot["clicking_active"] = True  # launch active behavior
        bot["watching_active"] = True

    for bot_name in ai_bots_cfg:
        thread = threading.Thread(target=ai_bot_worker, args=(bot_name,), daemon=True)
        thread.start()
    app.run(host="0.0.0.0", port=PORT)
