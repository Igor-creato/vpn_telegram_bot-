# handlers/bot_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_handler import DatabaseHandler
from datetime import datetime

class BotHandlers:
    def __init__(self):
        self.db = DatabaseHandler()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = user.id
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        email = user.email if hasattr(user, 'email') else None
        phone_number = user.phone_number if hasattr(user, 'phone_number') else None

        # Формируем имя для приветствия
        if first_name and last_name:
            name = f"{first_name} {last_name}"
        elif first_name:
            name = first_name
        else:
            name = username  # Если имя и фамилия отсутствуют, используем username

        # Поиск пользователя в базе данных
        user_data = self.db.get_user(telegram_id)
        if user_data:
            self.db.update_user(telegram_id, username, phone_number, email, name)
        else:
            self.db.add_user(username, telegram_id, phone_number, email, name)

        # Приветственное сообщение
        welcome_message = (
            f"👤 Привет, {name}\n"
            "🔗 Этот бот создает сверхбыстрое, неблокируемое ВПН (VPN) соединение.\n"
            "▶️ Забудь о тормозах, не грузящихся видео на Youtube.\n"
            "🌐 Добро пожаловать в открытый интернет."
        )

        # Создание инлайн кнопок
        keyboard = [
            [InlineKeyboardButton("Получить новый ключ", callback_data='get_new_key')],
            [InlineKeyboardButton("Продлить ключ", callback_data='renew_key')],
            [InlineKeyboardButton("Мои ключи", callback_data='my_keys')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'get_new_key':
            await query.edit_message_text(text="Вы выбрали: Получить новый ключ")
        elif query.data == 'renew_key':
            await query.edit_message_text(text="Вы выбрали: Продлить ключ")
        elif query.data == 'my_keys':
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if not keys:
                await query.edit_message_text(text="У вас нет активных ключей.")
                return

            message = "Ваши ключи:\n\n"
            for index, (link_key, expiration_date) in enumerate(keys, start=1):
                time_left = expiration_date - datetime.now()
                days = time_left.days
                hours, remainder = divmod(time_left.seconds, 3600)
                message += (
                    f"{index}. Ключ: {link_key}\n"
                    f"   Осталось {days} дней {hours} часов до истечения срока действия.\n\n"
                )

            await query.edit_message_text(text=message)
