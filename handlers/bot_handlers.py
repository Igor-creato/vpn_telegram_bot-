# handlers/bot_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_handler import DatabaseHandler
from payment.yookassa_handler import create_payment, check_payment_status
from datetime import datetime, timedelta

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

        if query.data == 'get_new_key':
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if not keys:
                keyboard = [
                    [InlineKeyboardButton("💵 1 месяц 150 руб.", callback_data='buy_1_month')],
                    [InlineKeyboardButton("💵 3 месяца 400 руб.", callback_data='buy_3_months')],
                    [InlineKeyboardButton("💵 6 месяцев 715 руб.", callback_data='buy_6_months')],
                    [InlineKeyboardButton("💵 1 год 1200 руб.", callback_data='buy_1_year')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text="Выберите срок действия ключа:", reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("Получить еще один ключ", callback_data='get_another_key')],
                    [InlineKeyboardButton("Продлить старый ключ", callback_data='renew_existing_key')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text="У вас уже есть активные ключи доступа, хотите получить еще один или продлить старый?",
                    reply_markup=reply_markup
                )

        elif query.data == 'get_another_key':
            keyboard = [
                [InlineKeyboardButton("💵 1 месяц 150 руб.", callback_data='buy_1_month')],
                [InlineKeyboardButton("💵 3 месяца 400 руб.", callback_data='buy_3_months')],
                [InlineKeyboardButton("💵 6 месяцев 715 руб.", callback_data='buy_6_months')],
                [InlineKeyboardButton("💵 1 год 1200 руб.", callback_data='buy_1_year')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Выберите срок действия ключа:", reply_markup=reply_markup)

        elif query.data == 'renew_key' or query.data == 'renew_existing_key':
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if not keys:
                await query.edit_message_text(text="У вас нет активных ключей для продления.")
                return

            message = "Ваши ключи:\n\n"
            keyboard = []
            for index, (link_key, expiration_date) in enumerate(keys, start=1):
                time_left = expiration_date - datetime.now()
                days = time_left.days
                hours, remainder = divmod(time_left.seconds, 3600)
                message += (
                    f"{index}. Ключ:\n `{link_key}`\n"
                    f"  До истечения срока действия осталось {days} дней {hours} часов.\n\n"
                )
                keyboard.append([InlineKeyboardButton(f"Ключ №{index}", callback_data=f'renew_key_{index}')])

            message += "Выберите ключ для продления:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif query.data.startswith('renew_key_'):
            key_index = int(query.data.split('_')[-1]) - 1
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if key_index < 0 or key_index >= len(keys):
                await query.edit_message_text(text="Ошибка: выбран неверный ключ.")
                return

            keyboard = [
                [InlineKeyboardButton("💵 1 месяц 150 руб.", callback_data=f'extend_1_month_{key_index}')],
                [InlineKeyboardButton("💵 3 месяца 400 руб.", callback_data=f'extend_3_months_{key_index}')],
                [InlineKeyboardButton("💵 6 месяцев 715 руб.", callback_data=f'extend_6_months_{key_index}')],
                [InlineKeyboardButton("💵 1 год 1200 руб.", callback_data=f'extend_1_year_{key_index}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Выберите срок продления для выбранного ключа:",
                reply_markup=reply_markup
            )

        elif query.data.startswith('extend_'):
            parts = query.data.split('_')
            period = parts[1]
            key_index = int(parts[-1])

            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if key_index < 0 or key_index >= len(keys):
                await query.edit_message_text(text="Ошибка: выбран неверный ключ.")
                return

            selected_key = keys[key_index]
            await query.edit_message_text(
                text=f"Вы выбрали продление ключа на {period}. Ключ: `{selected_key[0]}`",
                parse_mode="Markdown"
            )

            # Создание платежа
            amount = self.get_amount_by_period(period)
            payment_id = self.db.add_payment(telegram_id, amount)
            payment_url, payment_uid = create_payment(amount, payment_id)
            self.db.update_payment(payment_id, payment_uid)

            await query.edit_message_text(
                text=f"Ссылка для оплаты: {payment_url}"
            )

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
                    f"{index}. Ключ:\n `{link_key}`\n"
                    f"  До истечения срока действия осталось {days} дней {hours} часов.\n\n"
                )

            await query.edit_message_text(
                text=message,
                parse_mode="Markdown"
            )

        elif query.data == 'check_payment':
            await self.check_payment(update, context)

    def get_amount_by_period(self, period):
        if period == '1_month':
            return 150
        elif period == '3_months':
            return 400
        elif period == '6_months':
            return 715
        elif period == '1_year':
            return 1200
        else:
            return 0

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
                text=f"Вы оплатили заказ №{payment_id} на сумму {amount} руб."
            )
        else:
            await query.edit_message_text(
                text=f"Оплата заказа №{payment_id} еще не завершена."
            )