import asyncio
import datetime
import sqlite3
from typing import Final
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import CallbackContext, CommandHandler, Updater, CallbackQueryHandler, Application, ContextTypes

manager_chat_id = "639415483"
TOKEN: Final = '6363322924:AAHbDW_QXDCbazBCfCZa1_E_vA-zK-AaqoY'
bot = Bot(TOKEN)

async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    insert_user(username, chat_id)
    await context.bot.send_message(chat_id=chat_id, text='Вы зарегистрированы')

def insert_user(username: str, chat_id: int):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (username, chat_id) VALUES (?, ?)', (username, chat_id))
    conn.commit()
    conn.close()
def create_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_user(username: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT chat_id FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    print(result)
    conn.close()

    return result[0]

def get_user_by_id(chat_id: int):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE chat_id = ?', (chat_id,))
    result = c.fetchone()
    print(result)
    conn.close()

    return '@' + result[0]

async def send_message_to_user(username: str, message: str, reply_markup: InlineKeyboardMarkup, context: CallbackContext):
    await context.bot.send_message(chat_id=username, text=message, reply_markup=reply_markup)

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(user_id)
    tel_id, test, date, time, answer_time = map(str.strip, update.message.text.split(','))

    tel_id = int(get_user(tel_id.split()[1][1:]))
    print(tel_id, "id")

    callback_data = f"{user_id}:{tel_id}"

    keyboard = [
        [InlineKeyboardButton("Выполнено", callback_data=f"{callback_data}:Выполнено")],
        [InlineKeyboardButton("Не сделано", callback_data=f"{callback_data}:Не сделано")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=tel_id, text=f"Напоминание: {test}\nДата: {date}\nВремя: {time}", reply_markup=reply_markup)
    answer_time_seconds = int(answer_time) * 60

    asyncio.get_event_loop().call_later(answer_time_seconds, asyncio.create_task, callback_timeout(context, tel_id))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tel_id = query.message.chat_id
    button = query.data.split(':')[2]
    await context.bot.send_message(chat_id=manager_chat_id, text="Сотрудник {} нажал кнопку: {}".format(get_user_by_id(tel_id), button))

async def callback_timeout(context: CallbackContext, tel_id: int):
    if tel_id not in context.bot_data:
        await context.bot.send_message(chat_id=manager_chat_id, text="Сотрудник {} проигнорировал напоминание.".format(tel_id))

if __name__ == '__main__':
    create_db()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_reminder", set_reminder))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(1.0)
