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

# ===== ОПРОС =====
QUESTIONS = [
    {
        "key": "who",
        "text": "Хто заповнює форму?\n"
                "1️⃣ Учень / Учениця\n"
                "2️⃣ Батько / Мати\n"
                "3️⃣ Свідок (інша особа)"
    },
    {
        "key": "class",
        "text": "У якому класі ви навчаєтесь / навчається дитина?\n"
                "✏️ Напишіть, наприклад: 7-Б"
    },
    {
        "key": "place",
        "text": "Де це відбулося?\n"
                "1️⃣ У класі на перерві\n"
                "2️⃣ У коридорі\n"
                "3️⃣ До / після уроків\n"
                "4️⃣ В соцмережі\n"
                "5️⃣ Інше"
    },
    {
        "key": "reported",
        "text": "Чи звертались ви вже з цією проблемою?\n"
                "1️⃣ Так, до вчителя / класного керівника\n"
                "2️⃣ Так, до батьків\n"
                "3️⃣ Ні, це перше звернення"
    },
    {
        "key": "help",
        "text": "Якої допомоги ви очікуєте від адміністрації?\n"
                "1️⃣ Розмова з учасниками конфлікту\n"
                "2️⃣ Консультація психолога (конфіденційно)\n"
                "3️⃣ Залучення батьків інших сторін\n"
                "4️⃣ Просто повідомити, щоб ситуація була на контролі"
    }
]

user_state = {}     # chat_id -> номер вопроса
user_answers = {}   # chat_id -> ответы



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
        user_state[chat_id] = 0
        user_answers[chat_id] = {}
        send_message(chat_id, QUESTIONS[0]["text"], cancel_menu())
        return "ok"

# ===== ОБРАБОТКА ОПРОСА =====
    if chat_id in user_state:
        step = user_state[chat_id]

        user_answers[chat_id][QUESTIONS[step]["key"]] = text
        step += 1
        user_state[chat_id] = step

        if step >= len(QUESTIONS):
            del user_state[chat_id]
            waiting_for_text.add(chat_id)

            send_message(
                chat_id,
                "✍️ Опишіть ситуацію одним повідомленням.\n\n"
                "Натисніть ❌ Відміна, щоб скасувати.",
                cancel_menu()
            )
        else:
            send_message(chat_id, QUESTIONS[step]["text"], cancel_menu())

        return "ok"

    if text == "❌ Відміна":
        waiting_for_text.discard(chat_id)
        send_message(chat_id, "❌ Скасовано.\n\nОберіть дію з меню 👇", main_menu())
        return "ok"

    # Получаем сообщение и пересылаем администратору
    if chat_id in waiting_for_text:
        answers = user_answers.get(chat_id, {})

    message_to_admin = (
        "📩 *Новое анонимное обращение*\n\n"
        f"👤 Кто заполняет форму: {answers.get('who', 'не указано')}\n"
        f"🏫 Класс: {answers.get('class', 'не указано')}\n"
        f"📍 Где произошло: {answers.get('place', 'не указано')}\n"
        f"📣 Обращались ранее: {answers.get('reported', 'не указано')}\n"
        f"🆘 Ожидаемая помощь: {answers.get('help', 'не указано')}\n\n"
        "📝 *Описание ситуации:*\n"
        f"{text}"
    )

    send_message(ADMIN_ID, message_to_admin)

    send_message(
        chat_id,
        "✅ Ваше обращение успешно отправлено омбудсмену.\n\n"
        "Спасибо, что сообщили о проблеме 🙏",
        main_menu()
    )

    waiting_for_text.discard(chat_id)
    user_answers.pop(chat_id, None)

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
