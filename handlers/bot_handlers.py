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
            f"👤 Привет {name}\n"
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
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if not keys:
                # Если ключей нет, выводим меню с кнопками для покупки нового ключа
                keyboard = [
                    [InlineKeyboardButton("💵 1 месяц 150 руб.", callback_data='buy_1_month')],
                    [InlineKeyboardButton("💵 3 месяца 400 руб.", callback_data='buy_3_months')],
                    [InlineKeyboardButton("💵 6 месяцев 715 руб.", callback_data='buy_6_months')],
                    [InlineKeyboardButton("💵 1 год 1200 руб.", callback_data='buy_1_year')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text="Выберите срок действия ключа:", reply_markup=reply_markup)
            else:
                # Если ключи есть, предлагаем получить еще один или продлить старый
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
            # Если пользователь выбрал "Получить еще один ключ", выводим меню с кнопками для покупки нового ключа
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

            # Формируем сообщение с ключами
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
            # Обработка выбора ключа для продления
            key_index = int(query.data.split('_')[-1]) - 1  # Получаем индекс ключа
            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if key_index < 0 or key_index >= len(keys):
                await query.edit_message_text(text="Ошибка: выбран неверный ключ.")
                return

            # Выводим меню для выбора срока продления
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
            # Обработка выбора срока продления
            parts = query.data.split('_')
            period = parts[1]  # 1_month, 3_months и т.д.
            key_index = int(parts[-1])  # Индекс ключа

            telegram_id = query.from_user.id
            keys = self.db.get_user_keys(telegram_id)

            if key_index < 0 or key_index >= len(keys):
                await query.edit_message_text(text="Ошибка: выбран неверный ключ.")
                return

            # Здесь можно добавить логику для продления ключа в базе данных
            selected_key = keys[key_index]
            await query.edit_message_text(
                text=f"Вы выбрали продление ключа на {period}. Ключ: `{selected_key[0]}`",
                parse_mode="Markdown"
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