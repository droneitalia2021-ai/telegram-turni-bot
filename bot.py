import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

MEZZO, RUOLO = range(2)

user_data = {}

mezzi = [
    ["Zara10", "Zara20", "Beta10"],
    ["Volante 1", "Volante 2", "Volante 3"],
    ["Volante 4", "Volante 5", "Volante 6"],
    ["Volante 7", "Pattuglia SMN", "ALTRO"]
]

ruoli = [["Capo Pattuglia", "Autista"]]


def get_turno():
    from datetime import datetime
    h = datetime.now().hour

    if 7 <= h < 13:
        return "Mattutino"
    elif 13 <= h < 19:
        return "Pomeridiano"
    elif 19 <= h or h < 1:
        return "Serale"
    else:
        return "Notturno"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👮 Bot attivo. Usa /inizio per iniziare il turno.")


async def inizio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Turno: {get_turno()}\nSeleziona il mezzo:",
        reply_markup=ReplyKeyboardMarkup(mezzi, resize_keyboard=True, one_time_keyboard=True),
    )
    return MEZZO


async def scelta_mezzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {"mezzo": update.message.text}

    await update.message.reply_text(
        "Sei Capo Pattuglia o Autista?",
        reply_markup=ReplyKeyboardMarkup(ruoli, resize_keyboard=True, one_time_keyboard=True),
    )
    return RUOLO


async def scelta_ruolo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id]["ruolo"] = update.message.text

    await update.message.reply_text(
        "📍 Ora condividi la posizione in tempo reale nel gruppo."
    )
    return ConversationHandler.END


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
app.add_handler(conv_handler)

app.run_polling()
from telegram.ext import MessageHandler, filters

positions = {}  # {user_id: (lat, lon)}

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    loc = update.message.location

    positions[user_id] = (loc.latitude, loc.longitude)

    await update.message.reply_text("📍 Posizione aggiornata in tempo reale")

app.add_handler(MessageHandler(filters.LOCATION, location_handler))
