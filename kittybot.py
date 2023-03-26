import time
import logging
import os
import requests
import openai

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup

load_dotenv()

secret_token = os.getenv('TOKEN')
chat_id = os.getenv('chat_id')
openai_api_key = os.getenv('OPENAI_API_KEY')

openai.api_key = openai_api_key

URL = 'https://api.thecatapi.com/v1/images/search'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

messages = [
        {"role": "system", "content":
         "Hello! You are an Anfisa bot. You knouw everything in the world. You speak on Russia "},
        {"role": "user", "content": "Hi. I’m your companion, I’m asking you questions."}
]


def update_messages(messages, role, text):
    """Добавляет сообщение в список сообщений и удаляет старые сообщения"""
    messages.append({"role": role, "content": text})
    if len(messages) > 5:
        messages.pop(0)


def get_new_image():
    """Получает ссылку на случайное изображение котика"""
    try:
        response = requests.get(URL)
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
        new_url = 'https://api.thedogapi.com/v1/images/search'
        response = requests.get(new_url, timeout=60)

    response = response.json()
    random_cat = response[0].get('url')
    return random_cat


def new_chat(update, context):
    """Отправляет случайное изображение котика"""
    chat = update.effective_chat
    chat_id = chat.id
    context.bot.send_photo(chat_id, get_new_image())


def wake_up(update, context):
    """Отправляет приветственное сообщение и случайное изображение котика"""

    chat = update.effective_chat
    name = update.message.chat.first_name
    chat_id = chat.id
    button = ReplyKeyboardMarkup([
                                   ['/newcat', 'чатик']], resize_keyboard=True)

    # Изменение текста приветственного сообщения
    greeting_message = f'Привет, {name}! Добро пожаловать в бот!\n\n'
    greeting_message += 'Если хочешь получить картинку с котиком, используй команду /newcat.\n'

    context.bot.send_message(chat_id,
                             text=greeting_message,
                             reply_markup=button)
    context.bot.send_photo(chat_id, get_new_image())


def chat_with_gpt(update, context):
    """Отправляет сообщение в GPT-3 и получает ответ"""
    try:
        chat = update.effective_chat
        chat_id = chat.id
        user_message = update.message.text

        update_messages(messages, "user", user_message)

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages
        )

        gpt_response = response['choices'][0]['message']['content']
        context.bot.send_message(chat_id, gpt_response)
        update_messages(messages, "assistant", gpt_response)
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
        time.sleep(60)
        context.bot.send_message(chat_id, 'Я пока спокойно сплю, поговорим позже')


def main():
    """Запускает бота"""
    updater = Updater(token=secret_token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('newcat', new_chat))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, chat_with_gpt))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
