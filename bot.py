import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

turni = [
    ("07:00", "13:00", "Mattutino"),
    ("13:00", "19:00", "Pomeridiano"),
    ("19:00", "01:00", "Serale"),
    ("01:00", "07:00", "Notturno")
]

mezzi = [
    ["Zara10", "Zara20", "Beta10"],
    ["Volante 1", "Volante 2", "Volante 3"],
    ["Volante 4", "Volante 5", "Volante 6"],
    ["Volante 7", "Pattuglia SMN", "ALTRO"]
]

ruoli = [["Capo Pattuglia", "Autista"]]

user_data = {}

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
    await update.message.reply_text("Benvenuto 👮‍♂️\nScrivi /inizio per iniziare il turno.")


async def inizio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = mezzi
    await update.message.reply_text(
        f"Turno attivo: {get_turno()}\nSeleziona il mezzo:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )


async def handle_mezzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {"mezzo": update.message.text}

    await update.message.reply_text(
        "Sei Capo Pattuglia o Autista?",
        reply_markup=ReplyKeyboardMarkup(ruoli, one_time_keyboard=True, resize_keyboard=True)
    )


async def handle_ruolo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data:
        user_data[user_id]["ruolo"] = update.message.text

    await update.message.reply_text(
        "Ora condividi la tua posizione in tempo reale dal gruppo (Telegram)."
    )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("inizio", inizio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mezzo))

app.run_polling()
