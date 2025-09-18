import re
from datetime import time

TIME_PATTERN = re.compile(r'^\d{1,2}:\d{2}$')


def validate_time(time_str: str) -> bool:
    """
    Проверяет, что строка времени корректна в формате HH:MM (24-часовой формат).
    Возвращает True, если время валидное, иначе False.
    """
    if not TIME_PATTERN.match(time_str):
        return False
    try:
        hours, minutes = map(int, time_str.split(':'))
    except ValueError:
        return False
    return 0 <= hours < 24 and 0 <= minutes < 60


def normalize_time(time_str: str) -> str | None:
    """
    Приводит время к формату HH:MM с ведущими нулями.
    Возвращает строку времени или None, если некорректно.
    """
    if not validate_time(time_str):
        return None
    hours, minutes = map(int, time_str.split(':'))
    return f'{hours:02d}:{minutes:02d}'


def is_end_after_start(start: str, end: str) -> bool:
    """
    Проверяет, что время окончания не раньше времени начала.
    Возвращает True, если конец >= начало, иначе False.
    """
    start_norm = normalize_time(start)
    end_norm = normalize_time(end)
    if not start_norm or not end_norm:
        return False

    start_h, start_m = map(int, start_norm.split(':'))
    end_h, end_m = map(int, end_norm.split(':'))
    return time(end_h, end_m) >= time(start_h, start_m)
