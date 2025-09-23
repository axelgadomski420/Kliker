import os
import json
import time
import random
import threading
import requests
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PORT = int(os.getenv("PORT", "5000"))
DEFAULT_CLICK_RATE = float(os.getenv("CLICK_RATE", "0.20"))

stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending": 0,
    "last_update": datetime.now().isoformat()
}

# AI bots configurations with diverse modes
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
    },
}

lock = threading.Lock()
proxy_lock = threading.Lock()
LINKS_FILE = "links.json"

PROXIES = [
    "http://fmjwfjea:2dg9ugb5x8gi@142.111.48.253:7030/",
    "http://fmjwfjea:2dg9ugb5x8gi@198.23.239.134:6540/",
    "http://fmjwfjea:2dg9ugb5x8gi@45.38.107.97:6014/",
    "http://fmjwfjea:2dg9ugb5x8gi@107.172.163.27:6543/",
    "http://fmjwfjea:2dg9ugb5x8gi@64.137.96.74:6641/",
    "http://fmjwfjea:2dg9ugb5x8gi@154.203.43.247:5536/",
    "http://fmjwfjea:2dg9ugb5x8gi@84.247.60.125:6095/",
    "http://fmjwfjea:2dg9ugb5x8gi@216.10.27.159:6837/",
    "http://fmjwfjea:2dg9ugb5x8gi@142.111.67.146:5611/",
    "http://fmjwfjea:2dg9ugb5x8gi@142.147.128.93:6593/",
]

proxy_fail_counts = {p: 0 for p in PROXIES}
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
    with proxy_lock:
        if not PROXIES:
            logging.warning("Proxy list empty, using no proxy.")
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
        headers = {"User-Agent": f"Mozilla/5.0 AppleWebKit/{random.randint(537,539)}.36"}
        resp = requests.get("https://ipv4.webshare.io/", proxies=proxy, headers=headers, timeout=5)
        resp.raise_for_status()
        return round(0.05 + random.random() * 0.15, 4)
    except Exception as e:
        if proxy_url:
            report_proxy_failure(proxy_url)
        logging.warning(f"CPC fetch failed with proxy {proxy_url}: {e}")
        return 0.1

def smart_timing_multiplier():
    h = datetime.now().hour
    if 6 <= h <= 9 or 18 <= h <= 23:
        return 1.5
    if 0 <= h <= 5:
        return 0.7
    return 1.0

def check_achievements(stats_dict, ai_cfg_bot):
    new = []
    for m in ai_cfg_bot["milestones"][:]:
        if stats_dict["revenue"] >= m:
            new.append(f"💰 Milestone: ${m}")
            ai_cfg_bot["milestones"].remove(m)
    if stats_dict["clicks"] >= 100 and "Century Club" not in ai_cfg_bot["achievements"]:
        new.append("🎯 Century Club: 100 clicks")
        ai_cfg_bot["achievements"].append("Century Club")
    if stats_dict["imps"] >= 1000 and "Impression Master" not in ai_cfg_bot["achievements"]:
        new.append("👁️ Impression Master: 1000 imps")
        ai_cfg_bot["achievements"].append("Impression Master")
    return new

def ai_bot_worker(bot_name):
    bot_cfg = ai_bots_cfg[bot_name]
    logging.info(f"{bot_cfg['name']} started")
    while True:
        cpc = fetch_cpc()
        mult = smart_timing_multiplier()
        with lock:
            increment = 1 if random.random() < bot_cfg["click_rate"] * mult else 0
            stats["imps"] += 1
            stats["clicks"] += increment
            stats["revenue"] += increment * cpc
            if bot_cfg["expensive_mode"]:
                stats["revenue"] += 0.01
            if bot_cfg["turbo_mode"]:
                stats["imps"] += 1
            if bot_cfg["stealth_mode"] and random.random() < 0.1:
                stats["clicks"] = max(0, stats["clicks"] - 1)
            stats["last_update"] = datetime.now().isoformat()
            bot_cfg["history"].append(stats["revenue"])
            if len(bot_cfg["history"]) > 50:
                bot_cfg["history"].pop(0)
            for a in check_achievements(stats, bot_cfg):
                logging.info(f"{bot_cfg['name']} achievement: {a}")
            r = random.random()
            if r < 0.03:
                bot_cfg["expensive_mode"] = not bot_cfg["expensive_mode"]
                logging.info(f"{bot_cfg['name']} toggled expensive_mode to {bot_cfg['expensive_mode']}")
            elif r < 0.06:
                bot_cfg["turbo_mode"] = not bot_cfg["turbo_mode"]
                logging.info(f"{bot_cfg['name']} toggled turbo_mode to {bot_cfg['turbo_mode']}")
            elif r < 0.09:
                bot_cfg["stealth_mode"] = not bot_cfg["stealth_mode"]
                logging.info(f"{bot_cfg['name']} toggled stealth_mode to {bot_cfg['stealth_mode']}")
            elif r < 0.12:
                stats["revenue"] += 5.0
                logging.info(f"{bot_cfg['name']} performed revenue boost +$5")
        time.sleep(bot_cfg.get("interval", 3.0) * random.uniform(0.8, 1.2))

@app.route("/stats")
def stats_api():
    with lock:
        ctr = round(stats["clicks"] / max(stats["imps"], 1) * 100, 2)
        return jsonify({**stats, "ctr": ctr})

@app.route("/links", methods=["GET", "POST"])
def links_api():
    if request.method == "GET":
        return jsonify(load_links())

    data = request.get_json()

    if not data or "network" not in data or "url" not in 
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

@app.route("/command", methods=["POST"])
def command_api():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    with lock:
        if action == "toggle_expensive":
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = not bot["expensive_mode"]
            return jsonify({"message": "Toggled expensive mode for all bots"})
        if action == "toggle_turbo":
            for bot in ai_bots_cfg.values():
                bot["turbo_mode"] = not bot["turbo_mode"]
            return jsonify({"message": "Toggled turbo mode for all bots"})
        if action == "toggle_stealth":
            for bot in ai_bots_cfg.values():
                bot["stealth_mode"] = not bot["stealth_mode"]
            return jsonify({"message": "Toggled stealth mode for all bots"})
        if action == "boost":
            stats["revenue"] += 10.0
            return jsonify({"revenue": stats["revenue"], "message": "Boost triggered"})
        if action == "reset":
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending": 0})
            for bot in ai_bots_cfg.values():
                bot["history"].clear()
                bot["achievements"].clear()
            return jsonify({"message": "Stats and bots reset", **stats})
    return jsonify({"error": "unknown command"}), 400

@app.route("/scan", methods=["POST"])
def manual_scan():
    with lock:
        stats["imps"] += 3
        stats["clicks"] += 1
        stats["revenue"] += 0.1
        stats["last_update"] = datetime.now().isoformat()
    return jsonify(stats)

@app.route("/")
def index():
    try:
        return open("web/index.html").read()
    except FileNotFoundError:
        return "<h1>AI Clicker Platform</h1><p>Index file missing</p>"

if __name__ == "__main__":
    logging.info("🚀 Starting AI Clicker Engine with 4 AI bots...")
    for bot_name in ai_bots_cfg.keys():
        t = threading.Thread(target=ai_bot_worker, args=(bot_name,), daemon=True)
        t.start()
        logging.info(f"✅ {bot_name} started")
    app.run(host="0.0.0.0", port=PORT)
