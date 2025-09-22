import os
import time
import random
import requests
from threading import Thread
from flask import Flask, request, jsonify

app = Flask(__name__)

# Stats
stats = {"imps": 0, "clicks": 0}

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
<button onclick="fetch('/scan',{{method:'POST'}}).then(()=>location.reload())">Magnes na reklamy</button>
</body>
</html>
"""

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    stats["imps"] += 1
    
    # Symulacja kliknięcia z prawdopodobieństwem
    if random.random() < float(os.getenv('CLICK_RATE', '0.20')):
        stats["clicks"] += 1
        
    return jsonify(stats)

@app.route('/stats')
def get_stats():
    return jsonify(stats)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
