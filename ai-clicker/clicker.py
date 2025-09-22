import os
import time
import random
from threading import Thread
from flask import Flask, jsonify, request

# Tworzymy aplikację Flask bez obsługi statycznych plików
app = Flask(__name__, static_folder=None)

# Statystyki oraz ustawienia AI
stats = {
    "imps": 0,
    "clicks": 0,
    "revenue": 0.0
}
ai_settings = {
    "click_rate": float(os.getenv("CLICK_RATE", "0.20")),
    "expensive_mode": False,
    "min_click_rate": 0.05,
    "max_click_rate": 0.50
}

def optimize_click_rate():
    """
    Co 30 sekund sprawdza, czy przychody wzrosły.
    Jeśli tak, zwiększa click_rate, w przeciwnym razie zmniejsza,
    aby uniknąć potencjalnego zablokowania.
    """
    previous_revenue = 0.0
    while True:
        time.sleep(30)
        current_revenue = stats["revenue"]
        if current_revenue > previous_revenue:
            ai_settings["click_rate"] = min(
                ai_settings["click_rate"] + 0.03,
                ai_settings["max_click_rate"]
            )
        else:
            ai_settings["click_rate"] = max(
                ai_settings["click_rate"] - 0.02,
                ai_settings["min_click_rate"]
            )
        previous_revenue = current_revenue

def auto_scan_loop():
    """
    Co 5 sekund generuje nową odsłonę i ewentualne kliknięcie
    według aktualnego click_rate i trybu expensive_mode.
    """
    while True:
        stats["imps"] += 1
        rate = ai_settings["click_rate"] * (2 if ai_settings["expensive_mode"] else 1)
        if random.random() < rate:
            stats["clicks"] += 1
        stats["revenue"] = round(
            stats["clicks"] * float(os.getenv("CPC", "0.05")), 2
        )
        time.sleep(5)

