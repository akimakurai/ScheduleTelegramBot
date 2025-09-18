import copy
from typing import Optional
from utils.storage import load_users, save_users
from utils.logger import logger


def add_block(user_id: int, day: str, title: str, start: str, end: str) -> bool:
    """Добавляет блок в расписание пользователя."""
    users = load_users()
    try:
        users[str(user_id)]['schedule'][day].append({
            'title': title,
            'start': start,
            'end': end
        })
        save_users(users)
        return True
    except Exception as e:
        logger.warning(
            f'Не удалось добавить блок в {day} пользователя {user_id}: {e}'
        )
        return False


def edit_block(user_id: int, day: str, index: int, title: Optional[str] = None,
               start: Optional[str] = None, end: Optional[str] = None) -> bool:
    """Редактирует блок в расписании пользователя по индексу(-1)."""
    users = load_users()
    try:
        block = users[str(user_id)]['schedule'][day][index-1]
        if title is not None:
            block['title'] = title
        if start is not None:
            block['start'] = start
        if end is not None:
            block['end'] = end
        save_users(users)
        return True
    except Exception as e:
        logger.warning(
            f'Не удалось редактировать {day} пользователя {user_id}: {e}'
        )
        return False


def delete_block(user_id: int, day: str, index: int) -> bool:
    """Удаляет блок из расписания пользователя по индексу(-1)."""
    users = load_users()
    try:
        users[str(user_id)]['schedule'][day].pop(index-1)
        save_users(users)
        return True
    except Exception as e:
        logger.warning(
            f'Не удалось удалить блок в {day} пользователя {user_id}: {e}'
        )
        return False


def copy_day(user_id: int, day_to: str, day_from: str) -> bool:
    """Копирует расписание одного дня в другой."""
    users = load_users()
    uid = str(user_id)
    try:
        users[uid]['schedule'][day_to] = copy.deepcopy(
            users[uid]['schedule'][day_from])
        save_users(users)
        return True
    except Exception as e:
        logger.warning(
            f'Не удалось скопировать {day_from} в {day_to} пользователя {user_id}: {e}'
        )
        return False
