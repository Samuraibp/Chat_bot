import time
import requests

BOT_TOKEN = "8531922367:AAHMg7uVl6t1BJaq2102tYnAEm6RZ9L12qs"
ADMIN_ID = 123456789
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    r = requests.get(f"{BASE_URL}/getUpdates", params=params)
    return r.json()["result"]


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(f"{BASE_URL}/sendMessage", json=data)


def main_menu():
    return {
        "keyboard": [
            ["📝 Новое обращение"],
            ["ℹ️ О боте"]
        ],
        "resize_keyboard": True
    }


def cancel_menu():
    return {
        "keyboard": [["❌ Отмена"]],
        "resize_keyboard": True
    }


def main():
    offset = None
    waiting_for_text = set()

    print("🤖 Bot started...")

    while True:
        updates = get_updates(offset)

        for update in updates:
            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text")

            if not text:
                continue

            # START
            if text.lower() in ["/start", "start"]:
                send_message(
                    chat_id,
                    "👋 Вітаю!\n"
                    "Це анонімний бот шкільного омбудсмена.\n\n"
                    "Оберіть дію з меню 👇",
                    main_menu()
                )
                continue

            # ABOUT
            if text == "ℹ️ О боте":
                send_message(
                    chat_id,
                    "ℹ️ **Про бота**\n\n"
                    "Через цього бота ви можете анонімно повідомити "
                    "про конфлікт, булінг або іншу проблему у школі.\n\n"
                    "🔒 Конфіденційність гарантовано.",
                    main_menu()
                )
                continue

            # NEW REQUEST
            if text == "📝 Новое обращение":
                waiting_for_text.add(chat_id)
                send_message(
                    chat_id,
                    "✍️ Опишіть ситуацію одним повідомленням.\n\n"
                    "Натисніть ❌ Отмена, щоб скасувати.",
                    cancel_menu()
                )
                continue

            # CANCEL
            if text == "❌ Отмена":
                waiting_for_text.discard(chat_id)
                send_message(
                    chat_id,
                    "❌ Скасовано.\nОберіть дію з меню 👇",
                    main_menu()
                )
                continue

            # USER MESSAGE
            if chat_id in waiting_for_text:
                admin_text = f"📩 Нове анонімне звернення:\n\n{text}"
                send_message(ADMIN_ID, admin_text)

                send_message(
                    chat_id,
                    "✅ Ваше звернення передано омбудсмену.\nДякуємо!",
                    main_menu()
                )

                waiting_for_text.discard(chat_id)
                continue

            # IF RANDOM TEXT
            send_message(
                chat_id,
                "ℹ️ Будь ласка, скористайтесь меню 👇",
                main_menu()
            )

        time.sleep(1)


if __name__ == "__main__":
    main()
