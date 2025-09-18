from telebot import types
from main import bot


@bot.callback_query_handler(func=lambda call: call.data == 'todolist')
def callback_todolist(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        '⬅️ Назад', callback_data='main_back'))
    bot.edit_message_caption('В разработке...', call.message.chat.id,
                             call.message.message_id, reply_markup=markup)
