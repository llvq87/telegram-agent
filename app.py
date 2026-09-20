"""
Telegram bot - webhook version, running on Render's free tier.
Step 2: replies using Claude instead of echoing.
Keeps a short in-memory conversation history per chat (resets if the
service restarts - persistent memory comes in a later step).
"""
import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "أنت مساعد شخصي ذكي يتكلم عربي بشكل طبيعي ومباشر. "
    "تساعد المستخدم يرتب مهامه ويتذكر أشياء، وترد بإيجاز ووضوح. "
    "لو طلب منك شي لسا ما تقدر تسويه (مثل إرسال إيميل أو تذكير مجدول)، "
    "قول له بصراحة إنها ميزة قادمة."
)

# chat_id -> list of {"role": "user"/"assistant", "content": str}
conversations = {}
MAX_HISTORY = 10  # keep the last N messages per chat to control cost


def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


def ask_claude(chat_id, user_text):
    history = conversations.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})
    history[:] = history[-MAX_HISTORY:]

    resp = requests.post(
        ANTHROPIC_API,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": history,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    reply = data["content"][0]["text"]
    history.append({"role": "assistant", "content": reply})
    history[:] = history[-MAX_HISTORY:]
    return reply


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
            conversations.pop(chat_id, None)
            send_message(chat_id, "أهلاً! أنا مساعدك الشخصي، اسألني أو اطلب مني أي شي.")
        else:
            try:
                reply = ask_claude(chat_id, text)
            except Exception as e:
                reply = f"صار خطأ وأنا أحاول أرد عليك: {e}"
            send_message(chat_id, reply)
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
