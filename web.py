import os
import psycopg2
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mappa Pattuglie</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
</head>
<body>
<h3>Mappa Live Pattuglie</h3>
<div id="map" style="height: 90vh;"></div>

<script>
var map = L.map('map').setView([43.8, 11.1], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

async function loadMarkers() {
    const res = await fetch('/data');
    const data = await res.json();

    data.forEach(p => {
        L.marker([p.lat, p.lon]).addTo(map);
    });
}

loadMarkers();
setInterval(loadMarkers, 5000);
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/data")
def data():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT lat, lon FROM positions ORDER BY updated_at DESC LIMIT 50")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify([{"lat": r[0], "lon": r[1]} for r in rows])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
