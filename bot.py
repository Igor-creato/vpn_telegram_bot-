# bot.py
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.bot_handlers import BotHandlers

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    bot_handlers = BotHandlers()

    application = ApplicationBuilder().token("7753890665:AAHcwEnhlPkjN2XvBJWbmd1mOEL4Z39hmtM").build()

    application.add_handler(CommandHandler('start', bot_handlers.start))
    application.add_handler(CallbackQueryHandler(bot_handlers.button_handler))

    application.run_polling()

if __name__ == '__main__':
    main()