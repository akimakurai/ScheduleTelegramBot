from telebot import types
from utils.storage import ensure_user
from bot import bot
from handlers.schedule import tracker


@bot.message_handler(commands=['start'])
def start(message):
    ensure_user(message.from_user.id,
                message.from_user.first_name, message.from_user.last_name)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        'Главное меню', callback_data='main_new'))
    msg = bot.send_message(message.chat.id,
                           f'Привет, {message.from_user.first_name}. Я бот в котором можно составить личное расписание на любой день недели.\n\nДля начала работы со мной нажми на кнопку ниже.',
                           reply_markup=markup)
    tracker.track(message.from_user.id, msg.message_id)
