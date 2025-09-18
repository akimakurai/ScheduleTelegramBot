from enum import IntEnum
from telebot import types
from typing import Callable
from main import bot
from utils.storage import load_users, save_users
from utils.session import set_user_session, get_user_session, clear_user_state
from utils.validation import normalize_time, is_end_after_start
from utils.messages import tracker
from utils.schedule import add_block, edit_block, delete_block, copy_day


DAYS_RU = {
    'monday': 'Понедельник',
    'tuesday': 'Вторник',
    'wednesday': 'Среда',
    'thursday': 'Четверг',
    'friday': 'Пятница',
    'saturday': 'Суббота',
    'sunday': 'Воскресенье',
}

DAYS_CUT = {
    'day_mon': 'monday',
    'day_tue': 'tuesday',
    'day_wed': 'wednesday',
    'day_thu': 'thursday',
    'day_fri': 'friday',
    'day_sat': 'saturday',
    'day_sun': 'sunday',
}


class BlockStep(IntEnum):
    DELETE = -1
    ASK_INDEX = 0
    ASK_TITLE = 1
    ASK_START = 2
    ASK_END = 3


def ask(user_id, chat_id, text):
    """
    Отправляет сообщение пользователю и сохраняет его ID через MessageTracker
    """
    msg = bot.send_message(chat_id, text)
    tracker.track(user_id, msg.message_id)
    return msg


def is_change_action_complete(user_id: int, chat_id: int, check_func: Callable[..., bool]) -> None:
    """
    check_func - любая функция, возвращающая bool.
    """
    if check_func:
        ask(user_id, chat_id,
            f'✅ Действие выполнено успешно.')
    else:
        ask(user_id, chat_id,
            f'❌ Не удалось выполнить действие')
    tracker.clear(chat_id, user_id)


def build_day_buttons(back_to: str = 'main_back', suffix: str = ''):
    """
    Возвращает список кнопок для меню дней недели + кнопку "Назад".
    back_to - callback_data для кнопки "Назад"
    """
    buttons = [(name, f'day_{cut[:3]}'+suffix)
               for cut, name in DAYS_RU.items()]
    buttons.append(('⬅️ Назад', back_to))  # динамическая кнопка назад
    l = len(buttons)
    half = l//2

    rows = []
    for i in range(half):
        row = []
        # левая кнопка
        text1, cb1 = buttons[i]
        row.append(types.InlineKeyboardButton(text1, callback_data=cb1))

        # правая кнопка (если есть)
        if i + half < l:
            text2, cb2 = buttons[i + half]
            row.append(types.InlineKeyboardButton(text2, callback_data=cb2))

        rows.append(row)

    return rows


