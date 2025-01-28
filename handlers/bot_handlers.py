# handlers/bot_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_handler import DatabaseHandler

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
        name = f"{first_name} {last_name}"

        user_data = self.db.get_user(telegram_id)
        if user_data:
            self.db.update_user(telegram_id, username, phone_number, email, name)
        else:
            self.db.add_user(username, telegram_id, phone_number, email, name)

        welcome_message = (
            f"👤 Привет, {first_name} {last_name}\n"
            "🔗 Этот бот создает сверхбыстрое, неблокируемое ВПН (VPN) соединение.\n"
            "▶️ Забудь о тормозах, не грузящихся видео на Youtube.\n"
            "🌐 Добро пожаловать в открытый интернет."
        )

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
            await query.edit_message_text(text="Вы выбрали: Мои ключи")