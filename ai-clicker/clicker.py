import os
import json
import time
import random
import threading
import requests
import logging
import secrets
import re
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
lock = threading.Lock()
proxy_lock = threading.Lock()

# Global variables
PORT = int(os.getenv("PORT", "5000"))
stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending": 0,
    "last_update": datetime.now().isoformat()
}

user_agents_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)"
]

# Bots configuration
ai_bots_cfg = {
    "Bot1": {"name": "HelperBot", "click_rate": 0.15, "interval": 3.0, "clicking_active": True, "watching_active": True,
             "history": [], "achievements": [], "milestones": [10, 20, 50, 100],
             "expensive_mode": False, "turbo_mode": False, "stealth_mode": True, "min_rate": 0.05, "max_rate": 0.5},
    "Bot2": {"name": "TurboBot", "click_rate": 0.35, "interval": 2.0, "clicking_active": True, "watching_active": True,
             "history": [], "achievements": [], "milestones": [10, 25, 60, 120],
             "expensive_mode": False, "turbo_mode": True, "stealth_mode": False, "min_rate": 0.1, "max_rate": 0.8},
    "Bot3": {"name": "StealthBot", "click_rate": 0.1, "interval": 4.0, "clicking_active": True, "watching_active": True,
             "history": [], "achievements": [], "milestones": [5, 15, 40, 90],
             "expensive_mode": True, "turbo_mode": False, "stealth_mode": True, "min_rate": 0.05, "max_rate": 0.4},
    "Bot4": {"name": "BoosterBot", "click_rate": 0.25, "interval": 3.5, "clicking_active": True, "watching_active": True,
             "history": [], "achievements": [], "milestones": [20, 50, 100, 200],
             "expensive_mode": False, "turbo_mode": True, "stealth_mode": True, "min_rate": 0.1, "max_rate": 0.7}
}

LINKS_FILE = "links.json"

