import json
import os
from typing import Dict

USERS_FILE = 'data/users.json'
WHITELIST_FILE = 'data/whitelist.json'


def load_users() -> dict:
    """
    Загружает данные пользователей из файла. Возвращает пустой словарь, если файл не найден.
    """
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_users(users: dict) -> None:
    """
    Сохраняет данные пользователей в файл.
    """
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


def load_whitelist() -> list:
    """
    Загружает whitelist из файла. Возвращает пустой список при ошибках.
    """
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def create_user_template(first_name: str = '', last_name: str = '') -> Dict:
    """
    Возвращает шаблон словаря для храниения данных каждого пользователя.
    """
    return {
        'first_name': first_name,
        'last_name': last_name,
        'schedule': {
            'monday': [],
            'tuesday': [],
            'wednesday': [],
            'thursday': [],
            'friday': [],
            'saturday': [],
            'sunday': []
        },
        'todolist': []
    }


def ensure_user(user_id: int, first_name: str = '', last_name: str = '') -> Dict:
    """
    Проверяет есть ли пользователь в users.json
    """
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = create_user_template(first_name, last_name)
        save_users(users)
    return users[uid]