def day_actions_markup(back_to: str = 'schedule') -> types.InlineKeyboardMarkup:
    """
    Возвращает список кнопок редактирования для выбранного дня недели + кнопку "Назад".
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            '➕ Добавить', callback_data='block_add_choice'),
        types.InlineKeyboardButton(
            '✏️ Редактировать', callback_data='block_edit')
    )
    markup.add(
        types.InlineKeyboardButton(
            '✖️ Удалить', callback_data='block_delete_choice'),
        types.InlineKeyboardButton('⬅️ Назад', callback_data=back_to)
    )
    return markup


def format_day_text(day_name: str, day_data: list) -> str:
    """
    Форматирует текст выбранного дня
    """
    text = f'📅 <b>{day_name}</b>:\n<pre>'
    for i, block in enumerate(day_data, 1):
        text += f'{i}. {block["title"]}\n⏰ {block["start"]} – {block["end"]}\n\n'
    text += '</pre>'
    return text


def refresh_day_view(user_id: int, chat_id: int, message_id: int):
    """
    Обновляет сообщение с расписанием выбранного дня
    и стандартными кнопками управления.
    """
    users = load_users()
    state_day = get_user_session(user_id, 'day')
    day = DAYS_CUT[state_day]
    day_name = DAYS_RU[day]
    day_data = users[str(user_id)]['schedule'][day]
    try:
        bot.edit_message_caption(
            caption=format_day_text(day_name, day_data),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=day_actions_markup(back_to='schedule'),
            parse_mode='html'
        )
    except:
        pass


@bot.callback_query_handler(func=lambda call: call.data == 'schedule')
def callback_schedule(call):
    """
    Отображает меню выбора дня недели.
    """
    markup = types.InlineKeyboardMarkup()
    for row in build_day_buttons():
        markup.row(*row)
    bot.edit_message_caption(
        caption='Выбери день недели:',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='html'
    )


@bot.callback_query_handler(func=lambda call: call.data in DAYS_CUT.keys())
def callback_day(call):
    """
    Обработчик кнопки выбора дня недели.
    Сохраняет выбранный день и обновляет сообщение с расписанием.
    """
    set_user_session(call.from_user.id, 'day', call.data)
    # Сохраняем ID "основного" сообщения с расписанием
    set_user_session(call.from_user.id, 'day_message_id',
                     call.message.message_id)

    day_name = DAYS_RU.get(DAYS_CUT[call.data], 'Неизвестный день')
    users = load_users()
    day_data = users[str(call.from_user.id)]['schedule'][DAYS_CUT[call.data]]

    bot.edit_message_caption(
        caption=format_day_text(day_name, day_data),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=day_actions_markup(back_to='schedule'),
        parse_mode='html'
    )


@bot.callback_query_handler(func=lambda call: call.data == 'block_add_choice')
def callback_block_add_choice(call):
    """
    Обработчик кнопки 'Добавить'.
    Отображает подменю: добавить блок или скопировать день.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '➕ Добавить блок', callback_data='block_add'),
        types.InlineKeyboardButton(
            '📋 Копировать день', callback_data='block_copy')
    )
    markup.add(
        types.InlineKeyboardButton('⬅️ Назад', callback_data=get_user_session(
            call.from_user.id, 'day'))
    )

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'block_delete_choice')
def callback_block_delete_choice(call):
    """
    Обработчик кнопки 'Удалить'.
    Отображает подменю: удалить блок или очистить весь день.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '✖️ Удалить блок', callback_data='block_delete'),
        types.InlineKeyboardButton(
            '🧹 Очистить день', callback_data='day_clear')
    )
    markup.add(
        types.InlineKeyboardButton('⬅️ Назад', callback_data=get_user_session(
            call.from_user.id, 'day'))
    )

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'block_copy')
def callback_block_copy(call):
    """
    Обработчик кнопки 'Копировать день'.
    Отображает список дней для выбора источника копирования.
    """
    markup = types.InlineKeyboardMarkup()
    for row in build_day_buttons('block_add_choice', suffix='_copy'):
        markup.row(*row)

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data == 'day_clear')
def callback_day_clear(call):
    """
    Обработчик кнопки 'Очистить день'.
    Удаляет все блоки выбранного дня и обновляет сообщение.
    """
    users = load_users()
    day = DAYS_CUT[get_user_session(call.from_user.id, 'day')]
    users[str(call.from_user.id)]['schedule'][day] = []
    save_users(users)
    refresh_day_view(call.from_user.id, call.message.chat.id,
                     call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('day_') and call.data.endswith('_copy'))
def callback_day_copy(call):
    """
    Обработчик копирования дня.
    Копирует содержимое одного дня расписания в другой.
    """
    # День, выбранный ранее
    day_to = DAYS_CUT[get_user_session(call.from_user.id, 'day')]
    # Откуда копируем
    day_from = DAYS_CUT[call.data.removesuffix('_copy')]

    is_change_action_complete(
        call.from_user.id,
        call.message.chat.id,
        lambda: copy_day(
            call.from_user.id,
            day_to, day_from
        )
    )
    refresh_day_view(call.from_user.id, call.message.chat.id,
                     call.message.message_id)


# Добавление блока
@bot.callback_query_handler(func=lambda call: call.data == 'block_add')
def callback_block_add(call):
    """
    Обработчик кнопки 'Добавить блок'.
    Переводит пользователя в состояние добавления блока.
    """
    user_id = call.from_user.id
    day = get_user_session(user_id, 'day')
    day_message_id = get_user_session(user_id, 'day_message_id')
    set_user_session(user_id, 'state', {
        'action': 'add',
        'day': day,
        'day_message_id': day_message_id,
        'step': BlockStep.ASK_TITLE,
        'data': {'title': '', 'start': '', 'end': '', 'index': ''},
    })
    ask(user_id, call.message.chat.id,
        'Введите название блока (макс. 20 символов):')


# Редактирование блока
@bot.callback_query_handler(func=lambda call: call.data == 'block_edit')
def callback_block_edit(call):
    """
    Обработчик кнопки 'Редактировать блок'.
    Переводит пользователя в состояние редактирования блока.
    """
    user_id = call.from_user.id
    day = get_user_session(user_id, 'day')
    day_message_id = get_user_session(user_id, 'day_message_id')
    set_user_session(user_id, 'state', {
        'action': 'edit',
        'day': day,
        'day_message_id': day_message_id,
        'step': BlockStep.ASK_INDEX,
        'data': {'title': '', 'start': '', 'end': '', 'index': ''},
    })
    ask(user_id, call.message.chat.id,
        'Введите номер блока, который нужно изменить:')


# Удаление блока
@bot.callback_query_handler(func=lambda call: call.data == 'block_delete')
def callback_block_delete(call):
    """
    Обработчик кнопки 'Удалить блок'.
    Переводит пользователя в состояние удаления блока.
    """
    user_id = call.from_user.id
    day = get_user_session(user_id, 'day')
    day_message_id = get_user_session(user_id, 'day_message_id')
    set_user_session(user_id, 'state', {
        'action': 'delete',
        'day': day,
        'day_message_id': day_message_id,
        'step': BlockStep.DELETE,
        'data': {'title': '', 'start': '', 'end': '', 'index': ''},
    })
    ask(user_id, call.message.chat.id,
        'Введите номер блока, который нужно удалить:')


# Обработка сообщений пользователя
@bot.message_handler(func=lambda message: get_user_session(message.from_user.id, 'state') is not None and not message.text == '/start')
def handle_block_entry(message):
    """
    Обрабатывает текстовые сообщения пользователя
    во время добавления, редактирования или удаления блока.
    Выполняет пошаговый сценарий по состоянию (step).
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    state = get_user_session(user_id, 'state')
    day = DAYS_CUT[state['day']]

    step = state['step']
    if step is not None:
        step = BlockStep(step)

    tracker.track(user_id, message.message_id)

    if step == BlockStep.DELETE:
        state['data']['index'] = int(message.text)
        is_change_action_complete(user_id, chat_id, lambda: delete_block(
            user_id, day, state['data']['index']))
        refresh_day_view(message.from_user.id,
                         message.chat.id, get_user_session(user_id, 'day_message_id'))
        clear_user_state(user_id)
        tracker.clear(chat_id, user_id)

    elif step == BlockStep.ASK_INDEX:
        state['data']['index'] = int(message.text)
        state['step'] = BlockStep.ASK_TITLE
        set_user_session(user_id, 'state', state)
        ask(user_id, chat_id, 'Введите название блока (максимум 20 символов):')

    elif step == BlockStep.ASK_TITLE:
        state['data']['title'] = message.text[:20]
        state['step'] = BlockStep.ASK_START
        set_user_session(user_id, 'state', state)
        ask(user_id, chat_id, 'Введите время начала (ЧЧ:ММ):')

    elif step == BlockStep.ASK_START:
        start = normalize_time(message.text)
        if start:
            state['data']['start'] = start
            state['step'] = BlockStep.ASK_END
            set_user_session(user_id, 'state', state)
            ask(user_id, chat_id, 'Введите время окончания (ЧЧ:ММ):')
        else:
            ask(user_id, chat_id, '⚠️ Введите корректное время начала (например 09:30).')

    elif step == BlockStep.ASK_END:
        end = normalize_time(message.text)
        if end:
            state['data']['end'] = end
            if is_end_after_start(state['data']['start'], end):
                if state['action'] == 'add':
                    is_change_action_complete(user_id, chat_id,
                                              lambda: add_block(
                                                  user_id=user_id,
                                                  day=day,
                                                  title=state['data']['title'],
                                                  start=state['data']['start'],
                                                  end=end))
                    refresh_day_view(message.from_user.id,
                                     message.chat.id, get_user_session(user_id, 'day_message_id'))
                elif state['action'] == 'edit':
                    is_change_action_complete(user_id, chat_id,
                                              lambda: edit_block(
                                                  user_id=user_id,
                                                  day=day,
                                                  index=state['data']['index'],
                                                  title=state['data']['title'],
                                                  start=state['data']['start'],
                                                  end=end))
                    refresh_day_view(message.from_user.id,
                                     message.chat.id, get_user_session(user_id, 'day_message_id'))
                clear_user_state(user_id)  # очистка
                tracker.clear(chat_id, user_id)
            else:
                ask(user_id, chat_id,
                    '⚠️ Время окончания не может быть меньше времени начала. Попробуйте ещё раз.')
        else:
            ask(user_id, chat_id,
                '⚠️ Введите корректное время окончания (например 10:00).')