# Default links including all specified affiliate URLs
LINKS_DEFAULT = [
    {"id":1,"network":"Zeydoo A","url":"https://ldl1.com/link?z=9917741&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":2,"network":"Zeydoo B","url":"https://sgben.com/link?z=9917747&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":3,"network":"Zeydoo C","url":"https://92orb.com/link?z=9917751&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":4,"network":"Zeydoo D","url":"https://92orb.com/link?z=9917754&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":5,"network":"Zeydoo E","url":"https://ldl1.com/link?z=9917757&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":6,"network":"Zeydoo F","url":"https://ovret.com/link?z=9917758&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":7,"network":"Zeydoo G","url":"https://92orb.com/link?z=9917759&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":8,"network":"Zeydoo H","url":"https://92orb.com/link?z=9917766&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":9,"network":"Zeydoo J","url":"https://134l.com/link?z=9917767&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":10,"network":"Hshsh","url":"https://ldl1.com/link?z=9917775&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":11,"network":"Jsjsj","url":"https://sgben.com/link?z=9917779&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":12,"network":"Hsh","url":"https://92orb.com/link?z=9917780&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":13,"network":"Ldld","url":"https://ldl1.com/link?z=9917784&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0},
    {"id":14,"network":"Ksjsb","url":"https://92orb.com/link?z=9917785&var={SOURCE_ID}&ymid={CLICK_ID}","weight":1.0}
]

# Proxy list, use actual active proxies here
PROXIES = [
    "http://fmjwfje:a2dg@142.111.48.253:703",
    "http://fmjwfje:a2dg@198.23.239.134:6540",
    "http://fmjwfje:a2dg@45.38.97.14:6014",
    "http://fmjwfje:a2dg@107.172.27.3:6543",
    "http://fmjwfje:a2dg@64.137.30.48:6641",
    "http://fmjwfje:a2dg@154.203.7.43:5536",
    "http://fmjwfje:a2dg@84.247.125.21:6095",
    "http://fmjwfje:a2dg@216.159.3.7:6837",
    "http://fmjwfje:a2dg@142.67.45.12:5611",
    "http://fmjwfje:a2dg@142.128.95.8:6593"
]

proxy_fail_counts = {p:0 for p in PROXIES}
proxy_health_cache = {}

# =============================================
# Functions

def load_links():
    try:
        with open(LINKS_FILE,"r") as f:
            links = json.load(f)
            if not links:
                raise Exception("Empty")
            return links
    except Exception:
        return LINKS_DEFAULT.copy()

def save_links(links):
    with open(LINKS_FILE,"w") as f:
        json.dump(links,f,indent=2)

def generate_id(byte_count=8):
    return secrets.token_hex(byte_count)

def is_proxy_alive(proxy_string):
    try:
        headers = {"User-Agent":random.choice(user_agents_list)}
        r=requests.get("https://httpbin.org/ip", proxies={"http":proxy_string,"https":proxy_string}, headers=headers, timeout=3)
        return r.status_code==200
    except:
        return False

def get_next_proxy():
    with proxy_lock:
        alive = []
        for p in list(PROXIES):
            if p in proxy_health_cache:
                if proxy_health_cache[p]:
                    alive.append(p)
                else:
                    proxy_fail_counts[p]+=1
                    if proxy_fail_counts[p]>=3:
                        PROXIES.remove(p)
                        logging.warning(f"Removed proxy {p} due to failures")
            else:
                alive_p_ = is_proxy_alive(p)
                proxy_health_cache[p]=alive_p_
                if alive_p_:
                    alive.append(p)
                else:
                    proxy_fail_counts[p] = proxy_fail_counts.get(p,0)+1
        if not alive:
            logging.error("No working proxies")
            return None
        choice=random.choice(alive)
        return {"http":choice,"https":choice}

def fetch_cpc():
    # Placeholder: simulate CPC value
    return round(0.05 + random.random()*0.15, 4)

def smart_delay(base_time):
    return base_time * random.uniform(0.8, 1.2)

def check_achievements(stats, bot):
    new_achievements = []
    for milestone in list(bot["milestones"]):
        if stats["revenue"] >= milestone:
            new_achievements.append(f"Milestone ${milestone}")
            bot["milestones"].remove(milestone)
    if stats["clicks"] >= 100 and "Century Club" not in bot["achievements"]:
        new_achievements.append("Century Club")
        bot["achievements"].append("Century Club")
    if stats["imps"] >= 1000 and "Impression Master" not in bot["achievements"]:
        new_achievements.append("Impression Master")
        bot["achievements"].append("Impression Master")
    return new_achievements

def create_session():
    sess = requests.Session()
    sess.headers.update({"User-Agent":random.choice(user_agents_list)})
    return sess

def perform_click(session, url, proxy):
    try:
        resp = session.get(url, proxies=proxy, timeout=10)
        resp.raise_for_status()
        return resp.status_code==200
    except Exception as e:
        logging.warning(f"Error clicking url: {e}")
        return False

def selenium_click(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument(f"user-agent={random.choice(user_agents_list)}")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(random.uniform(5,10))
        action = webdriver.ActionChains(driver)
        action.move_by_offset(random.randint(5,200),random.randint(5,200)).perform()
        time.sleep(random.uniform(1,3))
        driver.execute_script("window.scrollBy(0, window.innerHeight/2)")
        time.sleep(random.uniform(3,5))
    except WebDriverException as e:
        logging.error(f"Selenium error: {e}")
    finally:
        driver.quit()

def ai_bot_worker(name):
    bot = ai_bots_cfg[name]
    session = create_session()
    logging.info(f"Bot {bot['name']} started")
    while True:
        if not bot["clicking_active"]:
            time.sleep(1)
            continue
        links = load_links()
        if not links:
            time.sleep(5)
            continue

        chosen = random.choices(links, weights=[l["weight"] for l in links])[0]
        url = chosen["url"].replace("{SOURCE_ID}", generate_id(6)).replace("{CLICK_ID}", generate_id(8))
        proxy = get_next_proxy()

        use_selenium = random.random() < 0.3
        success = False
        if use_selenium:
            try:
                selenium_click(url)
                success = True
            except Exception as e:
                logging.warning(f"Selenium click failed: {e}")
                success = False
        else:
            success = perform_click(session, url, proxy)

        if success:
            with lock:
                cpc = fetch_cpc()
                stats["clicks"] += 1
                stats["revenue"] += cpc
                stats["imps"] += 1
                stats["last_update"] = datetime.now().isoformat()
                achs = check_achievements(stats, bot)
                for a in achs:
                    logging.info(f"{bot['name']} achieved: {a}")

        time.sleep(smart_delay(bot["click_rate"]))

# Flask routes
@app.route("/stats")
def stats_api():
    with lock:
        ctr = (stats["clicks"] / stats["imps"] * 100) if stats["imps"] else 0
        return jsonify({**stats, "ctr": round(ctr, 2)})

@app.route("/links", methods=["GET", "POST"])
def links_api():
    if request.method == "GET":
        return jsonify(load_links())
    data = request.get_json()
    if not data or "network" not in data or "url" not in 
        return jsonify({"error": "Missing fields"}), 400
    links = load_links()
    new_id = max([l["id"] for l in links], default=0) + 1
    new_link = {"id": new_id, "network": data["network"], "url": data["url"], "weight": 1.0}
    links.append(new_link)
    save_links(links)
    return jsonify(new_link), 201

@app.route("/command", methods=["POST"])
def commands_api():
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    with lock:
        if action == "przelacz_drogi":
            for bot in ai_bots_cfg.values():
                bot["expensive_mode"] = not bot["expensive_mode"]
            return jsonify({"message": "Toggled expensive mode"})
        if action == "przelacz_turbo":
            for bot in ai_bots_cfg.values():
                bot["turbo_mode"] = not bot["turbo_mode"]
            return jsonify({"message": "Toggled turbo mode"})
        if action == "przelacz_ukryty":
            for bot in ai_bots_cfg.values():
                bot["stealth_mode"] = not bot["stealth_mode"]
            return jsonify({"message": "Toggled stealth mode"})
        if action == "zwieksz_przychod":
            stats["revenue"] += 10
            return jsonify({"message": "Increased revenue by 10", "revenue": stats["revenue"]})
        if action == "resetuj":
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0, "pending": 0})
            for bot in ai_bots_cfg.values():
                bot["history"].clear()
                bot["achievements"].clear()
            return jsonify({"message": "Stats and bots reset", "stats": stats})
        if action == "ustaw_click_rate":
            val = data.get("value")
            try:
                val = float(val)
            except:
                return jsonify({"error": "Invalid click rate"}), 400
            for bot in ai_bots_cfg.values():
                bot["click_rate"] = max(bot["min_rate"], min(val, bot["max_rate"]))
            return jsonify({"message": f"Set click rate to {val}"})
        if action == "start_klikanie":
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = True
            return jsonify({"message": "Started clicking"})
        if action == "stop_klikanie":
            for bot in ai_bots_cfg.values():
                bot["clicking_active"] = False
            return jsonify({"message": "Stopped clicking"})
        if action == "start_oglądanie":
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = True
            return jsonify({"message": "Started watching"})
        if action == "stop_oglądanie":
            for bot in ai_bots_cfg.values():
                bot["watching_active"] = False
            return jsonify({"message": "Stopped watching"})
        return jsonify({"error": "Unknown command"}), 400

