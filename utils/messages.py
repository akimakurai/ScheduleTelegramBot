import threading
from typing import Dict, List, Any
from utils.logger import logger
from bot import bot


class MessageTracker:
    """
    Класс для отслеживания сообщений пользователей и их удаления.
    """

    def __init__(self) -> None:
        self.tracked_messages: Dict[int, List[int]] = {}

    def track(self, user_id: int, msg_id: int) -> None:
        """
        Добавляет сообщение пользователя в список отслеживаемых.
        """
        self.tracked_messages.setdefault(user_id, []).append(msg_id)

    def clear(self, chat_id: int, user_id: int, delay: int = 1):
        """
        Удаляет все сообщения пользователя через delay секунд.
        Если delay=0, удаление произойдет сразу.
        """
        messages = self.tracked_messages.pop(user_id, [])

        def delete_msgs():
            for msg_id in messages:
                try:
                    bot.delete_message(chat_id, msg_id)
                except Exception as e:
                    print(f'Не удалось удалить сообщение {msg_id}: {e}')

        if delay > 0:
            threading.Timer(delay, delete_msgs).start()
        else:
            delete_msgs()


tracker = MessageTracker()
