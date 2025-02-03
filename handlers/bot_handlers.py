# handlers/bot_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_handler import DatabaseHandler
from payment.yookassa_handler import create_payment, check_payment_status
from datetime import datetime, timedelta

class BotHandlers:
    def __init__(self):
        self.db = DatabaseHandler()

    async def handle_payment_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount):
        query = update.callback_query
        telegram_id = query.from_user.id
        
        payment_id = self.db.add_payment(telegram_id, amount)
        payment_url, payment_uid = create_payment(amount, payment_id)
        self.db.update_payment(payment_id, payment_uid)
        
        await query.edit_message_text(
            text=f"Оплата заказа No{payment_id}\n"
                 f"Для оплаты перейдите по ссылке:\n{payment_url}"
        )

    async def check_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        last_payment = self.db.get_last_payment(telegram_id)

        if not last_payment:
            await query.edit_message_text(text="У вас нет активных платежей.")
            return

        payment_id, amount = last_payment
        status = check_payment_status(payment_id)

        if status == 'succeeded':
            self.db.update_payment_status(payment_id, status)
            await query.edit_message_text(
                text=f"Вы оплатили заказ No{payment_id} на сумму {amount} руб."
            )
        else:
            await query.edit_message_text(
                text=f"Оплата заказа No{payment_id} еще не завершена."
            )

    # Остальные методы класса остаются без изменений

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = user.id
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        email = user.email if hasattr(user, 'email') else None
        phone_number = user.phone_number if hasattr(user, 'phone_number') else None

        if first_name and last_name:
            name = f"{first_name} {last_name}"
        elif first_name:
            name = first_name
        else:
            name = username

        user_data = self.db.get_user(telegram_id)
        if user_data:
            self.db.update_user(telegram_id, username, phone_number, email, name)
        else:
            self.db.add_user(username, telegram_id, phone_number, email, name)

        welcome_message = (
            f"👤 Привет {name}\n"
            "🔗 Этот бот создает сверхбыстрое, неблокируемое ВПН (VPN) соединение.\n"
            "▶️ Забудь о тормозах, не грузящихся видео на Youtube.\n"
            "🌐 Добро пожаловать в открытый интернет."
        )

        keyboard = [
            [InlineKeyboardButton("Получить новый ключ", callback_data='get_new_key')],
            [InlineKeyboardButton("Продлить ключ", callback_data='renew_key')],
            [InlineKeyboardButton("Мои ключи", callback_data='my_keys')],
            [InlineKeyboardButton("Проверить статус оплаты", callback_data='check_payment')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'get_new_key' or query.data == 'get_another_key':
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            keyboard = [
                [InlineKeyboardButton("💵 1 месяц 150 руб.", callback_data='buy_1_month')],
                [InlineKeyboardButton("💵 3 месяца 400 руб.", callback_data='buy_3_months')],
                [InlineKeyboardButton("💵 6 месяцев 715 руб.", callback_data='buy_6_months')],
                [InlineKeyboardButton("💵 1 год 1200 руб.", callback_data='buy_1_year')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Выберите срок действия ключа:", reply_markup=reply_markup)
        
        elif query.data == 'my_keys':
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)
            
            if not keys:
                keyboard = [
                    [InlineKeyboardButton("« Назад", callback_data='back_to_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text="У вас пока нет активных ключей.", 
                    reply_markup=reply_markup
                )
                return
                
            keys_text = "Ваши активные ключи:\n\n"
            for key, expiration_date in keys:
                keys_text += f"🔑 Ключ: {key}\n📅 Действует до: {expiration_date.strftime('%d.%m.%Y')}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("« Назад", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=keys_text, reply_markup=reply_markup)
        
        elif query.data == 'back_to_main':
            keyboard = [
                [InlineKeyboardButton("Получить новый ключ", callback_data='get_new_key')],
                [InlineKeyboardButton("Продлить ключ", callback_data='renew_key')],
                [InlineKeyboardButton("Мои ключи", callback_data='my_keys')],
                [InlineKeyboardButton("Проверить статус оплаты", callback_data='check_payment')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Выберите действие:",
                reply_markup=reply_markup
            )
        
        elif query.data in ['buy_1_month', 'buy_3_months', 'buy_6_months', 'buy_1_year']:
            amounts = {
                'buy_1_month': 150,
                'buy_3_months': 400,
                'buy_6_months': 715,
                'buy_1_year': 1200
            }
            await self.handle_payment_button(update, context, amounts[query.data])

    async def check_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        last_payment = self.db.get_last_payment(telegram_id)

        if not last_payment:
            await query.edit_message_text(text="У вас нет активных платежей.")
            return

        payment_id, amount = last_payment
        status = check_payment_status(payment_id)

        if status == 'succeeded':
            self.db.update_payment_status(payment_id, status)
            await query.edit_message_text(
                text=f"Вы оплатили заказ No{payment_id} на сумму {amount} руб."
            )
        else:
            await query.edit_message_text(
                text=f"Оплата заказа No{payment_id} еще не завершена."
            )
