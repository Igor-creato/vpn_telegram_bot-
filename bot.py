import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.bot_handlers import BotHandlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_application():
    try:
        logger.info("Запуск бота...")
        bot_handlers = BotHandlers()

        application = ApplicationBuilder() \
            .token("7753890665:AAHcwEnhlPkjN2XvBJWbmd1mOEL4Z39hmtM") \
            .build()

        application.add_handler(CommandHandler('start', bot_handlers.start))
        application.add_handler(CallbackQueryHandler(bot_handlers.button_handler))

        logger.info("Бот успешно инициализирован")
        return application

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
        return None

application = get_application()

if __name__ == '__main__':
    if application:
        application.run_polling()