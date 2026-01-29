from flask import Flask, request
import os
import requests

BOT_TOKEN = "8531922367:AAHMg7uVl6t1BJaq2102tYnAEm6RZ9L12qs"
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"

r = requests.get(url)
print(r.json())


# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Токен бота Telegram
ADMIN_ID = int(os.environ.get("ADMIN_ID", 1191654019))  # ID админа
RAILWAY_URL = os.environ.get("RAILWAY_URL")  # Например, https://my-bot.up.railway.app

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
waiting_for_text = set()

# ===== ФУНКЦИИ =====
def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def main_menu():
    return {
        "keyboard": [
            ["📝 Нове звернення"],
            ["ℹ️ Про бота"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def cancel_menu():
    return {
        "keyboard": [
            ["❌ Відміна"]
        ],
        "resize_keyboard": True
    }

# ===== ПРОВЕРКА, ЖИВОЙ ЛИ СЕРВЕР =====
@app.route("/")
def hello():
    return "Bot is alive 🚀"

# ===== WEBHOOK =====
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(force=True)

    if "message" not in update:
        return "ok"

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text")
    if not text:
        return "ok"

    # Главное меню
    if text in ["/start", "start"]:
        send_message(chat_id, "👋 Вітаю!\nЦе анонімний бот шкільного омбудсмена.\nОберіть дію з меню 👇", main_menu())
        return "ok"

    if text == "ℹ️ Про бота":
        send_message(chat_id, "ℹ️ Про бота\n\nТут можна анонімно повідомити про проблему у школі.", main_menu())
        return "ok"

    if text == "📝 Нове звернення":
        waiting_for_text.add(chat_id)
        send_message(chat_id, "✍️ Опишіть ситуацію одним повідомленням.\n\nНатисніть ❌ Відміна, щоб скасувати.", cancel_menu())
        return "ok"

    if text == "❌ Відміна":
        waiting_for_text.discard(chat_id)
        send_message(chat_id, "❌ Скасовано.\n\nОберіть дію з меню 👇", main_menu())
        return "ok"

    # Получаем сообщение и пересылаем администратору
    if chat_id in waiting_for_text:
        send_message(ADMIN_ID, f"📩 Нове анонімне звернення:\n\n{text}")
        send_message(chat_id, "✅ Ваше звернення передано омбудсмену.", main_menu())
        waiting_for_text.discard(chat_id)
        return "ok"

    send_message(chat_id, "ℹ️ Скористайтесь кнопками меню 👇", main_menu())
    return "ok"

# ===== УСТАНОВКА WEBHOOK =====
def set_webhook():
    if not RAILWAY_URL:
        print("RAILWAY_URL не задан! Webhook не установлен.")
        return
    url = f"{RAILWAY_URL}/{BOT_TOKEN}"
    r = requests.get(f"{BASE_URL}/setWebhook", params={"url": url})
    print("Webhook set:", r.text)

# ===== ЗАПУСК СЕРВЕРА =====
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
