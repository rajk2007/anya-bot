import os
import logging
import requests
from flask import Flask, request
import google.generativeai as genai

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
model = genai.GenerativeModel("gemini-1.5-flash")

# Chat history store
chat_histories = {}

# Flask app
flask_app = Flask(__name__)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_typing(chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    requests.post(url, json={"chat_id": chat_id, "action": "typing"})

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    r = requests.post(url, json={"url": webhook})
    logger.info(f"Webhook set: {r.json()}")

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" not in data:
        return "OK"

    message = data["message"]
    chat_id = message["chat"]["id"]

    if "text" not in message:
        return "OK"

    text = message["text"]
    user_id = message["from"]["id"]

    # Commands
    if text == "/start":
        send_message(chat_id, "Hi! I'm Anya 🌸 Your personal AI assistant!\nJust talk to me and I'll respond.\n\nCommands:\n/start - Start\n/help - Help\n/clear - Clear chat history")
        return "OK"

    if text == "/help":
        send_message(chat_id, "Just send me any message and I'll reply using AI! 🤖\n/clear to reset our conversation.")
        return "OK"

    if text == "/clear":
        chat_histories[user_id] = []
        send_message(chat_id, "Chat history cleared! Let's start fresh 🌸")
        return "OK"

    # AI response
    send_typing(chat_id)

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    try:
        chat = model.start_chat(history=chat_histories[user_id])
        response = chat.send_message(text)
        reply = response.text

        chat_histories[user_id].append({"role": "user", "parts": [text]})
        chat_histories[user_id].append({"role": "model", "parts": [reply]})

        if len(chat_histories[user_id]) > 20:
            chat_histories[user_id] = chat_histories[user_id][-20:]

        send_message(chat_id, reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        send_message(chat_id, "Oops! Something went wrong. Try again 🌸")

    return "OK"

@flask_app.route("/")
def index():
    return "Anya Bot is running! 🌸"

if __name__ == "__main__":
    set_webhook()
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
