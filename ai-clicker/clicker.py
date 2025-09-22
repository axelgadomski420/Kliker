import os, time, random, threading, requests, json
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__, static_folder=None)

# ═══════════════════════════════════════════════════════════════
#  EXTRA AD MINING PLATFORM - ULTIMATE VERSION WITH IQ 777
# ═══════════════════════════════════════════════════════════════

# Global stats & AI settings
stats = {"imps": 0, "clicks": 0, "revenue": 0.0, "time": datetime.now().isoformat()}
lock = threading.Lock()
ai = {
    "click_rate": float(os.getenv("CLICK_RATE", "0.20")),
    "expensive_mode": False,
    "turbo_mode": False,
    "stealth_mode": True,
    "min_rate": 0.05,
    "max_rate": 0.80,
    "interval": 3.0,
    "history": [],
    "milestones": [10, 50, 100, 250, 500, 1000],
    "achievements": [],
    "proxy_rotation": True,
    "smart_timing": True
}

# Premium proxy pool (mix of working & mock addresses)
PROXIES = [
    "http://51.158.68.68:8811",
    "http://192.99.56.244:80", 
    "http://45.77.24.239:8080",
    "http://165.16.64.198:8800",
    "http://159.89.49.217:3128",
    "http://103.28.118.57:80",
    "http://45.167.123.69:999",
    "http://194.67.91.153:80"
]

# ═══════════════════════════════════════════════════════════════
#  ADVANCED AI FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_random_proxy():
    """Smart proxy rotation with fallback"""
    if not ai["proxy_rotation"]:
        return None
    proxy = random.choice(PROXIES)
    return {"http": proxy, "https": proxy}

def fetch_premium_cpc():
    """Advanced CPC fetching with proxy rotation and fallback"""
    try:
        proxy = get_random_proxy()
        headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random.randint(537,539)}.36",
            "Accept": "application/json,text/html,*/*",
        }
        # Mock premium API call
        r = requests.get("https://httpbin.org/json", 
                        proxies=proxy, headers=headers, timeout=2)
        mock_cpc = 0.05 + (random.random() * 0.15)  # 0.05-0.20 dynamic CPC
        return mock_cpc
    except:
        return ai["click_rate"]

def smart_timing_multiplier():
    """Peak hours optimization (6-9AM, 6-11PM = higher rates)"""
    if not ai["smart_timing"]:
        return 1.0
    hour = datetime.now().hour
    if 6 <= hour <= 9 or 18 <= hour <= 23:
        return 1.5  # 50% boost during peak hours
    elif 0 <= hour <= 6:
        return 0.7  # 30% reduction during night hours
    return 1.0

def adaptive_strategy():
    """Ultra-advanced strategy adjustment every 45s"""
    while True:
        time.sleep(45)
        with lock:
            h = ai["history"]
            if len(h) >= 5:
                trend = sum(h[-3:]) / 3 - sum(h[-5:-2]) / 3
                if trend > 0:  # Revenue increasing
                    ai["click_rate"] = min(ai["click_rate"] * 1.05, ai["max_rate"])
                    ai["interval"] = max(ai["interval"] * 0.95, 1.0)
                else:  # Revenue stagnating
                    ai["click_rate"] = max(ai["click_rate"] * 0.98, ai["min_rate"])
                    ai["interval"] = min(ai["interval"] * 1.02, 8.0)

def check_achievements():
    """Advanced achievement system"""
    revenue = stats["revenue"]
    clicks = stats["clicks"]
    
    achievements = []
    for milestone in ai["milestones"][:]:
        if revenue >= milestone:
            achievement = f"💰 ${milestone} Revenue Milestone!"
            achievements.append(achievement)
            ai["milestones"].remove(milestone)
    
    # Special achievements
    if clicks == 100 and "First Century" not in ai["achievements"]:
        achievements.append("🎯 First Century - 100 clicks!")
        ai["achievements"].append("First Century")
    
    if stats["imps"] >= 1000 and "Impression Master" not in ai["achievements"]:
        achievements.append("👁️ Impression Master - 1000 views!")
        ai["achievements"].append("Impression Master")
    
    return achievements

# ═══════════════════════════════════════════════════════════════
#  QUAD-CORE SCANNING ENGINE
# ═══════════════════════════════════════════════════════════════

