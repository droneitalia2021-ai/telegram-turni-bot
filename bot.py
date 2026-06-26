import os
import psycopg2
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

MEZZO, RUOLO = range(2)


# ---------------- DATABASE ----------------

def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # posizioni live
    cur.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # turni
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            mezzo TEXT,
            ruolo TEXT,
            start_time TIMESTAMP DEFAULT NOW(),
            active BOOLEAN DEFAULT TRUE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ---------------- DATI ----------------

mezzi = [
    ["Zara10", "Zara20", "Beta10"],
    ["Volante 1", "Volante 2", "Volante 3"],
    ["Volante 4", "Volante 5", "Volante 6"],
    ["Volante 7", "Pattuglia SMN", "ALTRO"]
]

ruoli = [["Capo Pattuglia", "Autista"]]


# ---------------- TURNO ORARIO ----------------

def get_turno():
    h = datetime.now().hour

    if 7 <= h < 13:
        return "Mattutino"
    elif 13 <= h < 19:
        return "Pomeridiano"
    elif 19 <= h or h < 1:
        return "Serale"
    else:
        return "Notturno"


# ---------------- COMANDI ----------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 Inizia turno", callback_data="start")],
        [InlineKeyboardButton("🔴 Fine turno", callback_data="stop")]
    ]

    await update.message.reply_text(
        "📋 Menu operativo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# INIZIO TURNO
async def inizio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Turno attivo: {get_turno()}\nSeleziona il mezzo:",
        reply_markup=ReplyKeyboardMarkup(mezzi, resize_keyboard=True, one_time_keyboard=True),
    )
    return MEZZO


async def scelta_mezzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mezzo"] = update.message.text

    await update.message.reply_text(
        "Sei Capo Pattuglia o Autista?",
        reply_markup=ReplyKeyboardMarkup(ruoli, resize_keyboard=True, one_time_keyboard=True),
    )
    return RUOLO


async def scelta_ruolo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ruolo"] = update.message.text

    await update.message.reply_text(
        "📍 Ora attiva la posizione in tempo reale nel gruppo (6 ore)."
    )
    return ConversationHandler.END


# FINE TURNO
async def fine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE shifts
        SET active = FALSE
        WHERE user_id = %s AND active = TRUE
    """, (user.id,))

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text("🔴 Turno chiuso. Buon rientro 👍")


# ---------------- GPS ----------------

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    loc = update.message.location

    mezzo = context.user_data.get("mezzo", "Sconosciuto")
    ruolo = context.user_data.get("ruolo", "Sconosciuto")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO positions (user_id, lat, lon)
        VALUES (%s, %s, %s)
    """, (user.id, loc.latitude, loc.longitude))

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(
        f"📍 Posizione ricevuta\n"
        f"👤 Agente: {user.first_name}\n"
        f"🚓 Mezzo: {mezzo}\n"
        f"👮 Ruolo: {ruolo}\n\n"
        f"Buon lavoro 👍"
    )


# ---------------- APP ----------------

app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("inizio", inizio)],
    states={
        MEZZO: [MessageHandler(filters.TEXT & ~filters.COMMAND, scelta_mezzo)],
        RUOLO: [MessageHandler(filters.TEXT & ~filters.COMMAND, scelta_ruolo)],
    },
    fallbacks=[],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("fine", fine))
app.add_handler(conv_handler)
app.add_handler(MessageHandler(filters.LOCATION, location_handler))

init_db()

app.run_polling()
