import json
import os

SESSION_FILE = 'data/session.json'


def load_sessions() -> dict:
    """
    Загружает все пользовательские сессии из файла.
    Если файла нет или он пустой, возвращает пустой словарь.
    """
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_sessions(sessions: dict) -> None:
    """
    Сохраняет все сессии в файл.
    """
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=4)


def set_user_session(user_id: int, key: str, value) -> None:
    """
    Устанавливает значение в сессию пользователя.
    Если key == "state", то перезаписывается весь state.
    Если другой key, то обновляется только поле внутри state.
    """
    sessions = load_sessions()
    uid = str(user_id)

    if uid not in sessions:
        sessions[uid] = {
            'state': {
                'action': None,
                'day': None,
                'step': None,
                'data': None
            }
        }

    if key == 'state':
        sessions[uid]['state'] = value   # перезаписываем state целиком
    else:
        sessions[uid]['state'][key] = value  # меняем только поле

    save_sessions(sessions)


def get_user_session(user_id: int, key: str, default=None):
    """
    Возвращает значение по ключу `key` для конкретного пользователя.
    Если ключ или пользователь не найдены — вернёт default.
    """
    sessions = load_sessions()
    user_session = sessions.get(str(user_id), {})
    state = user_session.get('state', {})
    if key == 'state':
        return state
    else:
        return state.get(key, default)


def clear_user_state(user_id: int):
    """
    Очищает состояние пользователя после завершения операции,
    но оставляет информацию о дне.
    """
    sessions = load_sessions()
    uid = str(user_id)

    if uid not in sessions:
        return  # нечего чистить

    day = sessions[uid]['state'].get('day')  # сохраняем день
    day_message_id = sessions[uid]['state'].get('day_message_id')

    sessions[uid]['state'] = {
        'action': None,
        'day': day,   # восстанавливаем
        'day_message_id': day_message_id,
        'step': None,
        'data': None
    }

    save_sessions(sessions)