@app.route("/huggingface_chat", methods=["POST"])
def huggingface_chat():
    data = request.get_json()
    if not data or "message" not in 
        return jsonify({"error": "Missing message"}), 400
    message = data["message"]
    token = os.getenv("HUGGINGFACE_API_KEY", "")
    if not token:
        return jsonify({"error": "Missing Huggingface API key"}), 500
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://api-inference.huggingface.co/models/gpt2",
                             headers=headers,
                             json={"inputs": message, "options": {"wait_for_model": True}})
    if response.status_code != 200:
        return jsonify({"error": "Huggingface API error", "details": response.text}), 500
    data_resp = response.json()
    text_response = ""
    if isinstance(data_resp, list) and data_resp:
        text_response = data_resp[0].get("generated_text", "").strip()
    lmsg = message.lower()
    command_response = ""
    with lock:
        if "aktywuj supermode" in lmsg:
            # Implement supermode start
            command_response = "Supermode activated"
        elif "dezaktywuj supermode" in lmsg:
            # Implement supermode stop
            command_response = "Supermode deactivated"
        else:
            command_response = "Command not recognized"
    return jsonify({"model_response": text_response, "command_response": command_response})

@app.route("/")
def index():
    try:
        return open("web/index.html").read()
    except:
        return "<h1>AI Clicker Platform</h1><p>Index file missing</p>"

@app.route("/scan", methods=["POST"])
def scan():
    # Placeholder scan endpoint
    return jsonify({"message": "Scan started (placeholder)"})

if __name__ == "__main__":
    logging.info(f"Starting app on port {PORT}")
    for bot_name in ai_bots_cfg:
        bot = ai_bots_cfg[bot_name]
        bot["clicking_active"] = True
        bot["watching_active"] = True
        threading.Thread(target=ai_bot_worker, args=(bot_name,), daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