def premium_scan_engine(worker_id):
    """Ultimate scanning engine with all advanced features"""
    worker_stats = {"scans": 0, "success": 0}
    
    while True:
        try:
            # Dynamic CPC fetching
            cpc = fetch_premium_cpc()
            timing_boost = smart_timing_multiplier()
            
            with lock:
                # Update global AI settings
                ai["click_rate"] = min(max(cpc, ai["min_rate"]), ai["max_rate"])
                
                # Generate impression
                stats["imps"] += 1
                worker_stats["scans"] += 1
                
                # Calculate dynamic click rate
                base_rate = ai["click_rate"] * timing_boost
                if ai["expensive_mode"]:
                    base_rate *= 2.0
                if ai["turbo_mode"]:
                    base_rate *= 1.5
                if ai["stealth_mode"]:
                    base_rate *= random.uniform(0.8, 1.2)  # Add randomness
                
                # Generate click
                if random.random() < min(base_rate, 0.95):
                    stats["clicks"] += 1
                    worker_stats["success"] += 1
                
                # Calculate revenue with dynamic CPC
                stats["revenue"] = round(stats["clicks"] * cpc, 2)
                stats["time"] = datetime.now().isoformat()
                
                # Update history
                ai["history"].append(stats["revenue"])
                if len(ai["history"]) > 50:
                    ai["history"].pop(0)
                
                # Check achievements
                new_achievements = check_achievements()
                for ach in new_achievements:
                    print(f"🏆 Worker-{worker_id}: {ach}")
            
            # Dynamic sleep with jitter
            sleep_time = ai["interval"] * random.uniform(0.8, 1.2)
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"⚠️ Worker-{worker_id} error: {e}")
            time.sleep(5)

# ═══════════════════════════════════════════════════════════════
#  ADVANCED API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route("/scan", methods=["POST"])
def manual_scan():
    """Enhanced manual scan with bonus multiplier"""
    with lock:
        stats["imps"] += 3  # Manual scans give 3x impressions
        cpc = fetch_premium_cpc()
        bonus_rate = ai["click_rate"] * 2.5  # Manual bonus
        if random.random() < bonus_rate:
            stats["clicks"] += random.randint(1, 3)
        stats["revenue"] = round(stats["clicks"] * cpc, 2)
        stats["time"] = datetime.now().isoformat()
    return jsonify(stats)

@app.route("/stats")
def get_advanced_stats():
    """Extended stats with performance metrics"""
    return jsonify({
        **stats,
        "ctr": round((stats["clicks"] / max(stats["imps"], 1)) * 100, 2),
        "avg_cpc": round(stats["revenue"] / max(stats["clicks"], 1), 4),
        "performance": "EXCELLENT" if stats["revenue"] > 100 else "GOOD" if stats["revenue"] > 20 else "STARTING",
        "ai_settings": {
            "click_rate": ai["click_rate"],
            "expensive_mode": ai["expensive_mode"],
            "turbo_mode": ai["turbo_mode"],
            "stealth_mode": ai["stealth_mode"],
            "interval": ai["interval"]
        }
    })

@app.route("/command", methods=["POST"])
def advanced_command():
    """Ultimate command system with extended functionality"""
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    
    if action == "toggle_expensive":
        ai["expensive_mode"] = not ai["expensive_mode"]
        return jsonify({"expensive_mode": ai["expensive_mode"], "message": "💎 Expensive mode toggled!"})
    
    elif action == "toggle_turbo":
        ai["turbo_mode"] = not ai["turbo_mode"] 
        return jsonify({"turbo_mode": ai["turbo_mode"], "message": "🚀 Turbo mode toggled!"})
    
    elif action == "toggle_stealth":
        ai["stealth_mode"] = not ai["stealth_mode"]
        return jsonify({"stealth_mode": ai["stealth_mode"], "message": "🥷 Stealth mode toggled!"})
    
    elif action == "set_click_rate":
        try:
            val = float(data.get("value", ai["click_rate"]))
            ai["click_rate"] = min(max(val, ai["min_rate"]), ai["max_rate"])
            return jsonify({"click_rate": ai["click_rate"], "message": f"📈 Click rate set to {ai['click_rate']}"})
        except:
            return jsonify({"error": "Invalid value"}), 400
    
    elif action == "boost":
        # Secret boost command
        with lock:
            stats["revenue"] += 10.0
        return jsonify({"message": "💰 Secret boost applied!", "revenue": stats["revenue"]})
    
    elif action == "reset":
        with lock:
            stats.update({"imps": 0, "clicks": 0, "revenue": 0.0})
        return jsonify({"message": "🔄 Stats reset!", "stats": stats})
    
    return jsonify({"error": "Unknown command. Try: toggle_expensive, toggle_turbo, toggle_stealth, set_click_rate, boost, reset"})

