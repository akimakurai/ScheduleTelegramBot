from bot import bot
import handlers.start
import handlers.main_menu
import handlers.schedule
import handlers.todolist

if __name__ == "__main__":
    bot.infinity_polling()
