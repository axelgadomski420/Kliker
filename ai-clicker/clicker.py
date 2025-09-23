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
        "clicking_active": False,
        "watching_active": False,
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
        "clicking_active": False,
        "watching_active": False,
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
        "clicking_active": False,
        "watching_active": False,
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
        "clicking_active": False,
        "watching_active": False,
        "milestones": [20, 50, 100, 200],
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
    {"id": 11, "network": "Jsjsjsj", "url": "https://sgben.com/link?z=9917779&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 12, "network": "Hsh", "url": "https://92orb.com/link?z=9917780&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 13, "network": "Ldldkj", "url": "https://ldl1.com/link?z=9917784&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 14, "network": "Ksjsbb", "url": "https://92orb.com/link?z=9917785&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
]

def load_links():
    try:
        with open(LINKS_FILE) as f:
            links = json.load(f)
            if not links:
                return DEFAULT_LINKS.copy()
            return links
    except FileNotFoundError:
        return DEFAULT_LINKS.copy()
    except json.JSONDecodeError:
        logging.warning("Plik links.json jest uszkodzony, używam domyślnej listy linków")
        return DEFAULT_LINKS.copy()

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

def start_mega_scan(duration_seconds=3000):
    global mega_scan_active, mega_scan_end_time
    with mega_scan_lock:
        mega_scan_active = True
        mega_scan_end_time = time.time() + duration_seconds
    logging.info(f"Mega scan activated for {duration_seconds} seconds")

def ai_bot_worker(bot_name):
    bot_cfg = ai_bots_cfg[bot_name]
    logging.info(f"{bot_cfg['name']} started")
    global supermode_active, supermode_end_time
    global mega_scan_active, mega_scan_end_time
    while True:
        with supermode_lock:
            if supermode_active and time.time() > supermode_end_time:
                logging.info("Supermode expired - stopping")
                stop_supermode()
        with mega_scan_lock:
            if mega_scan_active and time.time() > mega_scan_end_time:
                logging.info("Mega scan expired - stopping")
                mega_scan_active = False
            mega_effect = mega_scan_active
        cpc = fetch_cpc()
        mult = smart_timing_multiplier()
        with lock:
            increment = 1 if random.random() < bot_cfg["click_rate"] * mult else 0
            if mega_effect:
                increment = max(increment,1)
                stats["imps"] += 3
                stats["revenue"] += 0.1
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
    links = load_links()
    if not data or "network" not in data or "url" not in 
        pass
    else:
        new_id = max((l["id"] for l in links), default=0) + 1
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
    return jsonify(links)

@app.route("/command", methods=["POST"])
def command_api():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    with lock:
        if action == "przelacz_drogi_tryb":
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = not bot["expensive_mode"]
            return jsonify({"message": "Przełączono tryb drogi dla wszystkich botów"})
        elif action == "przelacz_turbo":
            for bot in ai_bots_cfg.values():
                bot["turbo_mode"] = not bot["turbo_mode"]
            return jsonify({"message": "Przełączono tryb turbo dla wszystkich botów"})
        elif action == "przelacz_ukryty":
            for bot in ai_bots_cfg.values():
                bot["stealth_mode"] = not bot["stealth_mode"]
            return jsonify({"message": "Przełączono tryb ukryty dla wszystkich botów"})
        elif action == "zwieksz_przychod":
            stats["revenue"] += 10.0
            return jsonify({"revenue": stats["revenue"], "message": "Zwiększono przychód o 10"})
        elif action == "resetuj_statystyki":
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending": 0})
            for bot in ai_bots_cfg.values():
                bot["history"].clear()
                bot["achievements"].clear()
            return jsonify({"message": "Zresetowano statystyki i boty", **stats})
        elif action == "ustaw_click_rate":
            try:
                v = float(data.get("value", 1.0))
                for bot in ai_bots_cfg.values():
                    bot["click_rate"] = max(bot.get("min_rate", 0.1), min(v, bot.get("max_rate", 10.0)))
                return jsonify({"message": f"Ustawiono click rate na {v} sekund dla wszystkich botów"})
            except (ValueError, TypeError):
                return jsonify({"error": "Nieprawidłowa wartość dla click rate"}), 400
        elif action == "start_klikanie":
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = True
            return jsonify({"message": "Rozpoczęto automatyczne klikanie dla wszystkich botów"})
        elif action == "stop_klikanie":
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = False
            return jsonify({"message": "Zatrzymano automatyczne klikanie dla wszystkich botów"})
        elif action == "start_oglądanie":
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = True
            return jsonify({"message": "Rozpoczęto automatyczne oglądanie dla wszystkich botów"})
        elif action == "stop_oglądanie":
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = False
            return jsonify({"message": "Zatrzymano automatyczne oglądanie dla wszystkich botów"})
        elif action == "aktywuj_supermode":
            start_supermode(6000)
            return jsonify({"message": "Supermode aktywowany na 6000 sekund"})
        elif action == "dezaktywuj_supermode":
            stop_supermode()
            return jsonify({"message": "Supermode dezaktywowany"})
        elif action == "start_mega_scan":
            start_mega_scan(3000)
            return jsonify({"message": "Mega scan aktywowany na 3000 sekund"})
        else:
            return jsonify({"error": "Nieznana komenda"}), 400

@app.route("/huggingface_chat", methods=["POST"])
def huggingface_chat():
    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "Brak wiadomości"}), 400
    
    HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/gpt2"
    HUGGINGFACE_API_KEY = "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"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": message, "options": {"wait_for_model": True}}

    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        return jsonify({"error": "Błąd Huggingface API", "details": response.text}), 500
    outputs = response.json()

    if isinstance(outputs, list) and len(outputs) > 0:
        model_response = outputs[0].get("generated_text", "").strip()
    else:
        model_response = ""

    response_lower = message.lower()
    command_response = ""
    with lock:
        if "aktywuj supermode" in response_lower or "włącz supermode" in response_lower:
            start_supermode(6000)
            command_response = "Supermode aktywowany."
        elif "dezaktywuj supermode" in response_lower or "wyłącz supermode" in response_lower:
            stop_supermode()
            command_response = "Supermode dezaktywowany."
        elif "ustaw click rate" in response_lower:
            m = re.search(r"(\d+)", response_lower)
            if m:
                val = float(m.group(1))
                for bot in ai_bots_cfg.values():
                    bot["click_rate"] = max(bot.get("min_rate", 0.1), min(val, bot.get("max_rate", 10.0)))
                command_response = f"Ustawiono click rate na {val} sekund."
            else:
                command_response = "Nie mogę rozpoznać wartości click rate."
        else:
            command_response = "Nie rozumiem polecenia."

    return jsonify({
        "model_response": model_response,
        "command_response": command_response
    })

@app.route("/")
def index():
    try:
        return open("web/index.html").read()
    except FileNotFoundError:
        return "<h1>AI Clicker Platform</h1><p>Index file missing</p>"

@app.route("/scan", methods=["POST"])
def manual_scan():
    start_mega_scan(30)
    return jsonify({"message": "Mega scan aktywowany na 30 sekund"})


if __name__ == "__main__":
    logging.info("🚀 Starting AI Clicker Engine with 4 AI bots...")
    for bot_name in ai_bots_cfg.keys():
        t = threading.Thread(target=ai_bot_worker, args=(bot_name,), daemon=True)
        t.start()
        logging.info(f"✅ {bot_name} started")
    app.run(host="0.0.0.0", port=PORT)
