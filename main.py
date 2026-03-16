import os
import logging
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import asyncio

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Chat history store
chat_histories = {}

# Flask app
flask_app = Flask(__name__)

# Telegram app
ptb_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm Anya 🌸 Your personal AI assistant!\nJust talk to me and I'll respond.\n\nCommands:\n/start - Start\n/help - Help\n/clear - Clear chat history"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just send me any message and I'll reply using AI! 🤖\n/clear to reset our conversation."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_histories[user_id] = []
    await update.message.reply_text("Chat history cleared! Let's start fresh 🌸")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    await context.bot.send_chat_action(
        chat_id=update.message.chat_id,
        action=telegram.constants.ChatAction.TYPING
    )

    try:
        chat = model.start_chat(history=chat_histories[user_id])
        response = chat.send_message(user_message)
        reply = response.text

        chat_histories[user_id].append({"role": "user", "parts": [user_message]})
        chat_histories[user_id].append({"role": "model", "parts": [reply]})

        # Keep history to last 20 messages
        if len(chat_histories[user_id]) > 20:
            chat_histories[user_id] = chat_histories[user_id][-20:]

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Oops! Something went wrong. Try again 🌸")

# Register handlers
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("help", help_cmd))
ptb_app.add_handler(CommandHandler("clear", clear))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK"

@flask_app.route("/")
def index():
    return "Anya Bot is running! 🌸"

async def setup():
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    asyncio.run(setup())
    flask_app.run(host="0.0.0.0", port=PORT)
