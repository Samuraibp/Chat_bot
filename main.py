import time
import string
import requests
import random

bot_key = '8531922367:AAHMg7uVl6t1BJaq2102tYnAEm6RZ9L12qs'

url = f"https://api.telegram.org/bot{bot_key}/"  # don't forget to change the token!


def last_update(request_url):
    response = requests.get(request_url + 'getUpdates')
    response = response.json()
    results = response['result']
    if results:
        return results[-1]
    return None


def get_chat_id(update):
    return update['message']['chat']['id']


def get_message_text(update):
    return update['message']['text']


def send_message(chat_id, text):
    params = {'chat_id': chat_id, 'text': text}
    response = requests.post(url + 'sendMessage', data=params)
    return response


def main():
    update = last_update(url)
    if update:
        update_id = update['update_id']
    else:
        update_id = 0

    while True:
        time.sleep(2)
        update = last_update(url)
        if not update:
            continue

        if update_id == update['update_id']:
            text = get_message_text(update)
            chat = get_chat_id(update)

            # Команди
            if text.lower() in ['start', 'привіт', 'hi', 'hello']:
                send_message(chat, "👋 Вітаю! Це анонімний бот шкільного омбудсмена.\n"
                                   "Напишіть своє звернення, і воно буде передано омбудсмену.\n"
                                   "Ваші дані залишаються конфіденційними.")
            else:
                # Надсилання повідомлення омбудсмену
                forwarded_text = f"📩 Нове анонімне звернення:\n\n{text}"
                send_message(ADMIN_ID, forwarded_text)
                send_message(chat, "✅ Ваше повідомлення надіслано омбудсмену. Дякуємо!")

            update_id += 1
            
# print(__name__)
if __name__ == '__main__':
    main()
# print(__name__)
# print('HELLO') #При подключении файла как бибилиотеки import bot, в другой .py файл проекта, этот код будет запускатся при включении того, другого файла
