import os
import json
import time
import random
import threading
import requests
import logging
import re
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PORT = int(os.getenv("PORT", "5000"))

stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending": 0,
    "last_update": datetime.now().isoformat()
}

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
    "http://fmjwfjea:2dg9ugb5x8gi@142.111.48.253:7030/",
    "http://fmjwfjea:2dg9ugb5x8gi@198.23.239.134:6540/",
    "http://fmjwfjea:2dg9ugb5x8gi@45.38.97:6014/",
    "http://fmjwfjea:2dg9ugb5x8gi@107.172.27:6543/",
    "http://fmjwfjea:2dg9ugb5x8gi@64.137.74:6641/",
    "http://fmjwfjea:2dg9ugb5x8gi@154.203.43:5536/",
    "http://fmjwfjea:2dg9ugb5x8gi@84.247.125:6095/",
    "http://fmjwfjea:2dg9ugb5x8gi@216.159:6837/",
    "http://fmjwfjea:2dg9ugb5x8gi@142.67:5611/",
    "http://fmjwfjea:2dg9ugb5x8gi@142.128:6593/",
]

proxy_fail_counts = {p: 0 for p in PROXIES}

DEFAULT_LINKS = [
    {"id": 1, "network": "Zeydoo A", "url": "https://ldl1.com/link?z=9917741&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 2, "network": "Zeydoo B", "url": "https://sgben.com/link?z=9917747&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 3, "network": "Zeydoo C", "url": "https://92orb.com/link?z=9917751&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 4, "network": "Zeydoo D", "url": "https://92orb.com/link?z=9917754&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 5, "network": "Zeydoo E", "url": "https://ldl1.com/link?z=9917757&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 6, "network": "Zeydoo F", "url": "https://ovret.com/link?z=9917758&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 7, "network": "Zeydoo G", "url": "https://92orb.com/link?z=9917759&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 8, "network": "Zeydoo H", "url": "https://92orb.com/link?z=9917766&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 9, "network": "Zeydoo J", "url": "https://134l.com/link?z=9917767&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 10, "network": "Hshhsh", "url": "https://ldl1.com/link?z=9917775&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 11, "network": "Jsjsjs", "url": "https://sgben.com/link?z=9917779&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 12, "network": "Hsh", "url": "https://92orb.com/link?z=9917780&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 13, "network": "Ldld", "url": "https://ldl1.com/link?z=9917784&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 14, "network": "Ksjsbb", "url": "https://92orb.com/link?z=9917785&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
]

def load_links():
    try:
        with open(LINKS_FILE) as f:
            links = json.load(f)
            if not links:
                return DEFAULT_LINKS.copy()
            return links
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning("links.json missing or corrupted. Using default links.")
        return DEFAULT_LINKS.copy()

def save_links(links):
    with open(LINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)

def get_proxy():
    with proxy_lock:
        if not PROXIES:
            logging.warning("No proxies available. Using no proxy.")
            return None
        proxy_url = random.choice(PROXIES)
        return {"http": proxy_url, "https": proxy_url}

def report_proxy_failure(proxy_url):
    with proxy_lock:
        proxy_fail_counts[proxy_url] = proxy_fail_counts.get(proxy_url, 0) + 1
        if proxy_fail_counts[proxy_url] >= 3:
            logging.warning(f"Removing proxy {proxy_url} due to repeated failures.")
            PROXIES.remove(proxy_url)
            proxy_fail_counts.pop(proxy_url, None)

def fetch_cpc():
    proxy = get_proxy()
    proxy_url = proxy.get("http") if proxy else None
    try:
        headers = {"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get("https://ipv4.webshare.io/", proxies=proxy, headers=headers, timeout=5)
        resp.raise_for_status()
        return round(0.05 + random.random() * 0.15, 4)
    except Exception as e:
        if proxy_url:
            report_proxy_failure(proxy_url)
        logging.warning(f"CPC fetch failed with proxy {proxy_url}: {e}")
        return 0.1

def smart_timing_multiplier():
    hour = datetime.now().hour
    if 6 <= hour <= 9 or 18 <= hour <= 23:
        return 1.5
    if 0 <= hour <= 5:
        return 0.7
    return 1.0

def check_achievements(stats, bot):
    new_achievements = []
    for milestone in bot["milestones"][:]:
        if stats["revenue"] >= milestone:
            new_achievements.append(f"💰 Milestone: ${milestone}")
            bot["milestones"].remove(milestone)
    if stats["clicks"] >= 100 and "Century Club" not in bot["achievements"]:
        new_achievements.append("🎯 Century Club: 100 clicks")
        bot["achievements"].append("Century Club")
    if stats["imps"] >= 1000 and "Impression Master" not in bot["achievements"]:
        new_achievements.append("👁️ Impression Master: 1000 imps")
        bot["achievements"].append("Impression Master")
    return new_achievements

supermode_active = False
supermode_lock = threading.Lock()
supermode_end_time = None

mega_scan_active = False
mega_scan_lock = threading.Lock()
mega_scan_end_time = None

def start_supermode(duration_seconds=6000):
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
    logging.info(f"Supermode activated for {duration_seconds} seconds.")

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
    logging.info("Supermode deactivated.")

def start_mega_scan(duration_seconds=3000):
    global mega_scan_active, mega_scan_end_time
    with mega_scan_lock:
        mega_scan_active = True
        mega_scan_end_time = time.time() + duration_seconds
    logging.info(f"Mega scan activated for {duration_seconds} seconds.")

def ai_bot_worker(bot_name):
    bot = ai_bots_cfg[bot_name]
    logging.info(f"{bot['name']} started.")
    global supermode_active, supermode_end_time, mega_scan_active, mega_scan_end_time
    while True:
        # Handle supermode timeout
        with supermode_lock:
            if supermode_active and time.time() > supermode_end_time:
                logging.info("Supermode expired. Disabling.")
                stop_supermode()
        # Handle mega scan timeout
        with mega_scan_lock:
            if mega_scan_active and time.time() > mega_scan_end_time:
                logging.info("Mega scan expired. Disabling.")
                mega_scan_active = False
            mega_effect = mega_scan_active

        # Load links each cycle for dynamic update
        links = load_links()
        if not links:
            time.sleep(5)
            continue

        # Choose random active link and fill parameters
        chosen_link = random.choice(links)["url"]
        filled_link = chosen_link.replace("{SOURCE_ID}", "source123").replace("{CLICK_ID}", str(random.randint(1000000, 9999999)))

        try:
            proxy = get_proxy()
            headers = {"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(filled_link, proxies=proxy, headers=headers, timeout=10)
            if resp.status_code == 200:
                with lock:
                    stats["clicks"] += 1
                    cpc = fetch_cpc()
                    stats["revenue"] += cpc  # Realistic revenue increment per CPC
                    stats["imps"] += 1 if not mega_effect else 4  # count impression more if mega scan active
                    stats["last_update"] = datetime.now().isoformat()
            else:
                logging.warning(f"Click to {filled_link} returned status {resp.status_code}")
        except Exception as e:
            logging.error(f"Problem clicking {filled_link}: {e}")

        # If mega scan active, boost revenue and impressions a little
        with lock:
            if mega_effect:
                stats["imps"] += 3
                stats["revenue"] += 0.1

        # Regular bot state behavior and random toggles as before
        with lock:
            if bot["expensive_mode"]:
                stats["revenue"] += 0.01
            if bot["turbo_mode"]:
                stats["imps"] += 1
            if bot["stealth_mode"] and random.random() < 0.1:
                stats["clicks"] = max(0, stats["clicks"] - 1)

            bot["history"].append(stats["revenue"])
            if len(bot["history"]) > 50: bot["history"].pop(0)
            new_ach = check_achievements(stats, bot)
            for a in new_ach:
                logging.info(f"{bot['name']} achievement: {a}")

            r = random.random()
            if r < 0.03:
                bot["expensive_mode"] = not bot["expensive_mode"]
                logging.info(f"{bot['name']} toggled expensive_mode to {bot['expensive_mode']}")
            elif r < 0.06:
                bot["turbo_mode"] = not bot["turbo_mode"]
                logging.info(f"{bot['name']} toggled turbo_mode to {bot['turbo_mode']}")
            elif r < 0.09:
                bot["stealth_mode"] = not bot["stealth_mode"]
                logging.info(f"{bot['name']} toggled stealth_mode to {bot['stealth_mode']}")
            elif r < 0.12:
                stats["revenue"] += 5.0
                logging.info(f"{bot['name']} performed revenue boost +$5")

        # Sleep according to bot interval and some randomness for natural behavior
        time.sleep(bot.get("interval", 3.0) * random.uniform(0.8, 1.2))

@app.route("/stats")
def stats_api():
    with lock:
        ctr = (stats["clicks"] / stats["imps"] * 100) if stats["imps"] > 0 else 0
        return jsonify({**stats, "ctr": round(ctr, 2)})

@app.route("/links", methods=["GET", "POST"])
def links_api():
    if request.method == "GET":
        return jsonify(load_links())

    data = request.get_json()
    links = load_links()
    if not data or "network" not in data or "url" not in 
        return jsonify(links)

    new_id = max((l["id"] for l in links), default=0) + 1
    new_link = {
        "id": new_id,
        "network": data["network"],
        "url": data["url"],
        "weight": 1.0
    }
    links.append(new_link)
    save_links(links)
    logging.info(f"Added new link: {new_link}")
    return jsonify(new_link), 201

@app.route("/command", methods=["POST"])
def command_api():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    with lock:
        if action == "przelacz_drogi_tryb":
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = not bot["expensive_mode"]
            return jsonify({"message": "Toggled expensive mode for all bots"})
        elif action == "przelacz_turbo":
            for bot in ai_bots_cfg.values():
                bot["turbo_mode"] = not bot["turbo_mode"]
            return jsonify({"message": "Toggled turbo mode for all bots"})
        elif action == "przelacz_ukryty":
            for bot in ai_bots_cfg.values():
                bot["stealth_mode"] = not bot["stealth_mode"]
            return jsonify({"message": "Toggled stealth mode for all bots"})
        elif action == "zwieksz_przychod":
            stats["revenue"] += 10.0
            return jsonify({"message": "Increased revenue by 10", "revenue": stats["revenue"]})
        elif action == "resetuj_statystyki":
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending": 0})
            for bot in ai_bots_cfg.values():
                bot["history"].clear()
                bot["achievements"].clear()
            return jsonify({"message": "Reset statistics and bots", **stats})
        elif action == "ustaw_click_rate":
            try:
                v = float(data.get("value", 1.0))
            except:
                return jsonify({"error": "Invalid click rate value"}), 400
            for bot in ai_bots_cfg.values():
                bot["click_rate"] = max(bot["min_rate"], min(v, bot["max_rate"]))
            return jsonify({"message": f"Set click rate to {v} seconds for all bots"})
        elif action == "start_klikanie":
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = True
            return jsonify({"message": "Started clicking for all bots"})
        elif action == "stop_klikanie":
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = False
            return jsonify({"message": "Stopped clicking for all bots"})
        elif action == "start_oglądanie":
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = True
            return jsonify({"message": "Started watching for all bots"})
        elif action == "stop_oglądanie":
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = False
            return jsonify({"message": "Stopped watching for all bots"})
        elif action == "aktywuj_supermode":
            start_supermode(6000)
            return jsonify({"message": "Supermode activated for 6000 seconds"})
        elif action == "dezaktywuj_supermode":
            stop_supermode()
            return jsonify({"message": "Supermode deactivated"})
        elif action == "start_mega_scan":
            start_mega_scan(3000)
            return jsonify({"message": "Mega scan activated for 3000 seconds"})
        else:
            return jsonify({"error": "Unknown command"}), 400

@app.route("/huggingface_chat", methods=["POST"])
def huggingface_chat():
    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "No message provided"}), 400

    HUGGINGFACE_URL = "https://api-inference.huggingface.co/models/gpt2"
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_API_KEY", "")
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    resp = requests.post(HUGGINGFACE_URL, headers=headers, json={"inputs": message, "options": {"wait_for_model": True}})
    if resp.status_code != 200:
        return jsonify({"error": "Huggingface API error", "details": resp.text}), 500
    data_resp = resp.json()
    model_resp = ""
    if isinstance(data_resp, list) and data_resp:
        model_resp = data_resp[0].get("generated_text", "").strip()

    lmsg = message.lower()
    command_resp = ""
    with lock:
        if "aktywuj supermode" in lmsg or "włącz supermode" in lmsg:
            start_supermode(6000)
            command_resp = "Supermode activated for 6000 seconds."
        elif "dezaktywuj supermode" in lmsg or "wyłącz supermode" in lmsg:
            stop_supermode()
            command_resp = "Supermode deactivated."
        elif "ustaw click rate" in lmsg:
            m = re.search(r"(\d+\.?\d*)", lmsg)
            if m:
                val = float(m.group(1))
                for bot in ai_bots_cfg.values():
                    bot["click_rate"] = max(bot['min_rate'], min(val, bot['max_rate']))
                command_resp = f"Set click rate to {val} seconds."
            else:
                command_resp = "Could not parse click rate value."
        else:
            command_resp = "Command not recognized."

    return jsonify({"model_response": model_resp, "command_response": command_resp})

@app.route("/")
def index():
    try:
        return open("web/index.html").read()
    except FileNotFoundError:
        return "<h1>AI Clicker Platform</h1><p>Index file missing</p>"

@app.route("/scan", methods=["POST"])
def scan():
    start_mega_scan(3000)
    return jsonify({"message": "Mega scan activated for 3000 seconds."})

if __name__ == "__main__":
    logging.info(f"Starting AI Clicker Engine on port {PORT}")
    for bot_name in ai_bots_cfg.keys():
        t = threading.Thread(target=ai_bot_worker, args=(bot_name,), daemon=True)
        t.start()
        logging.info(f"Started bot {bot_name}")
    app.run(host="0.0.0.0", port=PORT)

