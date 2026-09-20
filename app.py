"""
Telegram bot - webhook version, made to run on Render's free tier.
Step 1: just confirms the connection by echoing messages back.
Next steps will add AI replies, task tracking, and reminders.
"""
import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


@app.route("/", methods=["GET"])
def health():
    # Render pings this so the free service knows it's alive.
    return "Bot is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    message = update.get("message")
    if message and "text" in message:
        chat_id = message["chat"]["id"]
        text = message["text"]
        if text == "/start":
            send_message(chat_id, "أهلاً! أنا شغال. أرسل لي أي رسالة وبردها عليك.")
        else:
            send_message(chat_id, f"استلمت رسالتك: {text}")
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