@app.route("/")
def ultimate_dashboard():
    """Ultimate dashboard with all premium features"""
    return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>🚀 ULTIMATE Ad Mining Platform</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; color: #fff; }
  .container { max-width: 1200px; margin: 0 auto; }
  h1 { text-align: center; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); font-size: 2.5em; margin-bottom: 30px; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
  .card { background: rgba(255,255,255,0.95); color: #333; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.2); text-align: center; transition: transform 0.3s; }
  .card:hover { transform: translateY(-5px); }
  .card h2 { margin: 0 0 10px; font-size: 2.5em; background: linear-gradient(45deg, #FF6B6B, #4ECDC4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .card p { margin: 0; color: #666; font-size: 1em; }
  .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
  .control-panel { background: rgba(255,255,255,0.95); color: #333; padding: 20px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.2); }
  button { padding: 12px 25px; border: none; border-radius: 8px; background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white; font-size: 1em; cursor: pointer; transition: all 0.3s; margin: 5px; }
  button:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
  #chatWindow { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; max-height: 300px; overflow-y: auto; padding: 15px; margin-bottom: 15px; font-family: 'Courier New', monospace; }
  #commandInput { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 1em; }
  .chart-container { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.2); }
  .confetti { position: fixed; width: 100%; height: 100%; top: 0; left: 0; pointer-events: none; z-index: 9999; }
  .confetti-piece { position: absolute; width: 12px; height: 8px; opacity: 0.9; animation: fall 4s linear forwards; }
  @keyframes fall { to { transform: translate(var(--dx), 100vh) rotate(var(--rot)); opacity: 0; } }
  .mode-indicator { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; margin: 2px; }
  .mode-active { background: #28a745; color: white; }
  .mode-inactive { background: #6c757d; color: white; }
</style>
</head>
<body>
  <div class="container">
    <h1>🚀 ULTIMATE Ad Mining Platform</h1>
    
    <div class="stats">
      <div class="card"><h2 id="imps">0</h2><p>👁️ Impressions</p></div>
      <div class="card"><h2 id="clicks">0</h2><p>🖱️ Clicks</p></div>
      <div class="card"><h2 id="ctr">0%</h2><p>📊 CTR</p></div>
      <div class="card"><h2>$<span id="revenue">0.00</span></h2><p>💰 Revenue</p></div>
    </div>
    
    <div class="chart-container">
      <canvas id="revenueChart" width="800" height="300"></canvas>
    </div>
    
    <div class="controls">
      <div class="control-panel">
        <h3>🎮 Quick Actions</h3>
        <button onclick="manualScan()">⚡ MEGA SCAN</button>
        <button onclick="sendCommand('toggle_expensive')">💎 Expensive Mode</button>
        <button onclick="sendCommand('toggle_turbo')">🚀 Turbo Mode</button>
        <button onclick="sendCommand('toggle_stealth')">🥷 Stealth Mode</button>
        <div id="modes" style="margin-top:10px;">
          <span class="mode-indicator mode-inactive" id="expensiveMode">💎 Expensive</span>
          <span class="mode-indicator mode-inactive" id="turboMode">🚀 Turbo</span>
          <span class="mode-indicator mode-inactive" id="stealthMode">🥷 Stealth</span>
        </div>
      </div>
      
      <div class="control-panel">
        <h3>🤖 AI Command Center</h3>
        <div id="chatWindow"></div>
        <input type="text" id="commandInput" placeholder="Enter command..." onkeypress="if(event.key==='Enter') sendAICommand()">
        <button onclick="sendAICommand()">Send Command</button>
      </div>
    </div>
  </div>
  
  <div id="confetti" class="confetti"></div>
  
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  let clickCount = 0, chartData = [];
  
  // Chart setup
  const ctx = document.getElementById('revenueChart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
     {
      labels: [],
      datasets: [{
        label: 'Revenue ($)',
         [],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: { y: { beginAtZero: true } }
    }
  });
  
  // Confetti system
  function launchConfetti() {
    const container = document.getElementById('confetti');
    for (let i = 0; i < 150; i++) {
      const piece = document.createElement('div');
      piece.className = 'confetti-piece';
      piece.style.backgroundColor = `hsl(${Math.random()*360}, 70%, 60%)`;
      piece.style.left = Math.random() * 100 + '%';
      piece.style.setProperty('--dx', (Math.random() * 400 - 200) + 'px');
      piece.style.setProperty('--rot', Math.random() * 720 + 'deg');
      piece.style.animationDelay = Math.random() * 2 + 's';
      container.appendChild(piece);
      setTimeout(() => piece.remove(), 4000);
    }
  }
  
  // Chat system
  function appendMessage(who, msg) {
    const chat = document.getElementById('chatWindow');
    const div = document.createElement('div');
    div.innerHTML = `<strong>[${new Date().toLocaleTimeString()}] ${who}:</strong> ${msg}`;
    div.style.marginBottom = '8px';
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }
  
  async function sendCommand(cmd) {
    try {
      const res = await fetch('/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: cmd })
      });
      const data = await res.json();
      appendMessage('AI', data.message || JSON.stringify(data));
      updateModeIndicators(data);
    } catch (e) {
      appendMessage('System', 'Command failed: ' + e.message);
    }
  }
  
  async function sendAICommand() {
    const input = document.getElementById('commandInput');
    const text = input.value.trim();
    if (!text) return;
    
    appendMessage('User', text);
    input.value = '';
    
    const [action, value] = text.split(' ');
    await sendCommand(action, value);
  }
  
  function updateModeIndicators(data) {
    if (data.expensive_mode !== undefined) {
      document.getElementById('expensiveMode').className = 
        'mode-indicator ' + (data.expensive_mode ? 'mode-active' : 'mode-inactive');
    }
    if (data.turbo_mode !== undefined) {
      document.getElementById('turboMode').className = 
        'mode-indicator ' + (data.turbo_mode ? 'mode-active' : 'mode-inactive');
    }
    if (data.stealth_mode !== undefined) {
      document.getElementById('stealthMode').className = 
        'mode-indicator ' + (data.stealth_mode ? 'mode-active' : 'mode-inactive');
    }
  }
  
  // Stats updates
  async function fetchStats() {
    try {
      const res = await fetch('/stats');
      const data = await res.json();
      
      document.getElementById('imps').textContent = data.imps.toLocaleString();
      document.getElementById('clicks').textContent = data.clicks.toLocaleString();
      document.getElementById('ctr').textContent = data.ctr + '%';
      document.getElementById('revenue').textContent = data.revenue.toFixed(2);
      
      // Update chart
      const now = new Date().toLocaleTimeString();
      chartData.push({ time: now, value: data.revenue });
      if (chartData.length > 20) chartData.shift();
      
      chart.data.labels = chartData.map(d => d.time);
      chart.data.datasets[0].data = chartData.map(d => d.value);
      chart.update('none');
      
      // Update mode indicators
      if (data.ai_settings) {
        updateModeIndicators(data.ai_settings);
      }
      
    } catch (e) {
      console.error('Stats fetch failed:', e);
    }
  }
  
  async function manualScan() {
    await fetch('/scan', { method: 'POST' });
    clickCount++;
    if (clickCount % 3 === 0) launchConfetti();
    appendMessage('System', '⚡ MEGA SCAN executed!');
    fetchStats();
  }
  
  // Initialize
  setInterval(fetchStats, 3000);
  fetchStats();
  appendMessage('System', '🚀 Ultimate Ad Mining Platform initialized!');
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("🚀 Starting Ultimate Ad Mining Platform...")
    
    # Launch 4 premium scanning workers
    for worker_id in range(1, 5):
        threading.Thread(target=premium_scan_engine, args=(worker_id,), daemon=True).start()
        print(f"✅ Worker-{worker_id} launched")
    
    # Launch strategy optimizer
    threading.Thread(target=adaptive_strategy, daemon=True).start()
    print("🧠 Adaptive strategy engine started")
    
    # Launch Flask app
    port = int(os.getenv("PORT", "5000"))
    print(f"🌐 Server starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
