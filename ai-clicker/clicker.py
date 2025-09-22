import os
import time
import random
import requests
from threading import Thread
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Stats
stats = {"imps": 0, "clicks": 0}

def ai_face_loop():
    """Headless browsing co 10 sekund."""
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_opts)
    url = os.getenv('TARGET_URL')  # np. strona z reklamą

    while True:
        try:
            driver.get(url)
            stats["imps"] += 1
            # kliknij reklamę jeżeli widoczna
            ads = driver.find_elements("css selector", ".ad-button")
            if ads and random.random() < float(os.getenv('CLICK_RATE', '0.20')):
                ads[0].click()
                stats["clicks"] += 1
        except Exception:
            pass
        time.sleep(10)

@app.route('/')
def dashboard():
    return f"""
<!DOCTYPE html>
<html>
<head><title>Ad Mining Dashboard</title></head>
<body style="font-family:Arial;margin:20px;">
<h1>Ad Mining Platform</h1>
<p>Impressions: {stats['imps']}</p>
<p>Clicks: {stats['clicks']}</p>
<button onclick="fetch('/scan',{{method:'POST'}}).then(()=>location.reload())">
  Magnes na reklamy
</button>
</body>
</html>
"""

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    # Ręczny trigger, nadal dostępny
    stats["imps"] += 1
    if random.random() < float(os.getenv('CLICK_RATE', '0.20')):
        stats["clicks"] += 1
    return jsonify(stats)

@app.route('/stats')
def get_stats():
    return jsonify(stats)

if __name__ == '__main__':
    Thread(target=auto_scan_loop, daemon=True).start()
    Thread(target=ai_face_loop, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
