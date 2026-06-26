import os
import psycopg2
from flask import Flask, jsonify, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)


# ---------------- DB ----------------

def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


# ---------------- BOT ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot attivo. Invia posizione nel gruppo.")


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    user_id = update.message.from_user.id

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO positions (user_id, lat, lon) VALUES (%s, %s, %s)",
        (user_id, loc.latitude, loc.longitude),
    )
    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text("📍 Posizione salvata")


# ---------------- MAPPA ----------------

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

async function loadMarkers(){
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
    cur.execute("SELECT lat, lon FROM positions ORDER BY id DESC LIMIT 50")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([{"lat": r[0], "lon": r[1]} for r in rows])


# ---------------- START ----------------

def run_bot():
    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.LOCATION, location_handler))

    app_bot.run_polling()


if __name__ == "__main__":
    init_db()

    import threading
    threading.Thread(target=run_bot).start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
