from flask import Flask, request
import os
import requests

# BOT_TOKEN = "8531922367:AAHMg7uVl6t1BJaq2102tYnAEm6RZ9L12qs"
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
        "text": "Хто заповнює форму?",
        "options": [
            "👤 Учень / Учениця",
            "👨‍👩‍👧 Батько / Мати",
            "👀 Свідок (інша особа)"
        ]
    },
    {
        "key": "class",
        "text": "У якому класі ви навчаєтесь / навчається дитина?",
        "options": None  # тут ввод вручную
    },
    {
        "key": "place",
        "text": "Де це відбулося?",
        "options": [
            "🏫 У класі на перерві",
            "🚪 У коридорі",
            "⏰ До / після уроків",
            "🌐 В соцмережі",
            "❓ Інше"
        ]
    },
    {
        "key": "reported",
        "text": "Чи звертались ви вже з цією проблемою?",
        "options": [
            "✅ Так, до вчителя / класного керівника",
            "👨‍👩‍👧 Так, до батьків",
            "❌ Ні, це перше звернення"
        ]
    },
    {
        "key": "help",
        "text": "Якої допомоги ви очікуєте від адміністрації?",
        "options": [
            "🗣 Розмова з учасниками конфлікту",
            "🧠 Консультація психолога",
            "👨‍👩‍👧 Залучення батьків",
            "ℹ️ Просто повідомити"
        ]
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

def options_menu(options):
    return {
        "keyboard": [[opt] for opt in options],
        "resize_keyboard": True,
        "one_time_keyboard": True
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

    # ===== СТАРТ =====
    if text in ["/start", "start"]:
        send_message(
            chat_id,
            "👋 Вітаю!\n"
            "Це анонімний бот шкільного омбудсмена.\n"
            "Оберіть дію з меню 👇",
            main_menu()
        )
        return "ok"

    # ===== ПРО БОТА =====
    if text == "ℹ️ Про бота":
        send_message(
            chat_id,
            "ℹ️ *Про бота*\n\n"
            "Тут ви можете *анонімно* повідомити про проблему у школі.\n"
            "Ваше звернення отримає омбудсмен.",
            main_menu()
        )
        return "ok"

    # ===== НОВЕ ЗВЕРНЕННЯ =====
    if text == "📝 Нове звернення":
        user_state[chat_id] = 0
        user_answers[chat_id] = {}

        q = QUESTIONS[0]
        send_message(chat_id, q["text"], options_menu(q["options"]))
        return "ok"

    # ===== ВІДМІНА =====
    if text == "❌ Відміна":
        user_state.pop(chat_id, None)
        waiting_for_text.discard(chat_id)

        send_message(
            chat_id,
            "❌ Звернення скасовано.\n\n"
            "Оберіть дію з меню 👇",
            main_menu()
        )
        return "ok"

    # ===== ОПИТУВАННЯ (КНОПКИ) =====
    if chat_id in user_state:
        step = user_state[chat_id]
        q = QUESTIONS[step]

        # дозволяємо тільки натискання кнопок
        if q["options"] and text not in q["options"]:
            send_message(chat_id, "❗ Будь ласка, оберіть відповідь кнопкою 👇")
            return "ok"

        user_answers[chat_id][q["key"]] = text
        step += 1

        if step >= len(QUESTIONS):
            user_state.pop(chat_id)
            waiting_for_text.add(chat_id)

            send_message(
                chat_id,
                "✍️ Опишіть ситуацію *одним повідомленням*.\n\n"
                "Натисніть ❌ Відміна, щоб скасувати.",
                cancel_menu()
            )
        else:
            user_state[chat_id] = step
            next_q = QUESTIONS[step]

            keyboard = (
                options_menu(next_q["options"])
                if next_q["options"]
                else cancel_menu()
            )

            send_message(chat_id, next_q["text"], keyboard)

        return "ok"

    # ===== ОПИС СИТУАЦІЇ → АДМІНУ =====
    if chat_id in waiting_for_text:
        answers = user_answers.get(chat_id, {})

        message_to_admin = (
            "📩 *Нове анонімне звернення*\n\n"
            f"👤 Хто заповнює форму: {answers.get('who', '—')}\n"
            f"🏫 Клас: {answers.get('class', '—')}\n"
            f"📍 Де сталося: {answers.get('place', '—')}\n"
            f"📣 Чи звертались раніше: {answers.get('reported', '—')}\n"
            f"🆘 Очікувана допомога: {answers.get('help', '—')}\n\n"
            "📝 *Опис ситуації:*\n"
            f"{text}"
        )

        send_message(ADMIN_ID, message_to_admin)

        send_message(
            chat_id,
            "✅ Ваше звернення передано омбудсмену.\n"
            "Дякуємо за довіру 🙏",
            main_menu()
        )

        waiting_for_text.discard(chat_id)
        user_answers.pop(chat_id, None)

        return "ok"

    # ===== ЯКЩО НЕ ЗРОЗУМІЛО =====
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
