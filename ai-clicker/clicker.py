import os
import json
import time
import random
import threading
import requests
import logging
import secrets
import re
import numpy as np
import hashlib
from datetime import datetime
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sock import Sock
from dotenv import load_dotenv
from functools import wraps
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Inicjalizacja Flask
app = Flask(__name__)
CORS(app)
sock = Sock(app)
load_dotenv()

def get_driver():
    """Zwraca skonfigurowany driver Chrome w trybie headless dla Render.com"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Przykład użycia:
# driver = get_driver()
# try:
#     driver.get("https://example.com")
#     print(driver.title)
# finally:
#     driver.quit()

load_dotenv()

app = Flask(__name__)
CORS(app)
sock = Sock(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
lock = threading.Lock()
proxy_lock = threading.Lock()

PORT = int(os.getenv("PORT", "5000"))

# Global stats
stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0,
    "pending": 0,
    "last_update": datetime.now().isoformat()
}

# User agents list to rotate
user_agents_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)"
]

# AI bots config with various modes and parameters
ai_bots_cfg = {
    "Bot1": {
        "name": "HelperBot",
        "click_rate": 0.15,
        "interval": 3.0,
        "clicking_active": True,
        "watching_active": True,
        "history": [],
        "achievements": [],
        "milestones": [10, 20, 50, 100],
        "expensive_mode": False,
        "turbo_mode": False,
        "stealth_mode": True,
        "min_rate": 0.05,
        "max_rate": 0.5,
        "error_window": []
    },
    "Bot2": {
        "name": "TurboBot",
        "click_rate": 0.35,
        "interval": 2.0,
        "clicking_active": True,
        "watching_active": True,
        "history": [],
        "achievements": [],
        "milestones": [10, 25, 60, 120],
        "expensive_mode": False,
        "turbo_mode": True,
        "stealth_mode": False,
        "min_rate": 0.1,
        "max_rate": 0.8,
        "error_window": []
    },
    "Bot3": {
        "name": "StealthBot",
        "click_rate": 0.1,
        "interval": 4.0,
        "clicking_active": True,
        "watching_active": True,
        "history": [],
        "achievements": [],
        "milestones": [5, 15, 40, 90],
        "expensive_mode": True,
        "turbo_mode": False,
        "stealth_mode": True,
        "min_rate": 0.05,
        "max_rate": 0.4,
        "error_window": []
    },
    "Bot4": {
        "name": "BoosterBot",
        "click_rate": 0.25,
        "interval": 3.5,
        "clicking_active": True,
        "watching_active": True,
        "history": [],
        "achievements": [],
        "milestones": [20, 50, 100, 200],
        "expensive_mode": False,
        "turbo_mode": True,
        "stealth_mode": True,
        "min_rate": 0.1,
        "max_rate": 0.7,
        "error_window": []
    },
}

LINKS_FILE = "links.json"
LINKS_DEFAULT = [
    {"id": 1, "network": "Zeydoo A", "url": "https://ldl1.com/link?z=9917741&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 2, "network": "Zeydoo B", "url": "https://sgben.com/link?z=9917747&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 3, "network": "Zeydoo C", "url": "https://92orb.com/link?z=9917751&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 4, "network": "Zeydoo D", "url": "https://92orb.com/link?z=9917754&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 5, "network": "Zeydoo E", "url": "https://ldl1.com/link?z=9917757&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 6, "network": "Zeydoo F", "url": "https://ovret.com/link?z=9917758&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 7, "network": "Zeydoo G", "url": "https://92orb.com/link?z=9917759&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 8, "network": "Zeydoo H", "url": "https://92orb.com/link?z=9917766&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 9, "network": "Zeydoo J", "url": "https://134l.com/link?z=9917767&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 10, "network": "Hshsh", "url": "https://ldl1.com/link?z=9917775&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 11, "network": "Jsjsj", "url": "https://sgben.com/link?z=9917779&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 12, "network": "Hsh", "url": "https://92orb.com/link?z=9917780&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 13, "network": "Ldld", "url": "https://ldl1.com/link?z=9917784&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
    {"id": 14, "network": "Ksjsb", "url": "https://92orb.com/link?z=9917785&var={SOURCE_ID}&ymid={CLICK_ID}", "weight": 1.0},
]

def load_links():
    try:
        with open(LINKS_FILE, "r") as f:
            links = json.load(f)
            if not links:
                raise Exception("Empty links file")
            return links
    except Exception:
        return LINKS_DEFAULT.copy()

def save_links(links):
    with open(LINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)


PROXIES = [
    # Nowa lista proxy bez uwierzytelnienia
    "http://78.9.234.55:8080",
    "http://151.115.55.121:8080",
    "http://217.142.4.601:8080",
    "http://232.205.78.9:8080",
    "http://234.55.78.9:8080",
    "http://85.193.197.137:8081",
    "http://37.26.192.4:8081",
    "http://83.175.157.49:3128",
    "http://78.9.232.205:8080",
    "http://78.9.234.56:8080",
    "http://151.115.55.122:8080",
    "http://217.142.4.602:8080",
    "http://232.205.78.10:8080",
    "http://234.55.78.10:8080",
    "http://85.193.197.138:8081",
    "http://37.26.192.5:8081",
    "http://83.175.157.50:3128",
    "http://78.9.232.206:8080",
    "http://78.9.234.57:8080",
    "http://151.115.55.123:8080",
    "http://217.142.4.603:8080",
    "http://232.205.78.11:8080",
    "http://234.55.78.11:8080",
    "http://85.193.197.139:8081",
    "http://37.26.192.6:8081",
    "http://83.175.157.51:3128",
    "http://78.9.232.207:8080",
    "http://78.9.234.58:8080",
    "http://151.115.55.124:8080",
    "http://217.142.4.604:8080",
    "http://232.205.78.12:8080",
    "http://234.55.78.12:8080",
    "http://85.193.197.140:8081",
    "http://37.26.192.7:8081",
    "http://83.175.157.52:3128",
    "http://78.9.232.208:8080",
    "http://78.9.234.59:8080",
    "http://151.115.55.125:8080",
    "http://217.142.4.605:8080",
    "http://232.205.78.13:8080",
    "http://234.55.78.13:8080",
    "http://85.193.197.141:8081",

    # Twoje stare proxy HTTP z autoryzacją
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

proxy_health_cache = {}
proxy_fail_counts = {}

def load_links():
    try:
        with open(LINKS_FILE, "r") as f:
            links = json.load(f)
            if not links:
                raise Exception("Empty links file")
            return links
    except Exception:
        return LINKS_DEFAULT.copy()

def save_links(links):
    with open(LINKS_FILE, "w") as f:
        json.dump(links, f, indent=2)

def generate_unique_id(num_bytes=8):
    return secrets.token_hex(num_bytes)

def proxy_health_check(proxy_url):
    try:
        headers = {"User-Agent": random.choice(user_agents_list)}
        resp = requests.get("https://www.google.com", proxies={"http": proxy_url, "https": proxy_url}, headers=headers, timeout=5)
        # Uznać za działające także status 204 (No Content)
        if resp.status_code in [200, 204, 302, 301]:
            return True
        else:
            logging.warning(f"Proxy {proxy_url} zwróciło status {resp.status_code}")
            return False
    except Exception as e:
        logging.warning(f"Błąd proxy {proxy_url}: {e}")
        return False

def get_next_proxy():
    with proxy_lock:
        alive_proxies = []
        # Inicjalizacja liczników, jeśli puste
        for p in PROXIES:
            if p not in proxy_fail_counts:
                proxy_fail_counts[p] = 0

        for proxy in PROXIES[:]:
            if proxy in proxy_health_cache:
                if proxy_health_cache[proxy]:
                    alive_proxies.append(proxy)
                else:
                    proxy_fail_counts[proxy] += 1
                    if proxy_fail_counts[proxy] >= 10:  # zwiększony limit prób
                        logging.warning(f"Usuwanie proxy {proxy} po {proxy_fail_counts[proxy]} nieudanych próbach")
                        PROXIES.remove(proxy)
                        proxy_fail_counts.pop(proxy, None)
                        proxy_health_cache.pop(proxy, None)
            else:
                if proxy_health_check(proxy):
                    proxy_health_cache[proxy] = True
                    alive_proxies.append(proxy)
                else:
                    proxy_health_cache[proxy] = False
                    proxy_fail_counts[proxy] = proxy_fail_counts.get(proxy, 0) + 1
        if not alive_proxies:
            logging.error("Brak dostępnych proxy")
            return None
        chosen = random.choice(alive_proxies)
        return {"http": chosen, "https": chosen}

def fetch_cpc():
    proxy = get_next_proxy()
    headers = {"User-Agent": random.choice(user_agents_list)}
    try:
        # Tutaj możesz podmienić na realne API pobierania CPC
        # Przykład fetchu z endpointa (zakomentowany):
        # if proxy is not None:
        #     resp = requests.get("https://twoja-api-cpc.com/fetch", proxies=proxy, headers=headers, timeout=5)
        #     if resp.status_code == 200:
        #         data = resp.json()
        #         return float(data.get("cpc", 0.1))
        #     else:
        #         logging.warning(f"CPC fetch failed with status {resp.status_code}")
        #         return 0.1
        # else:
        #     logging.warning("No proxy available for CPC fetch")
        #     return 0.1

        # Symulacja losowego CPC, moduluje przychód, można rozszerzyć
        return round(0.05 + random.random() * 0.15, 4)
    except Exception as e:
        logging.warning(f"Pobieranie CPC nie powiodło się: {e}")
        return 0.1

def smart_delay(base):
    # Losowa modyfikacja czasu opóźnienia, by działać bardziej naturalnie
    return base * random.uniform(0.8, 1.2)

def check_achievements(stats, bot):
    new_achievements = []
    # Sprawdzanie kamieni milowych przychodu
    for milestone in bot["milestones"][:]:  # kopia listy milestonów, by można usuwać
        if stats["revenue"] >= milestone:
            new_achievements.append(f"💰 Milestone reached: ${milestone}")
            bot["milestones"].remove(milestone)
    # Dodatkowe osiągnięcia przy kliknięciach i wyświetleniach
    if stats["clicks"] >= 100 and "Century Club" not in bot["achievements"]:
        new_achievements.append("🎯 Century Club - 100 clicks")
        bot["achievements"].append("Century Club")
    if stats["imps"] >= 1000 and "Impression Master" not in bot["achievements"]:
        new_achievements.append("👁️ Impression Master - 1000 impressions")
        bot["achievements"].append("Impression Master")
    return new_achievements

# Supermode and megascan control variables and locks
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

def monitor_and_adapt(bot, error_rate_threshold=0.2):
    error_window = bot.get("error_window", [])
    error_rate = np.mean(error_window) if error_window else 0
    if error_rate > error_rate_threshold:
        bot["expensive_mode"] = not bot["expensive_mode"]
        bot["turbo_mode"] = not bot["turbo_mode"]
        logging.info(f"Bot {bot['name']} zmienił tryb z powodu wysokiego error rate: {error_rate}")
    # Clear error history after adaptation
    bot["error_window"] = []

def ai_bot_worker(bot_name):
    bot = ai_bots_cfg[bot_name]
    logging.info(f"Bot '{bot['name']}' started")
    global supermode_active, supermode_end_time, mega_scan_active, mega_scan_end_time

    session = requests.Session()
    session.headers.update({"User-Agent": random.choice(user_agents_list)})

    counter = 0

    while True:
        with supermode_lock:
            if supermode_active and time.time() > supermode_end_time:
                logging.info("Supermode expired, deactivating")
                stop_supermode()

        with mega_scan_lock:
            if mega_scan_active and time.time() > mega_scan_end_time:
                logging.info("Mega scan expired, deactivating")
                mega_scan_active = False
            mega_active = mega_scan_active

        links = load_links()
        if not links:
            time.sleep(5)
            continue

        selected_link = random.choice(links)["url"]
        unique_source = generate_unique_id(6)
        unique_click = generate_unique_id(8)
        url = selected_link.replace("{SOURCE_ID}", unique_source).replace("{CLICK_ID}", unique_click)
        proxy = get_next_proxy()

        if not bot["clicking_active"]:
            time.sleep(bot["interval"])
            continue

        try:
            response = session.get(url, proxies=proxy, timeout=15)
            if response.status_code == 200:
                with lock:
                    cpc = fetch_cpc()
                    stats["clicks"] += 1
                    stats["revenue"] += cpc
                    stats["imps"] += 1 if not mega_active else 4
                    stats["last_update"] = datetime.now().isoformat()
                logging.info(f"Bot '{bot['name']}' clicked URL successfully")
                bot["error_window"].append(0)
            else:
                logging.warning(f"Bot '{bot['name']}' received status {response.status_code} for URL")
                bot["error_window"].append(1)
        except Exception as e:
            logging.error(f"Bot '{bot['name']}' error during click: {e}")
            bot["error_window"].append(1)

        with lock:
            if mega_active:
                stats["imps"] += 3
                stats["revenue"] += 0.1

            if bot["expensive_mode"]:
                stats["revenue"] += 0.01
            if bot["turbo_mode"]:
                stats["imps"] += 1
            if bot["stealth_mode"] and random.random() < 0.1:
                stats["clicks"] = max(0, stats["clicks"] - 1)

            bot["history"].append(stats["revenue"])
            if len(bot["history"]) > 50:
                bot["history"].pop(0)

            achievements_new = check_achievements(stats, bot)
            for ach in achievements_new:
                logging.info(f"{bot['name']} achieved: {ach}")

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

        counter += 1
        if counter >= 50:
            monitor_and_adapt(bot)
            counter = 0

        time.sleep(smart_delay(bot["interval"]))

@app.route("/stats")
def api_stats():
    with lock:
        ctr = (stats["clicks"] / stats["imps"] * 100) if stats["imps"] > 0 else 0
        return jsonify({**stats, "ctr": round(ctr, 2)})



@app.route("/command", methods=["POST"])
def api_command():
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
            stats["revenue"] += 10.0
            return jsonify({"message": "Increased revenue by 10", "revenue": stats["revenue"]})

        if action == "resetuj":
            stats.update(imps=0, clicks=0, revenue=0.0, pending=0)
            for bot in ai_bots_cfg.values():
                bot["history"].clear()
                bot["achievements"].clear()
            return jsonify({"message": "Stats and bots reset", "stats": stats})

        if action == "ustaw_click_rate":
            val = data.get("value")
            try:
                val = float(val)
            except Exception:
                return jsonify({"error": "Invalid click rate"}), 400
            for bot in ai_bots_cfg.values():
                bot["click_rate"] = max(bot["min_rate"], min(val, bot["max_rate"]))
            return jsonify({"message": f"Click rate set to {val}"})

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

        if action == "aktywuj_supermode":
            start_supermode(6000)  # 6000 seconds
            return jsonify({"message": "Supermode activated for 6000 seconds"})

        if action == "dezaktywuj_supermode":
            stop_supermode()
            return jsonify({"message": "Supermode deactivated"})

        if action == "start_mega_scan":
            start_mega_scan(3000)  # 3000 seconds
            return jsonify({"message": "Mega scan activated for 3000 seconds"})

    return jsonify({"error": "Unknown command"}), 400

@app.route("/huggingface_chat", methods=["POST"])
def api_huggingface_chat():
    data = request.get_json()

    # Poprawiony warunek: dodane "data" po "message" not in
    if not data or "message" not in data:
        return jsonify({"error": "Missing message"}), 400

    message = data["message"]

    # Tutaj dodaj logikę obsługi wiadomości (np. wywołanie API Hugging Face)
    # Przykład:
    # response = query_huggingface(message)
    # return jsonify({"response": response})

    return jsonify({"status": "success", "received_message": message})

    token = os.getenv("HUGGINGFACE_API_KEY", "")
    if not token:
        return jsonify({"error": "Missing Huggingface API key"}), 500

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        "https://api-inference.huggingface.co/models/gpt2",
        headers=headers,
        json={"inputs": message, "options": {"wait_for_model": True}}
    )
    if resp.status_code != 200:
        return jsonify({"error": "Huggingface API error", "details": resp.text}), 500
    data_res = resp.json()
    text_response = ""
    if isinstance(data_res, list) and data_res:
        text_response = data_res[0].get("generated_text", "").strip()

    command_response = ""
    lmsg = message.lower()

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
    except Exception:
        return "<h1>AI Clicker Platform</h1><p>Index file missing</p>"

@app.route("/scan", methods=["POST"])
def api_scan():
    start_mega_scan(3000)
    return jsonify({"message": "Mega scan started for 3000 seconds"})

# Realistic Selenium click simulation
def selenium_click(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            pass
        time.sleep(random.uniform(3, 6))

        action = ActionChains(driver)
        for _ in range(random.randint(3,7)):
            action.move_by_offset(random.randint(10,300), random.randint(10,300)).perform()
            time.sleep(random.uniform(0.3,1.2))

        driver.execute_script("window.scrollBy(0, window.innerHeight / 2)")
        time.sleep(random.uniform(2,4))
        driver.execute_script("window.scrollBy(0, -window.innerHeight / 2)")
        time.sleep(random.uniform(1,2))

        try:
            clickable_elements = driver.find_elements(By.TAG_NAME, "a")
            if clickable_elements:
                chosen = random.choice(clickable_elements)
                action.move_to_element(chosen).click().perform()
                time.sleep(random.uniform(2,5))
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"Selenium error: {e}")
        return False
    finally:
        driver.quit()

# Proxy auto-refresh
def proxy_auto_refresh():
    global PROXIES, proxy_fail_counts, proxy_health_cache
    to_remove = [p for p, count in proxy_fail_counts.items() if count >= 3]
    for p in to_remove:
        if p in PROXIES:
            PROXIES.remove(p)
        proxy_fail_counts.pop(p, None)
        proxy_health_cache.pop(p, None)

    # Example adding new proxies - replace with real API or source
    if len(PROXIES) < 5:
        new_proxies = ["http://newproxy1:8080", "http://newproxy2:8080"]
        PROXIES.extend(new_proxies)
        for p in new_proxies:
            proxy_fail_counts[p] = 0
            proxy_health_cache[p] = True

# Analytics report with auth decorator
AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "secret-token")

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token != f"Bearer {AUTH_TOKEN}":
            abort(401, description="Unauthorized")
        return f(*args, **kwargs)
    return wrapper

def get_analytics_report():
    with lock:
        return {
            "total_clicks": stats["clicks"],
            "total_impressions": stats["imps"],
            "total_revenue": round(stats["revenue"], 4),
            "bots": {bot["name"]: {
                "achievements": bot["achievements"],
                "click_rate": bot["click_rate"],
                "expensive_mode": bot["expensive_mode"],
                "turbo_mode": bot["turbo_mode"],
                "stealth_mode": bot["stealth_mode"]
            } for bot in ai_bots_cfg.values()}
        }

@app.route("/analytics")
@require_auth
def api_analytics():
    return jsonify(get_analytics_report())

# WebSocket status updates
@sock.route('/ws_status')
def ws_status(ws):
    while True:
        with lock:
            data = {
                "clicks": stats["clicks"],
                "impressions": stats["imps"],
                "revenue": round(stats["revenue"], 4)
            }
        ws.send(json.dumps(data))
        time.sleep(2)

# Simple blockchain for stats
class SimpleBlockchain:
    def __init__(self):
        self.chain = []
        self.create_block(previous_hash='0')

    def create_block(self, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'clicks': stats["clicks"],
            'imps': stats["imps"],
            'revenue': stats["revenue"],
            'previous_hash': previous_hash
        }
        block['hash'] = self.hash(block)
        self.chain.append(block)
        return block

    def hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def get_last_block(self):
        return self.chain[-1]

blockchain = SimpleBlockchain()

def record_click_to_blockchain():
    last_hash = blockchain.get_last_block()['hash']
    blockchain.create_block(previous_hash=last_hash)

# Call record_click_to_blockchain() in ai_bot_worker after successful click if needed

if __name__ == "__main__":
    logging.info(f"Starting AI Clicker on port {PORT}")
    for bot_name in ai_bots_cfg:
        bot = ai_bots_cfg[bot_name]
        bot["clicking_active"] = True
        bot["watching_active"] = True
    for bot_name in ai_bots_cfg:
        thread = threading.Thread(target=ai_bot_worker, args=(bot_name,), daemon=True)
        thread.start()
    app.run(host="0.0.0.0", port=PORT)
