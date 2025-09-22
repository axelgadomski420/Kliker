import os
import time
import random
from threading import Thread
from flask import Flask, jsonify

app = Flask(__name__)

# Statystyki
stats = {"imps": 0, "clicks": 0, "revenue": 0.0}

def auto_scan_loop():
    """Automatycznie generuje odsłony i kliknięcia co 5 sekund."""
    while True:
        stats["imps"] += 1
        if random.random() < float(os.getenv('CLICK_RATE', '0.20')):
            stats["clicks"] += 1
        stats["revenue"] = round(stats["clicks"] * float(os.getenv('CPC', '0.05')), 2)
        time.sleep(5)

@app.route('/')
def dashboard():
    # Zwraca prosty HTML dashboard z kartami i przyciskiem (ładny CSS można dodać statycznie lub inline)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ad Mining Dashboard</title>
<style>
body {{
  font-family: Arial,sans-serif;
  background: #f0f2f5;
  margin: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}}
h1 {{
  margin-bottom: 20px;
  color: #333;
}}
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  width: 100%;
  max-width: 800px;
  margin-bottom: 30px;
}}
.card {{
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}}
.card h2 {{
  margin: 0 0 10px;
  font-size: 2.2em;
  color: #007bff;
}}
.card p {{
  margin: 0;
  color: #555;
  font-size: 0.9em;
}}
button {{
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  background: #28a745;
  color: #fff;
  font-size: 1em;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  transition: background 0.2s;
}}
button:hover {{
  background: #218838;
}}
#msg {{
  margin-top: 15px;
  color: #28a745;
  font-weight: bold;
}}
</style>
</head>
<body>
<h1>Ad Mining Platform</h1>

<div class="stats">
  <div class="card"><h2 id="imps">{stats['imps']}</h2><p>Impressions</p></div>
  <div class="card"><h2 id="clicks">{stats['clicks']}</h2><p>Clicks</p></div>
  <div class="card"><h2 id="ctr">{(100 * stats['clicks']/max(stats['imps'],1)):.2f}%</h2><p>CTR</p></div>
  <div class="card"><h2>${stats['revenue']:.2f}</h2><p>Revenue</p></div>
</div>

<button onclick="manualScan()">Magnes na reklamy</button>
<div id="msg"></div>

<script>
async function fetchStats() {{
  try {{
    const res = await fetch('/stats');
    const data = await res.json();
    document.getElementById('imps').innerText = data.imps;
    document.getElementById('clicks').innerText = data.clicks;
    document.getElementById('ctr').innerText = ((data.clicks/data.imps||0)*100).toFixed(2) + '%';
    document.getElementById('revenue').innerText = data.revenue.toFixed(2);
  }} catch(e) {{
    console.error('Failed to fetch stats:', e);
  }}
}}

async function manualScan() {{
  try {{
    await fetch('/scan', {{ method: 'POST' }});
    document.getElementById('msg').innerText = 'Magnes uruchomiony!';
    setTimeout(() => document.getElementById('msg').innerText = '', 3000);
    fetchStats();
  }} catch(e) {{
    console.error('Manual scan failed:', e);
  }}
}}

setInterval(fetchStats, 5000);
fetchStats();
</script>
</body>
</html>"""

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    stats["imps"] += 1
    if random.random() < float(os.getenv('CLICK_RATE', '0.20')):
        stats["clicks"] += 1
    stats["revenue"] = round(stats["clicks"] * float(os.getenv('CPC', '0.05')), 2)
    return jsonify(stats)

@app.route('/stats')
def get_stats():
    return jsonify(stats)

if __name__ == '__main__':
    Thread(target=auto_scan_loop, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