@app.route("/")
def dashboard():
    """
    Zwraca kompletny kod HTML dashboardu,
    zawierający statystyki, przycisk manualnego skanowania,
    panel sterowania AI oraz efekt konfetti.
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Ad Mining Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f0f2f5; margin:0; padding:20px;
           display:flex; flex-direction:column; align-items:center; }
    h1 { color:#333; margin-bottom:20px; }
    .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
             gap:20px; width:100%; max-width:800px; margin-bottom:30px; }
    .card { background:#fff; padding:20px; border-radius:8px;
             box-shadow:0 2px 8px rgba(0,0,0,0.1); text-align:center; }
    .card h2 { margin:0 0 10px; font-size:2.2em; color:#007bff; }
    .card p { margin:0; color:#555; font-size:0.9em; }
    button { padding:12px 24px; border:none; border-radius:6px; background:#28a745;
             color:#fff; font-size:1em; cursor:pointer; box-shadow:0 2px 5px rgba(0,0,0,0.1);
             transition:background 0.2s; margin-top:10px; }
    button:hover { background:#218838; }
    #msg { margin-top:15px; color:#28a745; font-weight:bold; }
    #commandResponse { margin-top:10px; white-space:pre-wrap; font-family:monospace; }
    #commandInput { width:100%; max-width:800px; height:60px; margin-top:15px;
                    padding:5px; font-size:1em; }
    .control-panel { max-width:800px; width:100%; background:#fff; border-radius:8px;
                     padding:15px; box-shadow:0 2px 8px rgba(0,0,0,0.1);
                     margin-bottom:20px; }
    .confetti { position:fixed; width:100%; height:100%; top:0; left:0;
                pointer-events:none; overflow:hidden; z-index:9999; }
    .confetti-piece { position:absolute; width:10px; height:6px; background-color:red;
                      opacity:0.8; transform-origin:center; animation:fall 3s linear forwards; }
    @keyframes fall {
      to { transform:translate(var(--dx),100vh) rotate(var(--rot)); opacity:0; }
    }
  </style>
</head>
<body>
  <h1>Ad Mining Platform</h1>
  <div class="stats">
    <div class="card"><h2 id="imps">0</h2><p>Impressions</p></div>
    <div class="card"><h2 id="clicks">0</h2><p>Clicks</p></div>
    <div class="card"><h2 id="ctr">0%</h2><p>CTR</p></div>
    <div class="card"><h2>$<span id="revenue">0.00</span></h2><p>Revenue</p></div>
  </div>
  <button onclick="manualScan()">Magnes na reklamy</button>
  <div class="control-panel">
    <h3>Sterowanie AI Face App</h3>
    <textarea id="commandInput" placeholder="Napisz komendę, np. toggle_expensive lub set_click_rate 0.5"></textarea><br>
    <button onclick="sendCommand()">Wyślij do AI</button>
    <pre id="commandResponse"></pre>
  </div>
  <div id="msg"></div>
  <div id="confetti" class="confetti"></div>
  <script>
    let clickCount = 0;
    function launchConfetti() {
      const container = document.getElementById("confetti");
      for (let i = 0; i < 100; i++) {
        const piece = document.createElement("div");
        piece.classList.add("confetti-piece");
        piece.style.backgroundColor = `hsl(${Math.random()*360},70%,60%)`;
        piece.style.left = `${Math.random()*100}%`;
        piece.style.setProperty("--dx", (Math.random()*200-100) + "px");
        piece.style.setProperty("--rot", (Math.random()*360) + "deg");
        piece.style.animationDelay = (Math.random()*2) + "s";
        container.appendChild(piece);
        setTimeout(() => piece.remove(), 3000);
      }
    }
    async function manualScan() {
      await fetch("/scan", { method: "POST" });
      clickCount++;
      if (clickCount % 3 === 0) launchConfetti();
      document.getElementById("msg").innerText = "Magnes uruchomiony!";
      setTimeout(() => { document.getElementById("msg").innerText = ""; }, 3000);
      fetchStats();
    }
    async function fetchStats() {
      try {
        const res = await fetch("/stats");
        const data = await res.json();
        document.getElementById("imps").innerText = data.imps;
        document.getElementById("clicks").innerText = data.clicks;
        document.getElementById("ctr").innerText = ((data.clicks/data.imps||0)*100).toFixed(2) + "%";
        document.getElementById("revenue").innerText = data.revenue.toFixed(2);
      } catch (e) {
        console.error("Failed to fetch stats:", e);
      }
    }
    async function sendCommand() {
      const input = document.getElementById("commandInput").value.trim();
      if (!input) return alert("Wpisz komendę");
      const parts = input.split(" ");
      const action = parts[0], value = parts[1];
      const body = { action };
      if (value) body.value = value;
      const res = await fetch("/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      document.getElementById("commandResponse").innerText = JSON.stringify(data, null, 2);
    }
    setInterval(fetchStats, 5000);
    fetchStats();
  </script>
</body>
</html>
"""

@app.route("/scan", methods=["GET", "POST"])
def scan():
    stats["imps"] += 1
    rate = ai_settings["click_rate"] * (2 if ai_settings["expensive_mode"] else 1)
    if random.random() < rate:
        stats["clicks"] += 1
    stats["revenue"] = round(
        stats["clicks"] * float(os.getenv("CPC", "0.05")), 2
    )
    return jsonify(stats)

@app.route("/stats")
def get_stats():
    return jsonify(stats)

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json() or {}
    action = data.get("action", "")
    if action == "toggle_expensive":
        ai_settings["expensive_mode"] = not ai_settings["expensive_mode"]
        return jsonify({"expensive_mode": ai_settings["expensive_mode"]})
    if action == "set_click_rate":
        try:
            val = float(data.get("value", ai_settings["click_rate"]))
            ai_settings["click_rate"] = min(max(val, ai_settings["min_click_rate"]), ai_settings["max_click_rate"])
            return jsonify({"click_rate": ai_settings["click_rate"]})
        except ValueError:
            return jsonify({"error":"Invalid value"}), 400
    return jsonify({"error":"Unknown action"}), 400

if __name__ == "__main__":
    Thread(target=auto_scan_loop, daemon=True).start()
    Thread(target=optimize_click_rate, daemon=True).start()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
