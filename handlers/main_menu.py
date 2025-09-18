from telebot import types
from main import bot
from utils.storage import ensure_user
from utils.messages import tracker


def main_menu_markup() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Расписание', callback_data='schedule'),
        types.InlineKeyboardButton('Список дел', callback_data='todolist')
    )
    return markup


def show_main_menu(user_id, call_data, chat_id, message_id=None):
    markup = main_menu_markup()
    if call_data == 'main_new':
        # пользователь впервые открывает меню - загружаем фото
        tracker.clear(chat_id, user_id)
        with open('img/menu.jpg', 'rb') as photo:
            return bot.send_photo(
                caption='Главное меню.',
                chat_id=chat_id,
                photo=photo,
                reply_markup=markup,
                parse_mode='html'
            )
    else:
        # пользователь возвращается к меню - редактируем сообщение
        return bot.edit_message_caption(
            caption='Главное меню.',
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup,
            parse_mode='html'
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('main_'))
def callback_main(call):
    ensure_user(call.from_user.id, call.from_user.first_name,
                call.from_user.last_name)
    show_main_menu(call.from_user.id, call.data,
                   call.message.chat.id, call.message.message_id)
